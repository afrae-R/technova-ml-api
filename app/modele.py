"""Chargement du modèle sauvegardé et calcul d'une prédiction."""
import json
from pathlib import Path

import joblib
import pandas as pd

from ml.preprocessing import ajouter_variables


class ModeleAttrition:
    """Enveloppe autour du Pipeline entraîné (traducteur + modèle) et de son seuil de décision."""

    def __init__(self, chemin: Path, chemin_infos: Path):
        # joblib.load rouvre exactement l'objet sauvegardé par ml/train.py
        self.pipeline = joblib.load(chemin)
        # Le seuil de décision est calculé à l'entraînement et sauvegardé à côté du modèle
        infos = json.loads(Path(chemin_infos).read_text(encoding="utf-8"))
        self.seuil = float(infos["seuil_decision"])

    def predire(self, fiche: dict):
        """Retourne ("Oui" ou "Non", score de départ entre 0 et 1) pour UN salarié.

        « Oui » si le score atteint le seuil de décision, « Non » sinon.
        """
        tableau = pd.DataFrame([fiche])        # une fiche = un tableau d'une ligne
        X = ajouter_variables(tableau)         # mêmes variables créées qu'à l'entraînement
        probabilites = self.pipeline.predict_proba(X)[0]
        position_oui = list(self.pipeline.classes_).index("Oui")
        score = float(probabilites[position_oui])
        etiquette = "Oui" if score >= self.seuil else "Non"
        return etiquette, round(score, 4)
