"""Réglages communs à tous les tests (pytest lit ce fichier automatiquement).

Règle d'or : les tests ne touchent JAMAIS à la vraie base PostgreSQL ni à la vraie clé.
On utilise une clé de test et une base de test, de deux façons possibles :
  - par défaut (sur votre ordinateur) : une petite base SQLite qui vit seulement en mémoire ;
  - si la variable TEST_DATABASE_URL existe (c'est le cas sur GitHub) : une base
    PostgreSQL de TEST, jetable, démarrée par le robot GitHub. Jamais la vraie base.
"""
import copy
import os

# Ces deux lignes doivent venir AVANT l'import de l'application :
#  - une clé de test, qui prend le pas sur celle du fichier .env ;
#  - une adresse de base vide, pour que l'API n'essaie pas de joindre PostgreSQL.
CLE_DE_TEST = "cle-de-test-uniquement"
# Adresse d'une base PostgreSQL de TEST (vide si absente : on utilise alors SQLite)
ADRESSE_BASE_DE_TEST = os.environ.get("TEST_DATABASE_URL", "").strip()
os.environ["API_KEY"] = CLE_DE_TEST
os.environ["DATABASE_URL"] = ""

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.main import app, obtenir_moteur  # noqa: E402
from app.schemas import FicheSalarie  # noqa: E402
from db.modeles import Base  # noqa: E402


@pytest.fixture(scope="session")
def client():
    """Un « faux navigateur » qui appelle l'API sans lancer de serveur.

    Le « with » fait démarrer l'API pour de vrai (chargement de la clé et du modèle).
    """
    with TestClient(app) as client_test:
        yield client_test


@pytest.fixture
def fiche_valide():
    """Une fiche de salarié correcte : celle de l'exemple affiché dans Swagger."""
    return copy.deepcopy(FicheSalarie.model_config["json_schema_extra"]["example"])


@pytest.fixture
def entetes():
    """L'en-tête avec la clé de test."""
    return {"X-API-Key": CLE_DE_TEST}


def creer_base_de_test(avec_tables=True):
    """Crée une base de test : PostgreSQL de test si TEST_DATABASE_URL existe, sinon SQLite."""
    if ADRESSE_BASE_DE_TEST:
        moteur = create_engine(ADRESSE_BASE_DE_TEST)
        # La base PostgreSQL de test est la même pour tous les tests : on la vide d'abord,
        # pour que chaque test parte d'une base propre (comme avec SQLite en mémoire).
        Base.metadata.drop_all(moteur)
    else:
        moteur = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,  # une seule connexion partagée, sinon la base en mémoire se perd
        )
    if avec_tables:
        Base.metadata.create_all(moteur)
    return moteur


@pytest.fixture
def moteur_test():
    """Une base de test avec les 3 tables, vide."""
    moteur = creer_base_de_test()
    yield moteur
    if ADRESSE_BASE_DE_TEST:
        Base.metadata.drop_all(moteur)   # on range : la base PostgreSQL de test est vidée
    moteur.dispose()


@pytest.fixture
def moteur_vide():
    """Une base de test SANS aucune table (pour tester la création des tables)."""
    moteur = creer_base_de_test(avec_tables=False)
    yield moteur
    if ADRESSE_BASE_DE_TEST:
        Base.metadata.drop_all(moteur)
    moteur.dispose()


@pytest.fixture
def api_avec_base_de_test(moteur_test):
    """Branche l'API sur la base de test à la place de PostgreSQL, puis remet tout en ordre."""
    app.dependency_overrides[obtenir_moteur] = lambda: moteur_test
    yield moteur_test
    app.dependency_overrides.clear()
