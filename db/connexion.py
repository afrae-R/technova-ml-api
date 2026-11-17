"""Connexion à la base de données PostgreSQL.

Deux adresses sont lues dans le fichier .env (elles contiennent un mot de passe :
elles ne sont donc JAMAIS écrites dans le code) :
  - DATABASE_URL       : utilisateur « technova_api » aux droits limités, utilisé par l'API ;
  - DATABASE_ADMIN_URL : administrateur, utilisé seulement par les scripts qui créent
                         les tables et chargent les salariés. Si elle est absente,
                         les scripts utilisent DATABASE_URL.
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


def lire_adresse_base(administrateur=False):
    """Retourne l'adresse de la base, ou refuse de continuer si elle n'est pas configurée.

    administrateur=True : adresse de l'administrateur (DATABASE_ADMIN_URL) pour les scripts
    de création et de chargement ; à défaut, on prend DATABASE_URL.
    """
    adresse = os.getenv("DATABASE_URL", "").strip()
    if administrateur:
        adresse = os.getenv("DATABASE_ADMIN_URL", "").strip() or adresse
    if not adresse or ADRESSE_EXEMPLE in adresse:
        raise RuntimeError(
            "DATABASE_URL n'est pas configurée. Dans le fichier .env, remplacez "
            "'utilisateur' et 'motdepasse' par le vrai nom et le vrai mot de passe PostgreSQL."
        )
    return adresse


def creer_moteur(adresse=None, administrateur=False) -> Engine:
    """Crée le « moteur » SQLAlchemy : l'objet qui sait parler à PostgreSQL.

    Le moteur ne se connecte pas tout de suite : il ouvre la porte seulement
    quand on lui demande vraiment quelque chose (une requête, une création de table...).
    """
    return create_engine(adresse or lire_adresse_base(administrateur))
