"""Tests unitaires du côté machine learning : chaque petit morceau est testé séparément.

Un test unitaire vérifie UNE petite fonction, avec des données simples dont on connaît
la bonne réponse à l'avance. Ici : la création des variables, le nettoyage des données,
la règle de décision du modèle et la cohérence entre l'API et le modèle.
"""
import json
from typing import get_args

import pandas as pd
import pytest

from app.config import CHEMIN_INFOS, CHEMIN_MODELE
from app.modele import ModeleAttrition
from app.schemas import (
    Departement,
    DomaineEtude,
    FrequenceDeplacement,
    Genre,
    Poste,
    StatutMarital,
)
from ml.preprocessing import (
    COLONNE_CIBLE,
    COLONNES_CATEGORIELLES,
    COLONNES_ENTREE,
    COLONNES_MODELE,
    ajouter_variables,
    charger_donnees_brutes,
    nettoyer_donnees_brutes,
    preparer_entrainement,
)
from ml.train import GRAINE, construire_pipeline


# ---------------------------------------------------------------------------
# 1. La création des deux variables (ml/preprocessing.py : ajouter_variables)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "heures_supp, equilibre, attendu",
    [
        ("Oui", 1, 1),   # heures supplémentaires ET équilibre faible : surcharge
        ("Oui", 2, 1),   # 2 est la limite incluse (<= 2)
        ("Oui", 3, 0),   # équilibre correct : pas de surcharge
        ("Non", 1, 0),   # équilibre faible mais pas d'heures supplémentaires
        ("Non", 4, 0),
        ("oui", 1, 1),   # la fonction ignore les majuscules...
        (" OUI ", 2, 1),  # ... et les espaces autour
    ],
)
def test_variable_surcharge_travail(fiche_valide, heures_supp, equilibre, attendu):
    fiche_valide["heures_supplementaires"] = heures_supp
    fiche_valide["satisfaction_employe_equilibre_pro_perso"] = equilibre
    resultat = ajouter_variables(pd.DataFrame([fiche_valide]))
    assert resultat["surcharge_travail"].iloc[0] == attendu


@pytest.mark.parametrize("total, entreprise, attendu", [(8, 6, 2), (10, 4, 6), (5, 5, 0)])
def test_variable_experience_externe(fiche_valide, total, entreprise, attendu):
    """Expérience externe = années d'expérience totale - années chez TechNova."""
    fiche_valide["annee_experience_totale"] = total
    fiche_valide["annees_dans_l_entreprise"] = entreprise
    # On garde la fiche cohérente : l'ancienneté dans le poste et la promotion ne dépassent pas l'ancienneté
    fiche_valide["annees_dans_le_poste_actuel"] = 0
    fiche_valide["annees_depuis_la_derniere_promotion"] = 0
    resultat = ajouter_variables(pd.DataFrame([fiche_valide]))
    assert resultat["experience_externe"].iloc[0] == attendu


def test_ajouter_variables_retourne_exactement_les_colonnes_du_modele(fiche_valide):
    resultat = ajouter_variables(pd.DataFrame([fiche_valide]))
    assert list(resultat.columns) == COLONNES_MODELE   # mêmes colonnes, dans le même ordre
    assert len(resultat) == 1


def test_ajouter_variables_ne_modifie_pas_le_tableau_d_origine(fiche_valide):
    tableau = pd.DataFrame([fiche_valide])
    copie_avant = tableau.copy()
    ajouter_variables(tableau)
    pd.testing.assert_frame_equal(tableau, copie_avant)


# ---------------------------------------------------------------------------
# 2. Le nettoyage et la préparation des données d'entraînement
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def donnees_nettoyees():
    """Les 1470 salariés, après lecture des 3 fichiers CSV et nettoyage (calculé une seule fois)."""
    return nettoyer_donnees_brutes(charger_donnees_brutes())


def test_nettoyage_garde_les_1470_salaries_sans_doublon(donnees_nettoyees):
    assert len(donnees_nettoyees) == 1470
    assert not donnees_nettoyees.duplicated().any()


def test_nettoyage_transforme_le_pourcentage_texte_en_nombre(donnees_nettoyees):
    augmentation = donnees_nettoyees["augmentation_salaire_precedente"]
    assert augmentation.dtype == float          # "11 %" est devenu 11.0
    assert augmentation.between(0, 100).all()


def test_nettoyage_retire_les_colonnes_inutiles(donnees_nettoyees):
    inutiles = {"code_sondage", "eval_number", "nombre_heures_travailless",
                "nombre_employee_sous_responsabilite"}
    assert inutiles.isdisjoint(donnees_nettoyees.columns)


def test_nettoyage_garde_les_colonnes_utiles_et_la_reponse(donnees_nettoyees):
    for colonne in COLONNES_ENTREE + [COLONNE_CIBLE, "id_employe"]:
        assert colonne in donnees_nettoyees.columns
    assert set(donnees_nettoyees[COLONNE_CIBLE]) == {"Oui", "Non"}


def test_preparer_entrainement_retourne_x_et_y_alignes():
    X, y = preparer_entrainement(charger_donnees_brutes())
    assert list(X.columns) == COLONNES_MODELE
    assert len(X) == len(y) == 1470


# ---------------------------------------------------------------------------
# 3. L'assemblage du modèle (ml/train.py : construire_pipeline)
# ---------------------------------------------------------------------------

def test_le_pipeline_contient_la_preparation_puis_le_modele():
    pipeline = construire_pipeline()
    assert [nom for nom, _ in pipeline.steps] == ["preparation", "modele"]


def test_le_modele_a_les_reglages_du_projet_4():
    modele = construire_pipeline().named_steps["modele"]
    assert modele.n_estimators == 100
    assert modele.max_depth == 8
    assert modele.min_samples_split == 10
    assert modele.class_weight == "balanced"
    assert modele.random_state == GRAINE   # le hasard est fixé : résultats reproductibles


# ---------------------------------------------------------------------------
# 4. La règle de décision (app/modele.py : ModeleAttrition.predire)
# ---------------------------------------------------------------------------

class PipelineFactice:
    """Un faux modèle qui renvoie toujours le score qu'on lui donne.

    Cela permet de tester la RÈGLE (« Oui » si le score atteint le seuil) sans dépendre
    du vrai modèle : on choisit nous-mêmes le score, et on connaît donc la bonne réponse.
    """

    classes_ = ["Non", "Oui"]

    def __init__(self, score):
        self.score = score

    def predict_proba(self, X):
        return [[1 - self.score, self.score]]


def modele_avec_score(score, seuil=0.38):
    modele = ModeleAttrition.__new__(ModeleAttrition)   # crée l'objet sans charger de fichier
    modele.pipeline = PipelineFactice(score)
    modele.seuil = seuil
    return modele


def test_score_exactement_au_seuil_donne_oui(fiche_valide):
    assert modele_avec_score(0.38).predire(fiche_valide) == ("Oui", 0.38)


def test_score_juste_en_dessous_du_seuil_donne_non(fiche_valide):
    assert modele_avec_score(0.379).predire(fiche_valide)[0] == "Non"


def test_score_au_dessus_du_seuil_donne_oui(fiche_valide):
    assert modele_avec_score(0.9).predire(fiche_valide)[0] == "Oui"


def test_le_score_est_arrondi_a_quatre_decimales(fiche_valide):
    assert modele_avec_score(0.123456).predire(fiche_valide)[1] == 0.1235


# ---------------------------------------------------------------------------
# 5. Cohérence entre l'API, le modèle enregistré et le code
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def modele():
    return ModeleAttrition(CHEMIN_MODELE, CHEMIN_INFOS)


def test_les_valeurs_autorisees_par_l_api_sont_celles_connues_du_modele(modele):
    """Si l'API acceptait une valeur que le modèle n'a jamais vue, il l'ignorerait en silence."""
    autorisees = {
        "genre": Genre,
        "statut_marital": StatutMarital,
        "departement": Departement,
        "poste": Poste,
        "domaine_etude": DomaineEtude,
        "frequence_deplacement": FrequenceDeplacement,
    }
    encodeur = modele.pipeline.named_steps["preparation"].named_transformers_["texte"]
    for colonne, connues in zip(COLONNES_CATEGORIELLES, encodeur.categories_):
        assert set(connues) == set(get_args(autorisees[colonne])), colonne


def test_les_colonnes_enregistrees_avec_le_modele_sont_celles_du_code():
    infos = json.loads(CHEMIN_INFOS.read_text(encoding="utf-8"))
    assert infos["colonnes_attendues"] == COLONNES_MODELE


def test_le_seuil_enregistre_est_un_score_valide(modele):
    assert 0 < modele.seuil < 1
