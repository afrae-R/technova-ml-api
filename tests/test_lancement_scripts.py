"""Tests des commandes lancées à la main : « python -m db.create_db », « python -m ml.train »...

Ce sont les commandes que le README donne à l'utilisateur. Ces tests les lancent pour de vrai,
exactement comme dans le terminal (c'est le rôle de runpy), mais sans jamais toucher à la vraie base :
l'adresse de la base est remplacée, le temps du test, par un fichier SQLite temporaire.
"""
import runpy
from pathlib import Path

import joblib
import pytest


@pytest.fixture
def base_temporaire(tmp_path, monkeypatch):
    """Remplace les adresses de base du .env par un fichier SQLite jetable (supprimé après le test)."""
    adresse = f"sqlite:///{(tmp_path / 'essai.db').as_posix()}"
    monkeypatch.setenv("DATABASE_URL", adresse)
    monkeypatch.setenv("DATABASE_ADMIN_URL", adresse)


def lancer(module):
    """Équivalent de « python -m <module> » dans le terminal."""
    runpy.run_module(module, run_name="__main__")


def test_les_commandes_de_la_base_fonctionnent_les_unes_apres_les_autres(base_temporaire, capsys):
    lancer("db.create_db")
    assert "predictions, requetes, salaries" in capsys.readouterr().out

    lancer("db.charger_salaries")
    sortie = capsys.readouterr().out
    assert "1470" in sortie
    assert "'Non': 1233" in sortie and "'Oui': 237" in sortie

    lancer("db.journal")
    sortie = capsys.readouterr().out
    assert "table requetes)     : 0" in sortie

    lancer("db.requetes")
    assert "1. Combien de salariés" in capsys.readouterr().out


def test_la_commande_d_entrainement_va_jusqu_au_bout_sans_ecraser_le_modele(monkeypatch):
    """« python -m ml.train » : on remplace les deux sauvegardes par de fausses sauvegardes."""
    sauvegardes = []
    monkeypatch.setattr(joblib, "dump", lambda objet, chemin: sauvegardes.append(Path(chemin).name))
    monkeypatch.setattr(Path, "write_text", lambda self, texte, **options: sauvegardes.append(self.name))
    lancer("ml.train")
    assert sauvegardes == ["modele_attrition.joblib", "modele_attrition_infos.json"]
