"""Tests fonctionnels : l'API et le modèle fonctionnent ensemble, avec des cas d'usage réels.

Un test fonctionnel ne regarde pas les petits morceaux : il se place du point de vue de
l'utilisateur. Il envoie une fiche à l'API et vérifie qu'il reçoit une réponse correcte,
comme le ferait un vrai client. Ici : de vrais salariés de nos données, et des profils extrêmes.
"""
import pytest

from ml.preprocessing import COLONNES_ENTREE, charger_donnees_brutes, nettoyer_donnees_brutes


@pytest.fixture(scope="module")
def salaries_reels():
    """Les 1470 vrais salariés, sous forme de fiches (une fiche = un dictionnaire)."""
    tableau = nettoyer_donnees_brutes(charger_donnees_brutes())
    return tableau[COLONNES_ENTREE].astype(object).to_dict("records")


def verifier_reponse_valide(reponse):
    assert reponse.status_code == 200
    corps = reponse.json()
    assert corps["prediction"] in ("Oui", "Non")
    assert 0 <= corps["probabilite_depart"] <= 1
    return corps


# 15 salariés répartis sur tout le fichier (positions 0, 98, 196, ...) : des profils variés
@pytest.mark.parametrize("position", range(0, 1470, 98))
def test_un_vrai_salarie_obtient_une_reponse_valide(
    client, api_avec_base_de_test, entetes, salaries_reels, position
):
    fiche = salaries_reels[position]
    corps = verifier_reponse_valide(client.post("/predict", json=fiche, headers=entetes))
    # L'API doit répondre exactement comme le modèle appelé directement
    etiquette, score = client.app.state.modele.predire(fiche)
    assert (corps["prediction"], corps["probabilite_depart"]) == (etiquette, score)


def test_les_reponses_sont_enregistrees_en_base_pour_des_profils_varies(
    client, api_avec_base_de_test, entetes, salaries_reels
):
    from sqlalchemy import func, select
    from sqlalchemy.orm import Session

    from db.modeles import Prediction, Requete

    for fiche in salaries_reels[:5]:
        assert client.post("/predict", json=fiche, headers=entetes).status_code == 200
    with Session(api_avec_base_de_test) as session:
        assert session.scalar(select(func.count()).select_from(Requete)) == 5
        assert session.scalar(select(func.count()).select_from(Prediction)) == 5


def fiche_minimale(fiche):
    """Toutes les valeurs au minimum permis (en gardant les règles de cohérence)."""
    fiche.update(
        age=18, revenu_mensuel=1, annee_experience_totale=0, annees_dans_l_entreprise=0,
        annees_dans_le_poste_actuel=0, satisfaction_employe_environnement=1,
        note_evaluation_precedente=1, satisfaction_employe_nature_travail=1,
        satisfaction_employe_equipe=1, satisfaction_employe_equilibre_pro_perso=1,
        heures_supplementaires="Non", augmentation_salaire_precedente=0.0,
        nombre_participation_pee=0, nb_formations_suivies=0, distance_domicile_travail=0,
        niveau_education=1, annees_depuis_la_derniere_promotion=0,
    )
    return fiche


def fiche_maximale(fiche):
    """Toutes les valeurs au maximum permis."""
    fiche.update(
        age=70, revenu_mensuel=100000, annee_experience_totale=50, annees_dans_l_entreprise=50,
        annees_dans_le_poste_actuel=50, satisfaction_employe_environnement=4,
        note_evaluation_precedente=4, satisfaction_employe_nature_travail=4,
        satisfaction_employe_equipe=4, satisfaction_employe_equilibre_pro_perso=4,
        heures_supplementaires="Oui", augmentation_salaire_precedente=100.0,
        nombre_participation_pee=10, nb_formations_suivies=20, distance_domicile_travail=200,
        niveau_education=5, annees_depuis_la_derniere_promotion=50,
    )
    return fiche


def fiche_a_risque(fiche):
    """Jeune, peu payé, heures supplémentaires, peu satisfait, peu d'ancienneté."""
    fiche.update(
        age=22, revenu_mensuel=1800, annee_experience_totale=2, annees_dans_l_entreprise=1,
        annees_dans_le_poste_actuel=1, satisfaction_employe_environnement=1,
        satisfaction_employe_nature_travail=1, satisfaction_employe_equipe=1,
        satisfaction_employe_equilibre_pro_perso=1, heures_supplementaires="Oui",
        augmentation_salaire_precedente=11.0, annees_depuis_la_derniere_promotion=1,
        distance_domicile_travail=25,
    )
    return fiche


def fiche_stable(fiche):
    """Expérimenté, bien payé, pas d'heures supplémentaires, très satisfait."""
    fiche.update(
        age=48, revenu_mensuel=9500, annee_experience_totale=25, annees_dans_l_entreprise=15,
        annees_dans_le_poste_actuel=8, satisfaction_employe_environnement=4,
        satisfaction_employe_nature_travail=4, satisfaction_employe_equipe=4,
        satisfaction_employe_equilibre_pro_perso=4, heures_supplementaires="Non",
        annees_depuis_la_derniere_promotion=3, distance_domicile_travail=3,
    )
    return fiche


@pytest.mark.parametrize(
    "fabriquer", [fiche_minimale, fiche_maximale, fiche_a_risque, fiche_stable]
)
def test_les_profils_extremes_et_types_obtiennent_une_reponse_valide(
    client, api_avec_base_de_test, fiche_valide, entetes, fabriquer
):
    fiche = fabriquer(fiche_valide)
    verifier_reponse_valide(client.post("/predict", json=fiche, headers=entetes))


def test_le_profil_a_risque_a_un_score_plus_eleve_que_le_profil_stable(client, fiche_valide):
    """Cohérence métier : le modèle juge plus risqué un profil qui cumule les signaux de départ."""
    modele = client.app.state.modele
    _, score_risque = modele.predire(fiche_a_risque(dict(fiche_valide)))
    _, score_stable = modele.predire(fiche_stable(dict(fiche_valide)))
    assert score_risque > score_stable
