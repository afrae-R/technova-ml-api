"""Connexion à la base de données PostgreSQL.

L'adresse de la base (variable DATABASE_URL) est lue dans le fichier .env.
Elle contient le mot de passe : elle n'est donc JAMAIS écrite dans le code.
"""
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from app.config import RACINE_PROJET

# Lit le fichier .env (comme dans app/config.py) pour que DATABASE_URL soit disponible
load_dotenv(RACINE_PROJET / ".env")

# Début de l'adresse d'exemple du fichier .env.example : interdit en vrai
ADRESSE_EXEMPLE = "utilisateur:motdepasse"


def lire_adresse_base():
    """Retourne l'adresse de la base, ou refuse de continuer si elle n'est pas configurée."""
    adresse = os.getenv("DATABASE_URL", "").strip()
    if not adresse or ADRESSE_EXEMPLE in adresse:
        raise RuntimeError(
            "DATABASE_URL n'est pas configurée. Dans le fichier .env, remplacez "
            "'utilisateur' et 'motdepasse' par le vrai nom et le vrai mot de passe PostgreSQL."
        )
    return adresse


def creer_moteur(adresse=None) -> Engine:
    """Crée le « moteur » SQLAlchemy : l'objet qui sait parler à PostgreSQL.

    Le moteur ne se connecte pas tout de suite : il ouvre la porte seulement
    quand on lui demande vraiment quelque chose (une requête, une création de table...).
    """
    return create_engine(adresse or lire_adresse_base())
