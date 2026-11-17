# Documentation technique du modèle et de sa maintenance

Ce document décrit le modèle de prédiction du départ des salariés (issu du Projet 4), ses performances,
ses limites et la façon de le maintenir. Tous les chiffres viennent de `ml/modele_attrition_infos.json`,
fichier écrit automatiquement par `python -m ml.train`.

## 1. Fiche d'identité

| Élément | Valeur |
|---------|--------|
| Objectif | Estimer, pour UN salarié, le risque qu'il quitte l'entreprise (réponse `Oui` / `Non` et note entre 0 et 1) |
| Algorithme | Forêt aléatoire (`RandomForestClassifier`, scikit-learn 1.9.0) |
| Réglages | 100 arbres, profondeur maximale 8, `min_samples_split` = 10, `class_weight="balanced"`, graine 42 |
| Réglages trouvés par | `GridSearchCV` au Projet 4 |
| Données | 3 fichiers CSV du dossier `data/` (SIRH, évaluations, sondage) : 1470 salariés |
| Découpage | 80 % entraînement (1176 salariés) / 20 % test (294), graine 42, découpage stratifié (même part de départs dans les deux) |
| Fichiers | `ml/modele_attrition.joblib` (préparation + modèle dans un seul objet) et `ml/modele_attrition_infos.json` (versions, seuil, scores) |
| Code | `ml/preprocessing.py` (préparation, partagée avec l'API) et `ml/train.py` (entraînement) |

## 2. Données d'entrée

L'API reçoit 23 informations par salarié (voir Swagger, `/docs`). Le code (`ml/preprocessing.py`) en tire les 21
colonnes que le modèle utilise :

- 6 colonnes en texte, transformées en 0/1 par `OneHotEncoder` : genre, statut marital, département, poste,
  domaine d'étude, fréquence de déplacement. Une catégorie jamais vue à l'entraînement ne fait pas planter
  l'API (`handle_unknown="ignore"`).
- 13 colonnes numériques utilisées telles quelles (âge, revenu mensuel, satisfactions, notes, distance, etc.).
- 2 variables créées à partir de 4 des 23 informations :
  - `surcharge_travail` = 1 si le salarié fait des heures supplémentaires ET si son équilibre vie pro/perso est <= 2 ;
  - `experience_externe` = années d'expérience totale moins années dans l'entreprise.

Colonnes écartées au Projet 4 (doublons ou valeur identique pour tous) : `ayant_enfants`,
`nombre_experiences_precedentes`, `niveau_hierarchique_poste`, `note_evaluation_actuelle`,
`annees_sous_responsable_actuel`.

Le même code de préparation sert à l'entraînement et à l'API : on évite ainsi de préparer les données d'une façon
à l'entraînement et d'une autre en production.

## 3. Seuil de décision

Le modèle calcule une note entre 0 et 1. L'API répond `Oui` si la note atteint le seuil **0,381**
(et `Non` sinon, y compris pile au seuil pour `Oui`).

Pourquoi ce seuil : rater un départ coûte plus cher qu'une fausse alerte. On a donc fixé une cible de rappel de 70 %
(choix métier du Projet 4). Le seuil retenu est le plus élevé qui détecte encore au moins 70 % des départs, calculé par
validation croisée sur le jeu d'entraînement uniquement. Le jeu de test n'est jamais utilisé pour le choisir.

## 4. Performances

Jeu de test : 294 salariés dont 47 départs, avec le seuil 0,381.

| Mesure | Valeur |
|--------|--------|
| Départs détectés | 37 sur 47 (rappel 0,787) |
| Départs manqués | 10 |
| Fausses alertes | 87 (précision 0,298 : environ 7 alertes sur 10 sont fausses) |
| F1 de la classe « Oui » | 0,433 (0,457 au seuil 0,50) |
| Matrice de confusion (réel Non / Oui ; prédit Non / Oui) | [[160, 87], [10, 37]] |
| F1 « Oui » sur l'entraînement | 0,597 |
| Validation croisée sur l'entraînement (seuil 0,50) | F1 moyen 0,495 ; rappel moyen 0,521 |

## 5. Limites à connaître

- Performance modeste : le modèle est une aide à la décision, pas un outil de décision automatique.
- Beaucoup de fausses alertes (précision 0,30) : c'est le prix payé pour détecter 79 % des départs.
- F1 de 0,60 à l'entraînement contre 0,43 au test : léger surapprentissage.
- La note n'est pas une probabilité calibrée : 0,40 ne veut pas dire « 40 % de chances de partir ».
- Le modèle ne connaît que les données TechNova de 1470 salariés ; il peut se tromper sur un profil très différent.
- Les fiches sont des données personnelles : accès restreint, HTTPS et durée de conservation à prévoir en production.

## 6. Protocole de maintenance et de mise à jour

Ce protocole est une procédure à suivre par l'équipe ; rien n'est lancé automatiquement.

### 6.1 Quand agir

| Fréquence | Contrôle |
|-----------|----------|
| À chaque modification du code | La CI GitHub Actions lance les 90 tests ; la fusion dans `main` est refusée s'ils échouent |
| Tous les mois | Lire la base (`python -m db.journal` et `python -m db.requetes`) : nombre de prédictions, part de « Oui ». Une part de « Oui » très différente de celle observée au test (environ 42 % : 124 alertes sur 294) mérite une enquête |
| Tous les 6 mois | Mettre à jour les bibliothèques et vérifier les alertes de sécurité ; changer les mots de passe et la clé d'API |
| Tous les ans, ou dès que de nouvelles données de départs réels sont disponibles | Réentraîner le modèle (6.2) |

Autres déclencheurs de réentraînement : changement important de l'entreprise (réorganisation, nouveaux postes ou
départements), part de « Oui » durablement anormale, ou comparaison des prédictions avec les départs réels qui
montre une baisse de qualité. Comparer aux départs réels demande de les collecter ; cette collecte n'existe pas
encore dans le projet.

### 6.2 Réentraîner le modèle, étape par étape

1. Créer une branche : `git switch -c feature/reentrainement-AAAA-MM`.
2. Remplacer ou compléter les fichiers CSV du dossier `data/` (mêmes colonnes qu'avant).
3. Lancer `python -m ml.train`. Lire le rapport affiché : rappel, précision, F1, matrice de confusion.
4. Contrôler les résultats : le rappel doit rester proche de la cible de 70 % et la précision et le F1 ne doivent pas
   s'effondrer par rapport au tableau du paragraphe 4. Sinon, ne pas mettre en service et chercher la cause.
5. Lancer `python -m pytest`. Certains tests comparent le modèle aux valeurs enregistrées ou à des planchers : si un
   test échoue après un réentraînement voulu, lire le message avant de conclure, puis mettre à jour le test ou les
   valeurs attendues en le justifiant dans le journal de bord.
6. Mettre à jour les chiffres de ce document, du README et de `docs/journal_de_bord.md`.
7. Commit, push, Pull Request, attendre la CI verte, fusionner dans `main`, puis poser un tag de version
   (par exemple `v1.4.0`).

Le modèle et son fichier d'infos sont toujours produits ensemble par `ml/train.py` : ne jamais en remplacer un seul.

### 6.3 Mettre à jour les bibliothèques

Le modèle enregistré est lié à la version de scikit-learn qui l'a créé. Après tout changement de version
de scikit-learn, pandas ou numpy dans `requirements.txt`, il faut réentraîner le modèle (6.2) et relancer les tests.
Les versions sont figées pour que l'installation soit identique partout, y compris sur GitHub.

### 6.4 Revenir en arrière

Tous les modèles livrés sont sauvegardés dans l'historique Git et repérés par un tag de version. En cas de problème
après une mise à jour : `git revert` du commit fautif via une Pull Request, ou retour à la version du tag précédent.

### 6.5 Ce qui n'est pas fait (limites)

- Pas de suivi automatique de la qualité du modèle dans le temps (le tableau de bord est décrit dans le README,
  section « Besoins analytiques », mais non réalisé).
- Pas de mise en ligne sur un serveur public : les environnements `staging` et `production` de la CI vérifient
  seulement que l'application démarre.
- Pas de sauvegarde automatique de la base.
