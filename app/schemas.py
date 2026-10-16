"""Règles de validation des données : ce qu'une fiche de salarié doit respecter.

Pydantic lit ces règles et contrôle automatiquement chaque fiche reçue.
Si une règle n'est pas respectée, l'API répond par une erreur claire (code 422)
sans jamais donner la fiche au modèle.
"""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

# Les valeurs de texte autorisées sont exactement celles vues par le modèle à l'entraînement.
# (L'orthographe "Entrepreunariat" est celle des fichiers d'origine : on la garde.)
Genre = Literal["F", "M"]
StatutMarital = Literal["Célibataire", "Marié(e)", "Divorcé(e)"]
Departement = Literal["Commercial", "Consulting", "Ressources Humaines"]
Poste = Literal[
    "Assistant de Direction",
    "Cadre Commercial",
    "Consultant",
    "Directeur Technique",
    "Manager",
    "Représentant Commercial",
    "Ressources Humaines",
    "Senior Manager",
    "Tech Lead",
]
DomaineEtude = Literal[
    "Autre",
    "Entrepreunariat",
    "Infra & Cloud",
    "Marketing",
    "Ressources Humaines",
    "Transformation Digitale",
]
FrequenceDeplacement = Literal["Aucun", "Occasionnel", "Frequent"]
OuiNon = Literal["Oui", "Non"]


class FicheSalarie(BaseModel):
    """Les 23 informations nécessaires pour estimer le risque de départ d'un salarié."""

    # extra="forbid" : une information inconnue (faute de frappe sur un nom) est refusée
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "age": 41,
                "genre": "F",
                "revenu_mensuel": 5993,
                "statut_marital": "Célibataire",
                "departement": "Commercial",
                "poste": "Cadre Commercial",
                "annee_experience_totale": 8,
                "annees_dans_l_entreprise": 6,
                "annees_dans_le_poste_actuel": 4,
                "satisfaction_employe_environnement": 2,
                "note_evaluation_precedente": 3,
                "satisfaction_employe_nature_travail": 4,
                "satisfaction_employe_equipe": 1,
                "satisfaction_employe_equilibre_pro_perso": 1,
                "heures_supplementaires": "Oui",
                "augmentation_salaire_precedente": 11.0,
                "nombre_participation_pee": 0,
                "nb_formations_suivies": 0,
                "distance_domicile_travail": 1,
                "niveau_education": 2,
                "domaine_etude": "Infra & Cloud",
                "frequence_deplacement": "Occasionnel",
                "annees_depuis_la_derniere_promotion": 0,
            }
        },
    )

    age: int = Field(ge=18, le=70, description="Âge en années")
    genre: Genre
    revenu_mensuel: int = Field(gt=0, le=100000, description="Revenu mensuel en euros")
    statut_marital: StatutMarital
    departement: Departement
    poste: Poste
    annee_experience_totale: int = Field(ge=0, le=50, description="Années d'expérience au total")
    annees_dans_l_entreprise: int = Field(ge=0, le=50, description="Années passées chez TechNova")
    annees_dans_le_poste_actuel: int = Field(ge=0, le=50)
    satisfaction_employe_environnement: int = Field(ge=1, le=4, description="De 1 (faible) à 4 (forte)")
    note_evaluation_precedente: int = Field(ge=1, le=4, description="De 1 à 4")
    satisfaction_employe_nature_travail: int = Field(ge=1, le=4, description="De 1 (faible) à 4 (forte)")
    satisfaction_employe_equipe: int = Field(ge=1, le=4, description="De 1 (faible) à 4 (forte)")
    satisfaction_employe_equilibre_pro_perso: int = Field(ge=1, le=4, description="De 1 (faible) à 4 (forte)")
    heures_supplementaires: OuiNon
    augmentation_salaire_precedente: float = Field(ge=0, le=100, description="En pourcentage, par exemple 11 pour 11 %")
    nombre_participation_pee: int = Field(ge=0, le=10)
    nb_formations_suivies: int = Field(ge=0, le=20)
    distance_domicile_travail: int = Field(ge=0, le=200, description="En kilomètres")
    niveau_education: int = Field(ge=1, le=5, description="De 1 à 5")
    domaine_etude: DomaineEtude
    frequence_deplacement: FrequenceDeplacement
    annees_depuis_la_derniere_promotion: int = Field(ge=0, le=50)

    @model_validator(mode="after")
    def verifier_coherence(self):
        """Règles qui comparent plusieurs informations entre elles."""
        if self.annees_dans_l_entreprise > self.annee_experience_totale:
            raise ValueError(
                "annees_dans_l_entreprise ne peut pas dépasser annee_experience_totale"
            )
        if self.annees_dans_le_poste_actuel > self.annees_dans_l_entreprise:
            raise ValueError(
                "annees_dans_le_poste_actuel ne peut pas dépasser annees_dans_l_entreprise"
            )
        if self.annees_depuis_la_derniere_promotion > self.annees_dans_l_entreprise:
            raise ValueError(
                "annees_depuis_la_derniere_promotion ne peut pas dépasser annees_dans_l_entreprise"
            )
        return self


class PredictionReponse(BaseModel):
    """Ce que l'API renvoie pour une fiche valide."""

    prediction: Literal["Oui", "Non"] = Field(description="Le modèle prévoit-il un départ ?")
    probabilite_depart: float = Field(
        ge=0, le=1, description="Score du modèle entre 0 et 1 (ce n'est pas une probabilité calibrée)"
    )
