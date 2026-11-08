"""Tests de l'API : est-ce qu'elle répond comme prévu dans chaque situation ?"""
import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.main import app, obtenir_moteur
from db.modeles import Prediction, Requete
from tests.conftest import creer_base_de_test


def test_health_repond_ok(client):
    reponse = client.get("/health")
    assert reponse.status_code == 200
    assert reponse.json()["statut"] == "ok"


def test_predict_sans_cle_donne_401(client, fiche_valide):
    reponse = client.post("/predict", json=fiche_valide)
    assert reponse.status_code == 401


def test_predict_avec_mauvaise_cle_donne_401(client, fiche_valide):
    reponse = client.post("/predict", json=fiche_valide, headers={"X-API-Key": "mauvaise-cle"})
    assert reponse.status_code == 401


def test_predict_fiche_valide_donne_200(client, fiche_valide, entetes):
    reponse = client.post("/predict", json=fiche_valide, headers=entetes)
    assert reponse.status_code == 200
    donnees = reponse.json()
    assert donnees["prediction"] in ("Oui", "Non")
    assert 0 <= donnees["probabilite_depart"] <= 1


def test_la_reponse_respecte_le_seuil_de_decision(client, fiche_valide, entetes):
    """« Oui » si et seulement si la note atteint le seuil (0,381)."""
    donnees = client.post("/predict", json=fiche_valide, headers=entetes).json()
    seuil = client.app.state.modele.seuil
    assert (donnees["prediction"] == "Oui") == (donnees["probabilite_depart"] >= seuil)


def fiche_sans_age(fiche):
    del fiche["age"]
    return fiche


def fiche_age_trop_grand(fiche):
    fiche["age"] = 400
    return fiche


def fiche_genre_inconnu(fiche):
    fiche["genre"] = "X"
    return fiche


def fiche_champ_en_trop(fiche):
    fiche["champ_invente"] = 1
    return fiche


def fiche_incoherente(fiche):
    # on prétend avoir plus d'années dans l'entreprise que d'années d'expérience au total
    fiche["annee_experience_totale"] = 2
    fiche["annees_dans_l_entreprise"] = 10
    return fiche


@pytest.mark.parametrize(
    "abimer_la_fiche",
    [fiche_sans_age, fiche_age_trop_grand, fiche_genre_inconnu, fiche_champ_en_trop, fiche_incoherente],
)
def test_fiche_invalide_donne_422(client, fiche_valide, entetes, abimer_la_fiche):
    fiche = abimer_la_fiche(fiche_valide)
    reponse = client.post("/predict", json=fiche, headers=entetes)
    assert reponse.status_code == 422


def compter(moteur, table):
    with Session(moteur) as session:
        return session.scalar(select(func.count()).select_from(table))


def test_une_prediction_est_enregistree_en_base(client, api_avec_base_de_test, fiche_valide, entetes):
    reponse = client.post("/predict", json=fiche_valide, headers=entetes)
    assert reponse.status_code == 200
    assert compter(api_avec_base_de_test, Requete) == 1
    assert compter(api_avec_base_de_test, Prediction) == 1


def test_une_fiche_refusee_nest_pas_enregistree(client, api_avec_base_de_test, fiche_valide, entetes):
    fiche_valide["age"] = 400
    client.post("/predict", json=fiche_valide, headers=entetes)
    assert compter(api_avec_base_de_test, Requete) == 0


def test_lapi_repond_meme_si_la_base_est_en_panne(client, fiche_valide, entetes):
    """Base sans tables = l'enregistrement échoue. L'utilisateur doit quand même avoir sa réponse."""
    base_cassee = creer_base_de_test(avec_tables=False)
    app.dependency_overrides[obtenir_moteur] = lambda: base_cassee
    try:
        reponse = client.post("/predict", json=fiche_valide, headers=entetes)
    finally:
        app.dependency_overrides.clear()
    assert reponse.status_code == 200
