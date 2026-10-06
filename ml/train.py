"""Entraînement du modèle de prédiction du départ des salariés TechNova.

Lancer depuis la racine du projet :
    .venv\\Scripts\\python.exe -m ml.train        (Windows)

Résultat : le fichier ml/modele_attrition.joblib (modèle + préparation des données
dans un seul objet) et ml/modele_attrition_infos.json (versions et scores).
"""
import json
from pathlib import Path

import joblib
import pandas as pd
import sklearn
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix, f1_score, make_scorer
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from ml.preprocessing import (
    COLONNES_CATEGORIELLES,
    charger_donnees_brutes,
    preparer_entrainement,
)

DOSSIER_ML = Path(__file__).resolve().parent
FICHIER_MODELE = DOSSIER_ML / "modele_attrition.joblib"
FICHIER_INFOS = DOSSIER_ML / "modele_attrition_infos.json"
GRAINE = 42  # fixe le hasard : on obtient les mêmes résultats à chaque lancement


def construire_pipeline():
    """Assemble la 'recette' : préparation des colonnes texte + modèle."""
    preparation = ColumnTransformer(
        transformers=[
            # Les colonnes texte deviennent des colonnes 0/1.
            # handle_unknown="ignore" : une catégorie jamais vue ne fait pas planter l'API.
            ("texte", OneHotEncoder(handle_unknown="ignore"), COLONNES_CATEGORIELLES),
        ],
        remainder="passthrough",  # les colonnes numériques passent sans changement
    )
    # Réglages trouvés par GridSearchCV dans le Projet 4
    modele = RandomForestClassifier(
        n_estimators=100,
        max_depth=8,
        min_samples_split=10,
        class_weight="balanced",
        random_state=GRAINE,
    )
    return Pipeline([("preparation", preparation), ("modele", modele)])


def entrainer():
    X, y = preparer_entrainement(charger_donnees_brutes())
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=GRAINE, stratify=y
    )

    pipeline = construire_pipeline()
    pipeline.fit(X_train, y_train)

    predictions = pipeline.predict(X_test)
    f1_test = f1_score(y_test, predictions, pos_label="Oui")
    f1_train = f1_score(y_train, pipeline.predict(X_train), pos_label="Oui")

    # Validation croisée : 5 découpages différents, pour vérifier que le score est stable
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=GRAINE)
    f1_oui_cv = cross_val_score(
        construire_pipeline(), X, y, cv=cv, scoring=make_scorer(f1_score, pos_label="Oui")
    )

    print("=== Résultats sur le jeu de TEST (examen final) ===")
    print(classification_report(y_test, predictions))
    print("Matrice de confusion (lignes = réalité, colonnes = prédiction ; ordre Non, Oui) :")
    print(confusion_matrix(y_test, predictions, labels=["Non", "Oui"]))
    print(f"\nF1 'Oui' train : {f1_train:.2f} | test : {f1_test:.2f}")
    print(f"F1 'Oui' validation croisée : {f1_oui_cv.mean():.2f} (+/- {f1_oui_cv.std():.2f})")

    infos = {
        "version_scikit_learn": sklearn.__version__,
        "version_pandas": pd.__version__,
        "colonnes_attendues": list(X.columns),
        "f1_oui_train": round(f1_train, 3),
        "f1_oui_test": round(f1_test, 3),
        "f1_oui_validation_croisee_moyenne": round(float(f1_oui_cv.mean()), 3),
        "nb_salaries_entrainement": int(len(X_train)),
        "nb_salaries_test": int(len(X_test)),
    }
    return pipeline, infos


if __name__ == "__main__":
    pipeline, infos = entrainer()
    joblib.dump(pipeline, FICHIER_MODELE)
    FICHIER_INFOS.write_text(json.dumps(infos, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nModèle sauvegardé : {FICHIER_MODELE.name}")
