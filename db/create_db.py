"""Crée les tables dans la base PostgreSQL (script de création de la base).

Utilisation, depuis la racine du projet :
    python -m db.create_db

Le script peut être relancé sans danger : il ne crée que les tables qui manquent
et ne touche jamais aux données déjà présentes.
"""
from sqlalchemy import inspect

from db.connexion import creer_moteur
from db.modeles import Base


def creer_tables(moteur=None):
    """Construit les tables décrites dans db/modeles.py et retourne leurs noms."""
    moteur = moteur or creer_moteur()
    # create_all lit le plan (Base.metadata) et envoie les ordres CREATE TABLE à PostgreSQL
    Base.metadata.create_all(moteur)
    # On demande ensuite à PostgreSQL ce qu'il contient vraiment, pour vérifier
    return sorted(inspect(moteur).get_table_names())


if __name__ == "__main__":
    tables = creer_tables()
    print("Tables presentes dans la base :", ", ".join(tables))
