"""Tests des performances du modèle et de la reproductibilité.

On rejoue l'« examen final » du modèle : mêmes 294 salariés de test que lors de
l'entraînement (même découpage grâce à la même graine, 42). Si quelqu'un remplaçait
le modèle par un modèle moins bon, ces tests deviendraient rouges.
"""
import json

import numpy as np
import pytest
from sklearn.metrics import f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split

from app.config import CHEMIN_INFOS, CHEMIN_MODELE
from app.modele import ModeleAttrition
from ml.preprocessing import charger_donnees_brutes, preparer_entrainement
from ml.train import GRAINE, RAPPEL_CIBLE, calculer_seuil, construire_pipeline, entrainer


@pytest.fixture(scope="module")
def jeu():
    """Le découpage entraînement / test, identique à celui de ml/train.py."""
    X, y = preparer_entrainement(charger_donnees_brutes())
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=GRAINE, stratify=y
    )
    return X_train, X_test, y_train, y_test


@pytest.fixture(scope="module")
def infos():
    """Les résultats enregistrés à côté du modèle au moment de l'entraînement."""
    return json.loads(CHEMIN_INFOS.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def resultats_test(jeu):
    """Scores et réponses du modèle enregistré sur le jeu de test."""
    _, X_test, _, y_test = jeu
    modele = ModeleAttrition(CHEMIN_MODELE, CHEMIN_INFOS)
    position_oui = list(modele.pipeline.classes_).index("Oui")
    scores = modele.pipeline.predict_proba(X_test)[:, position_oui]
    reponses = np.where(scores >= modele.seuil, "Oui", "Non")
    return y_test, scores, reponses


def test_le_rappel_atteint_la_cible_du_projet(resultats_test):
    """Le modèle doit détecter au moins 70 % des départs (choix métier du Projet 4)."""
    y_test, _, reponses = resultats_test
    assert recall_score(y_test, reponses, pos_label="Oui") >= RAPPEL_CIBLE


def test_precision_et_f1_restent_au_dessus_d_un_plancher(resultats_test):
    """Planchers volontairement un peu sous les valeurs connues (0,30 et 0,43)."""
    y_test, _, reponses = resultats_test
    assert precision_score(y_test, reponses, pos_label="Oui") >= 0.25
    assert f1_score(y_test, reponses, pos_label="Oui") >= 0.38


def test_le_modele_fait_mieux_que_le_hasard(resultats_test):
    y_test, scores, _ = resultats_test
    assert roc_auc_score(y_test == "Oui", scores) > 0.65   # 0,5 = hasard


def test_les_resultats_correspondent_a_ceux_enregistres(resultats_test, infos):
    y_test, _, reponses = resultats_test
    assert precision_score(y_test, reponses, pos_label="Oui") == pytest.approx(
        infos["precision_oui_test"], abs=0.01)
    assert recall_score(y_test, reponses, pos_label="Oui") == pytest.approx(
        infos["rappel_oui_test"], abs=0.01)
    assert f1_score(y_test, reponses, pos_label="Oui") == pytest.approx(
        infos["f1_oui_test"], abs=0.01)


def test_le_seuil_recalcule_correspond_au_seuil_enregistre(jeu, infos):
    X_train, _, y_train, _ = jeu
    assert calculer_seuil(X_train, y_train) == pytest.approx(infos["seuil_decision"], abs=0.05)


def test_deux_entrainements_donnent_exactement_les_memes_predictions(jeu):
    """Reproductibilité : avec la même graine, le même entraînement donne le même modèle."""
    X_train, X_test, y_train, _ = jeu
    premier = construire_pipeline().fit(X_train, y_train)
    second = construire_pipeline().fit(X_train, y_train)
    assert np.array_equal(premier.predict_proba(X_test), second.predict_proba(X_test))


def test_la_meme_fiche_donne_toujours_la_meme_reponse(fiche_valide):
    modele = ModeleAttrition(CHEMIN_MODELE, CHEMIN_INFOS)
    reponses = {modele.predire(fiche_valide) for _ in range(5)}
    assert len(reponses) == 1


def test_reentrainer_retrouve_les_resultats_enregistres(infos):
    """Rejoue tout ml/train.py (quelques secondes) et compare avec le modèle livré."""
    _, nouvelles_infos = entrainer()
    assert nouvelles_infos["colonnes_attendues"] == infos["colonnes_attendues"]
    assert nouvelles_infos["nb_salaries_entrainement"] == infos["nb_salaries_entrainement"]
    assert nouvelles_infos["nb_salaries_test"] == infos["nb_salaries_test"]
    for mesure in ("precision_oui_test", "rappel_oui_test", "f1_oui_test"):
        assert nouvelles_infos[mesure] == pytest.approx(infos[mesure], abs=0.03)
    assert nouvelles_infos["seuil_decision"] == pytest.approx(infos["seuil_decision"], abs=0.05)
