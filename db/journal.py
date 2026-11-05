"""Journalisation : enregistrer chaque demande de l'API et sa réponse dans PostgreSQL.

À chaque appel réussi de /predict, on écrit DEUX lignes :
  - une ligne dans la table « requetes »    : la fiche reçue (23 informations) et la date ;
  - une ligne dans la table « predictions » : la réponse du modèle, reliée à cette demande.

Pour voir ce que contient le journal :
    python -m db.journal
"""
from sqlalchemy import func, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from db.connexion import creer_moteur
from db.modeles import Prediction, Requete


def enregistrer_prediction(moteur: Engine, fiche: dict, etiquette: str, score: float) -> int:
    """Écrit une demande et sa réponse. Retourne le numéro de la demande.

    Les deux lignes sont enregistrées ensemble : soit les deux, soit aucune
    (si l'une échoue, la base annule tout et ne garde pas une demi-ligne).
    """
    with Session(moteur) as session:
        # Requete(**fiche) : les 23 clés du dictionnaire portent exactement le nom des colonnes
        requete = Requete(**fiche)
        # Reliée à la demande : SQLAlchemy remplit tout seul la colonne requete_id
        requete.reponse = Prediction(prediction=etiquette, probabilite_depart=score)
        session.add(requete)
        session.flush()  # envoie les lignes à la base pour obtenir le numéro de la demande
        numero = requete.id
        session.commit()  # valide définitivement
        return numero


def compter_journal(moteur: Engine | None = None):
    """Retourne (nombre de demandes, nombre de prédictions) déjà enregistrées."""
    moteur = moteur or creer_moteur()
    with Session(moteur) as session:
        demandes = session.scalar(select(func.count()).select_from(Requete))
        predictions = session.scalar(select(func.count()).select_from(Prediction))
    return demandes, predictions


if __name__ == "__main__":
    demandes, predictions = compter_journal()
    print(f"Demandes enregistrées (table requetes)     : {demandes}")
    print(f"Prédictions enregistrées (table predictions) : {predictions}")
