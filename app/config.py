"""Configuration de l'API : lecture des secrets dans le fichier .env.

Le fichier .env contient les secrets (clé d'accès, adresse de la base de données).
Il n'est JAMAIS publié sur GitHub (il est listé dans .gitignore).
Le fichier .env.example, lui, est publié : il montre quelles variables il faut définir.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

RACINE_PROJET = Path(__file__).resolve().parent.parent
CHEMIN_MODELE = RACINE_PROJET / "ml" / "modele_attrition.joblib"
# Informations sauvegardées avec le modèle : versions, scores et seuil de décision
CHEMIN_INFOS = RACINE_PROJET / "ml" / "modele_attrition_infos.json"

# Lit le fichier .env (s'il existe) et met son contenu à disposition de Python
load_dotenv(RACINE_PROJET / ".env")

# Valeurs d'exemple du fichier .env.example : interdites en vrai
CLES_INTERDITES = {"", "change-moi"}


def lire_cle_api():
    """Retourne la clé d'accès attendue, ou refuse de démarrer si elle n'est pas configurée."""
    cle = os.getenv("API_KEY", "").strip()
    if cle in CLES_INTERDITES:
        raise RuntimeError(
            "API_KEY n'est pas configurée. Copiez .env.example en .env "
            "et remplacez la valeur de API_KEY par une vraie clé secrète."
        )
    return cle
