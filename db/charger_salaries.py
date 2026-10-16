"""Charge les 1470 salariés du jeu de données dans la table « salaries ».

Utilisation, depuis la racine du projet :
    python -m db.charger_salaries

Le script peut être relancé sans danger : si la table contient déjà des salariés,
il ne fait rien (il ne crée jamais de doublons).
"""
from sqlalchemy import func, insert, select
from sqlalchemy.orm import Session

from db.connexion import creer_moteur
from db.modeles import Salarie
from ml.preprocessing import (
    COLONNE_CIBLE,
    COLONNES_ENTREE,
    charger_donnees_brutes,
    nettoyer_donnees_brutes,
)


def lire_salaries():
    """Lit les fichiers CSV et retourne les salariés sous forme de liste de dictionnaires.

    On utilise le même nettoyage que pour l'entraînement du modèle (ml/preprocessing.py) :
    la base contient donc exactement les données vues par le modèle.
    """
    tableau = nettoyer_donnees_brutes(charger_donnees_brutes())
    colonnes = ["id_employe"] + COLONNES_ENTREE + [COLONNE_CIBLE]
    # astype(object) : on repasse en types Python simples (int, float, str), que PostgreSQL comprend
    return tableau[colonnes].astype(object).to_dict("records")


def charger_salaries(moteur=None):
    """Insère les salariés dans la table. Retourne le nombre de salariés présents ensuite."""
    moteur = moteur or creer_moteur()
    # Une « session » regroupe plusieurs ordres en un seul bloc : tout réussit, ou rien n'est écrit
    with Session(moteur) as session:
        deja_presents = session.scalar(select(func.count()).select_from(Salarie))
        if deja_presents == 0:
            session.execute(insert(Salarie), lire_salaries())
            session.commit()
        return session.scalar(select(func.count()).select_from(Salarie))


def compter_par_reponse(moteur=None):
    """Retourne, par exemple, {'Non': 1233, 'Oui': 237} : combien sont partis ou restés."""
    moteur = moteur or creer_moteur()
    with Session(moteur) as session:
        lignes = session.execute(
            select(Salarie.a_quitte_l_entreprise, func.count())
            .group_by(Salarie.a_quitte_l_entreprise)
        ).all()
    return dict(lignes)


if __name__ == "__main__":
    total = charger_salaries()
    print("Salaries presents dans la base :", total)
    print("Repartition (a quitte l'entreprise) :", compter_par_reponse())
