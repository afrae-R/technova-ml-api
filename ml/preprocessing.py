"""Préparation des données TechNova.

Ce fichier est utilisé À DEUX ENDROITS :
  1. à l'entraînement (ml/train.py), sur les 1470 salariés ;
  2. plus tard par l'API, sur UN seul salarié envoyé par l'utilisateur.

Avoir une seule version du code de préparation évite le piège classique :
préparer les données d'une façon à l'entraînement et d'une autre façon en production.
"""
from pathlib import Path

import pandas as pd

DOSSIER_DATA = Path(__file__).resolve().parent.parent / "data"

COLONNE_CIBLE = "a_quitte_l_entreprise"

# --- Les 23 informations qu'il faut fournir pour prédire (futures entrées de l'API) ---
COLONNES_ENTREE = [
    "age",
    "genre",
    "revenu_mensuel",
    "statut_marital",
    "departement",
    "poste",
    "annee_experience_totale",
    "annees_dans_l_entreprise",
    "annees_dans_le_poste_actuel",
    "satisfaction_employe_environnement",
    "note_evaluation_precedente",
    "satisfaction_employe_nature_travail",
    "satisfaction_employe_equipe",
    "satisfaction_employe_equilibre_pro_perso",
    "heures_supplementaires",
    "augmentation_salaire_precedente",
    "nombre_participation_pee",
    "nb_formations_suivies",
    "distance_domicile_travail",
    "niveau_education",
    "domaine_etude",
    "frequence_deplacement",
    "annees_depuis_la_derniere_promotion",
]

# --- Colonnes réellement vues par le modèle, après création des 2 nouvelles variables ---
COLONNES_CATEGORIELLES = [
    "genre",
    "statut_marital",
    "departement",
    "poste",
    "domaine_etude",
    "frequence_deplacement",
]
COLONNES_NUMERIQUES = [
    "age",
    "revenu_mensuel",
    "annees_dans_le_poste_actuel",
    "satisfaction_employe_environnement",
    "note_evaluation_precedente",
    "satisfaction_employe_nature_travail",
    "satisfaction_employe_equipe",
    "augmentation_salaire_precedente",
    "nombre_participation_pee",
    "nb_formations_suivies",
    "distance_domicile_travail",
    "niveau_education",
    "annees_depuis_la_derniere_promotion",
    "surcharge_travail",   # variable créée (voir ajouter_variables)
    "experience_externe",  # variable créée (voir ajouter_variables)
]
COLONNES_MODELE = COLONNES_CATEGORIELLES + COLONNES_NUMERIQUES

# Colonnes qui existent dans les fichiers mais que le modèle n'utilise pas
# (décisions prises dans le Projet 4 : doublons ou colonnes constantes)
COLONNES_ECARTEES = [
    "id_employe",
    "ayant_enfants",                  # une seule valeur ("Y") pour tout le monde : inutile
    "nombre_experiences_precedentes",  # corrélée à experience_externe (Spearman ~0,70)
    "niveau_hierarchique_poste",       # doublon du revenu mensuel (0,95)
    "note_evaluation_actuelle",        # doublon de l'augmentation de salaire (0,77)
    "annees_sous_responsable_actuel",  # doublon de annees_dans_le_poste_actuel (0,71)
]

# Les fichiers d'origine contiennent des fautes de frappe : on les corrige ici.
RENOMMAGE = {
    "id_employee": "id_employe",
    "annes_sous_responsable_actuel": "annees_sous_responsable_actuel",
    "heure_supplementaires": "heures_supplementaires",
    "augementation_salaire_precedente": "augmentation_salaire_precedente",
    "satisfaction_employee_environnement": "satisfaction_employe_environnement",
    "satisfaction_employee_nature_travail": "satisfaction_employe_nature_travail",
    "satisfaction_employee_equipe": "satisfaction_employe_equipe",
    "satisfaction_employee_equilibre_pro_perso": "satisfaction_employe_equilibre_pro_perso",
}


def charger_donnees_brutes(dossier=DOSSIER_DATA):
    """Lit les 3 fichiers CSV et les assemble en un seul tableau (1 ligne = 1 salarié)."""
    sirh = pd.read_csv(Path(dossier) / "extrait_sirh.csv")
    evaluations = pd.read_csv(Path(dossier) / "extrait_eval.csv")
    sondage = pd.read_csv(Path(dossier) / "extrait_sondage.csv")
    # Même méthode que dans le Projet 4 : jointure sur la position de la ligne.
    return sirh.join(evaluations, how="inner").join(sondage, how="inner")


def nettoyer_donnees_brutes(df):
    """Nettoyage de l'ensemble d'entraînement (étapes du Projet 4)."""
    df = df.copy()
    # Colonnes sans intérêt : identifiants techniques ou valeurs identiques pour tous
    df = df.drop(
        columns=[
            "code_sondage",
            "eval_number",
            "nombre_heures_travailless",           # toujours 80
            "nombre_employee_sous_responsabilite",  # toujours 1
        ]
    )
    df = df.rename(columns=RENOMMAGE)
    # "11 %" (texte) -> 11.0 (nombre)
    df["augmentation_salaire_precedente"] = (
        df["augmentation_salaire_precedente"]
        .astype(str)
        .str.replace("%", "", regex=False)
        .str.strip()
        .astype(float)
    )
    return df.drop_duplicates()


def ajouter_variables(df):
    """Crée les 2 variables du Projet 4 et prépare le tableau pour le modèle.

    Fonctionne aussi bien sur 1470 salariés que sur un seul : c'est ce qui permet
    à l'API de préparer les données exactement comme à l'entraînement.
    """
    df = df.copy()
    fait_heures_supp = df["heures_supplementaires"].astype(str).str.lower().str.strip() == "oui"
    # Variable 1 : fait des heures supplémentaires ET équilibre vie pro/perso <= 2
    df["surcharge_travail"] = (
        fait_heures_supp & (df["satisfaction_employe_equilibre_pro_perso"] <= 2)
    ).astype(int)
    # Variable 2 : années d'expérience acquises AVANT d'arriver chez TechNova
    df["experience_externe"] = df["annee_experience_totale"] - df["annees_dans_l_entreprise"]
    # On ne garde que les colonnes (et dans l'ordre) que le modèle connaît
    return df[COLONNES_MODELE]


def preparer_entrainement(df_brut):
    """Retourne X (variables explicatives) et y (le salarié est-il parti ?)."""
    df = nettoyer_donnees_brutes(df_brut)
    y = df[COLONNE_CIBLE]
    X = ajouter_variables(df)
    return X, y
