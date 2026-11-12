"""Tests des trois scripts de la base : création, chargement, requêtes.

Chaque script accepte qu'on lui donne la base où écrire (le « moteur »).
Dans ces tests, on lui donne toujours une base temporaire : la vraie base
PostgreSQL n'est jamais touchée.
"""
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from db.charger_salaries import charger_salaries, compter_par_reponse
from db.create_db import creer_tables
from db.requetes import lancer_requetes


def test_creer_tables_cree_les_trois_tables():
    # Une base temporaire VIDE : sans aucune table
    moteur = create_engine("sqlite://", poolclass=StaticPool,
                           connect_args={"check_same_thread": False})
    tables = creer_tables(moteur)
    moteur.dispose()   # ferme la base temporaire proprement
    assert tables == ["predictions", "requetes", "salaries"]


def test_charger_salaries_charge_1470_salaries_sans_doublon(moteur_test):
    assert charger_salaries(moteur_test) == 1470
    assert charger_salaries(moteur_test) == 1470   # relancé : aucun doublon
    assert compter_par_reponse(moteur_test) == {"Non": 1233, "Oui": 237}


def test_lancer_requetes_affiche_les_quatre_questions(moteur_test, capsys):
    lancer_requetes(moteur_test)
    sortie = capsys.readouterr().out
    assert "1. Combien de salariés" in sortie
    assert "4. Combien de prédictions" in sortie
