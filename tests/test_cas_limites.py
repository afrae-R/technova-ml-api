"""Tests de cas limites : règles de cohérence, configuration, requêtes avec des données.

Chaque test vise un cas qui n'était pas encore vérifié.
"""
import pytest
from pydantic import ValidationError

from app.config import lire_cle_api
from app.schemas import FicheSalarie
from db.charger_salaries import charger_salaries
from db.connexion import lire_adresse_base
from db.requetes import lancer_requetes


def test_anciennete_dans_le_poste_plus_grande_que_dans_l_entreprise_est_refusee(fiche_valide):
    fiche_valide["annees_dans_l_entreprise"] = 5
    fiche_valide["annees_dans_le_poste_actuel"] = 6   # plus que les 5 ans dans l'entreprise : absurde
    with pytest.raises(ValidationError, match="annees_dans_le_poste_actuel ne peut pas"):
        FicheSalarie(**fiche_valide)


def test_promotion_plus_ancienne_que_l_entree_dans_l_entreprise_est_refusee(fiche_valide):
    fiche_valide["annees_dans_l_entreprise"] = 5
    fiche_valide["annees_dans_le_poste_actuel"] = 4
    fiche_valide["annees_depuis_la_derniere_promotion"] = 6   # promu il y a plus longtemps que l'arrivée
    with pytest.raises(ValidationError, match="annees_depuis_la_derniere_promotion ne peut pas"):
        FicheSalarie(**fiche_valide)


@pytest.mark.parametrize("valeur_interdite", ["", "change-moi"])
def test_cle_api_non_configuree_arrete_le_demarrage(monkeypatch, valeur_interdite):
    # monkeypatch change la variable pendant ce test seulement, puis remet l'ancienne valeur
    monkeypatch.setenv("API_KEY", valeur_interdite)
    with pytest.raises(RuntimeError, match="API_KEY n'est pas configurée"):
        lire_cle_api()


def test_adresse_de_base_configuree_est_retournee(monkeypatch):
    adresse = "postgresql+psycopg2://moi:abc@localhost:5432/essai"
    monkeypatch.setenv("DATABASE_URL", adresse)
    assert lire_adresse_base() == adresse


def test_requetes_affichent_les_resultats_quand_la_base_est_remplie(moteur_test, capsys):
    charger_salaries(moteur_test)
    lancer_requetes(moteur_test)
    sortie = capsys.readouterr().out
    assert "('Non', 1233)" in sortie
    assert "('Oui', 237)" in sortie
