"""Tests de la base de données : les tables, les règles et l'enregistrement."""
import pytest
from sqlalchemy import func, inspect, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from db.journal import compter_journal, enregistrer_prediction
from db.modeles import Prediction, Requete


def test_les_trois_tables_existent(moteur_test):
    assert set(inspect(moteur_test).get_table_names()) == {"salaries", "requetes", "predictions"}


def test_enregistrer_une_prediction_ajoute_deux_lignes(moteur_test, fiche_valide):
    numero = enregistrer_prediction(moteur_test, fiche_valide, "Oui", 0.6745)
    assert numero == 1
    assert compter_journal(moteur_test) == (1, 1)


def test_les_valeurs_relues_ont_le_bon_type(moteur_test, fiche_valide):
    enregistrer_prediction(moteur_test, fiche_valide, "Non", 0.12)
    with Session(moteur_test) as session:
        demande = session.scalars(select(Requete)).one()
        assert isinstance(demande.age, int)
        assert isinstance(demande.augmentation_salaire_precedente, float)
        assert demande.reponse.prediction == "Non"
        assert isinstance(demande.reponse.probabilite_depart, float)
        assert demande.date_heure is not None  # remplie automatiquement par la base


def test_un_age_hors_des_regles_est_refuse(moteur_test, fiche_valide):
    fiche_valide["age"] = 5
    with Session(moteur_test) as session:
        session.add(Requete(**fiche_valide))
        with pytest.raises(IntegrityError):
            session.commit()


def test_un_champ_vide_est_refuse(moteur_test, fiche_valide):
    fiche_valide["age"] = None
    with Session(moteur_test) as session:
        session.add(Requete(**fiche_valide))
        with pytest.raises(IntegrityError):
            session.commit()


def test_une_prediction_inconnue_est_refusee(moteur_test, fiche_valide):
    with Session(moteur_test) as session:
        demande = Requete(**fiche_valide)
        demande.reponse = Prediction(prediction="Peut-etre", probabilite_depart=0.5)
        session.add(demande)
        with pytest.raises(IntegrityError):
            session.commit()


def test_supprimer_une_demande_supprime_sa_reponse(moteur_test, fiche_valide):
    enregistrer_prediction(moteur_test, fiche_valide, "Oui", 0.7)
    with Session(moteur_test) as session:
        demande = session.scalars(select(Requete)).one()
        session.delete(demande)
        session.commit()
        assert session.scalar(select(func.count()).select_from(Prediction)) == 0
