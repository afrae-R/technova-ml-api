"""Réglages communs à tous les tests (pytest lit ce fichier automatiquement).

Règle d'or : les tests ne touchent JAMAIS à la vraie base PostgreSQL ni à la vraie clé.
On utilise une clé de test et une petite base SQLite qui vit seulement en mémoire.
"""
import copy
import os

# Ces deux lignes doivent venir AVANT l'import de l'application :
#  - une clé de test, qui prend le pas sur celle du fichier .env ;
#  - une adresse de base vide, pour que l'API n'essaie pas de joindre PostgreSQL.
CLE_DE_TEST = "cle-de-test-uniquement"
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
    """Crée une petite base SQLite en mémoire (disparaît à la fin du test)."""
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
    moteur.dispose()


@pytest.fixture
def api_avec_base_de_test(moteur_test):
    """Branche l'API sur la base de test à la place de PostgreSQL, puis remet tout en ordre."""
    app.dependency_overrides[obtenir_moteur] = lambda: moteur_test
    yield moteur_test
    app.dependency_overrides.clear()
