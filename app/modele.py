"""Chargement du modèle sauvegardé et calcul d'une prédiction."""
from pathlib import Path

import joblib
import pandas as pd

from ml.preprocessing import ajouter_variables


class ModeleAttrition:
    """Enveloppe autour du Pipeline entraîné (traducteur + modèle)."""

    def __init__(self, chemin: Path):
        # joblib.load rouvre exactement l'objet sauvegardé par ml/train.py
        self.pipeline = joblib.load(chemin)

    def predire(self, fiche: dict):
        """Retourne ("Oui" ou "Non", score de départ entre 0 et 1) pour UN salarié."""
        tableau = pd.DataFrame([fiche])        # une fiche = un tableau d'une ligne
        X = ajouter_variables(tableau)         # mêmes variables créées qu'à l'entraînement
        probabilites = self.pipeline.predict_proba(X)[0]
        position_oui = list(self.pipeline.classes_).index("Oui")
        etiquette = str(self.pipeline.predict(X)[0])
        return etiquette, round(float(probabilites[position_oui]), 4)
