"""Entraînement du modèle de prédiction du départ des salariés TechNova.

Lancer depuis la racine du projet :
    python -m ml.train

Résultat : le fichier ml/modele_attrition.joblib (modèle + préparation des données
dans un seul objet) et ml/modele_attrition_infos.json (versions, seuil de décision, scores).

Ce script reproduit le modèle final du Projet 4 : mêmes données, même découpage
train/test, mêmes réglages, et le même seuil de décision calibré sur le jeu
d'entraînement uniquement (jamais sur le test).
"""
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    f1_score,
    make_scorer,
    precision_recall_curve,
    precision_score,
    recall_score,
)
from sklearn.model_selection import cross_val_predict, cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from ml.preprocessing import (
    COLONNES_CATEGORIELLES,
    COLONNES_NUMERIQUES,
    charger_donnees_brutes,
    preparer_entrainement,
)

DOSSIER_ML = Path(__file__).resolve().parent
FICHIER_MODELE = DOSSIER_ML / "modele_attrition.joblib"
FICHIER_INFOS = DOSSIER_ML / "modele_attrition_infos.json"
GRAINE = 42  # fixe le hasard : on obtient les mêmes résultats à chaque lancement
RAPPEL_CIBLE = 0.70  # on veut détecter au moins 70 % des départs (choix métier du Projet 4)


def construire_pipeline():
    """Assemble la 'recette' : préparation des colonnes + modèle.

    L'ordre est le même que dans le notebook du Projet 4 : d'abord les colonnes
    numériques, puis les colonnes texte transformées en 0/1 (la première catégorie
    de chaque colonne est retirée, comme avec pd.get_dummies(drop_first=True)).
    Ainsi le modèle obtenu est identique à celui du Projet 4.
    """
    preparation = ColumnTransformer(
        transformers=[
            ("numerique", "passthrough", COLONNES_NUMERIQUES),
            # handle_unknown="ignore" : une catégorie jamais vue ne fait pas planter l'API.
            (
                "texte",
                OneHotEncoder(drop="first", handle_unknown="ignore"),
                COLONNES_CATEGORIELLES,
            ),
        ]
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


def calculer_seuil(X_train, y_train):
    """Choisit le seuil à partir duquel le modèle répond « Oui ».

    Méthode du Projet 4 : on fait prédire chaque salarié d'entraînement par un modèle qui
    ne l'a pas vu (validation croisée), puis on retient le seuil LE PLUS ÉLEVÉ qui détecte
    encore au moins 70 % des départs. Le jeu de test n'est jamais utilisé ici.
    """
    probabilites = cross_val_predict(
        construire_pipeline(), X_train, y_train, cv=5, method="predict_proba"
    )
    position_oui = sorted(set(y_train)).index("Oui")
    _, rappels, seuils = precision_recall_curve(
        y_train, probabilites[:, position_oui], pos_label="Oui"
    )
    seuils_valides = np.where(rappels[:-1] >= RAPPEL_CIBLE)[0]
    return float(seuils[seuils_valides[np.argmax(seuils[seuils_valides])]])


def entrainer():
    X, y = preparer_entrainement(charger_donnees_brutes())
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=GRAINE, stratify=y
    )

    pipeline = construire_pipeline()
    pipeline.fit(X_train, y_train)
    seuil = calculer_seuil(X_train, y_train)

    # Prédictions avec le seuil calibré : « Oui » si le score atteint le seuil
    position_oui = list(pipeline.classes_).index("Oui")
    score_test = pipeline.predict_proba(X_test)[:, position_oui]
    score_train = pipeline.predict_proba(X_train)[:, position_oui]
    predictions = np.where(score_test >= seuil, "Oui", "Non")
    predictions_train = np.where(score_train >= seuil, "Oui", "Non")
    predictions_050 = np.where(score_test >= 0.5, "Oui", "Non")

    precision = precision_score(y_test, predictions, pos_label="Oui")
    rappel = recall_score(y_test, predictions, pos_label="Oui")
    f1_test = f1_score(y_test, predictions, pos_label="Oui")
    f1_train = f1_score(y_train, predictions_train, pos_label="Oui")
    f1_test_050 = f1_score(y_test, predictions_050, pos_label="Oui")
    matrice = confusion_matrix(y_test, predictions, labels=["Non", "Oui"])

    # Validation croisée sur le jeu d'entraînement (seuil 0,50) : le score est-il stable ?
    f1_cv = cross_val_score(
        construire_pipeline(), X_train, y_train, cv=5, scoring=make_scorer(f1_score, pos_label="Oui")
    )
    rappel_cv = cross_val_score(
        construire_pipeline(), X_train, y_train, cv=5, scoring=make_scorer(recall_score, pos_label="Oui")
    )

    print(f"Seuil de décision calibré : {seuil:.3f} (« Oui » si le score atteint ce seuil)")
    print("\n=== Résultats sur le jeu de TEST (examen final), avec ce seuil ===")
    print(classification_report(y_test, predictions, digits=3))
    print("Matrice de confusion (lignes = réalité, colonnes = prédiction ; ordre Non, Oui) :")
    print(matrice)
    print(f"\nF1 'Oui' train : {f1_train:.2f} | test : {f1_test:.2f} (au seuil 0,50 : {f1_test_050:.2f})")
    print(f"F1 'Oui' validation croisée (train, seuil 0,50) : {f1_cv.mean():.2f} (+/- {f1_cv.std():.2f})")
    print(f"Rappel 'Oui' validation croisée (train, seuil 0,50) : {rappel_cv.mean():.2f} (+/- {rappel_cv.std():.2f})")

    infos = {
        "version_scikit_learn": sklearn.__version__,
        "version_pandas": pd.__version__,
        "colonnes_attendues": list(X.columns),
        "seuil_decision": seuil,
        "rappel_cible_pour_le_seuil": RAPPEL_CIBLE,
        "precision_oui_test": round(float(precision), 3),
        "rappel_oui_test": round(float(rappel), 3),
        "f1_oui_train": round(float(f1_train), 3),
        "f1_oui_test": round(float(f1_test), 3),
        "f1_oui_test_au_seuil_050": round(float(f1_test_050), 3),
        "matrice_confusion_test_non_oui": matrice.tolist(),
        "f1_oui_validation_croisee_train_moyenne": round(float(f1_cv.mean()), 3),
        "rappel_oui_validation_croisee_train_moyenne": round(float(rappel_cv.mean()), 3),
        "nb_salaries_entrainement": int(len(X_train)),
        "nb_salaries_test": int(len(X_test)),
    }
    return pipeline, infos


if __name__ == "__main__":
    pipeline, infos = entrainer()
    joblib.dump(pipeline, FICHIER_MODELE)
    FICHIER_INFOS.write_text(json.dumps(infos, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nModèle sauvegardé : {FICHIER_MODELE.name}")
    print(f"Informations et seuil sauvegardés : {FICHIER_INFOS.name}")
