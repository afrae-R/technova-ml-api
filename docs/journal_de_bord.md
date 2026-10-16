# Journal de bord - Projet 5 (déploiement du modèle TechNova)

Ce fichier garde la trace de ce qui a été fait, des choix techniques (et de leurs raisons),
des problèmes rencontrés et de ce qui reste à faire. Il sert aussi de base pour justifier
les choix techniques devant le jury.

## Contexte

- Mission : déployer le modèle de prédiction de départ des salariés du Projet 4 (TechNova)
  derrière une API, pour le client fictif Futurisys (interlocuteur : Aurélien, responsable technique).
- Soutenance : lundi 12 octobre 2026 (30 min : 15 min de présentation, 10 min de discussion, débrief).
- Livrables : dépôt Git, API FastAPI documentée, tests Pytest + couverture, base PostgreSQL,
  pipeline CI/CD (YAML, environnements, secrets), README complet.

## Planning

| Jour | Contenu | État |
|---|---|---|
| Mar. 6 oct. | Git/GitHub, environnement, modèle sauvegardé | Fait |
| Mer. 7 oct. | API FastAPI + Pydantic + clé d'accès + Swagger | À faire |
| Jeu. 8 oct. | Base PostgreSQL (schéma, script de création, dataset, journalisation, requêtes) | À faire |
| Ven. 9 oct. | Tests Pytest + couverture (API et base) | À faire |
| Sam. 10 oct. | CI/CD GitHub Actions (tests + déploiement, environnements, secrets) | À faire |
| Dim. 11 oct. | README final, schéma UML, support de présentation, répétition | À faire |
| Lun. 12 oct. | Vérifications finales, soutenance | |

## Ce qui a été fait (6 octobre 2026)

- Dépôt GitHub `technova-ml-api`, branches de fonctionnalité + Pull Requests :
  `feature/structure-projet` (PR #1), `feature/versions-figees` (PR #2), `feature/modele-ml` (PR #3).
- Tag `v0.1.0` (structure initiale).
- Environnement virtuel `.venv` créé avec `uv`, dépendances installées depuis `requirements.txt`.
- Modèle entraîné et sauvegardé : `ml/modele_attrition.joblib` (+ `ml/modele_attrition_infos.json`).

## Choix techniques et pourquoi

- **Branches + Pull Requests** : `main` reste propre ; chaque idée est isolée dans une branche
  et relue avant fusion. Un commit = une idée.
- **Environnement virtuel + versions figées** : le modèle est lié à la version de scikit-learn
  qui l'a créé ; tout le monde (API, CI) doit utiliser les mêmes versions.
- **Pipeline scikit-learn** (OneHotEncoder + RandomForest) au lieu de `pd.get_dummies` :
  une API reçoit un seul salarié à la fois ; `get_dummies` ne connaît que ce qu'il voit
  (une seule ligne = colonnes manquantes ou dans un autre ordre). `OneHotEncoder` mémorise
  les catégories vues à l'entraînement ; `handle_unknown="ignore"` évite un plantage sur une
  catégorie inconnue. Le traducteur et le modèle sont sauvegardés ensemble avec `joblib`.
- **`ml/preprocessing.py` partagé** entre l'entraînement et l'API : une seule version du
  nettoyage et de la création des variables (`surcharge_travail`, `experience_externe`),
  pour éviter les écarts entre entraînement et production.
- **Variables retirées** (décisions du Projet 4) : `ayant_enfants` (une seule valeur),
  `nombre_experiences_precedentes`, `niveau_hierarchique_poste`, `note_evaluation_actuelle`,
  `annees_sous_responsable_actuel` (corrélations trop fortes avec d'autres variables).
- **Secrets** : `.env` n'est jamais publié (`.gitignore`) ; `.env.example` sert de modèle.

## Résultats du modèle (honnêtes)

- Test (294 salariés, dont 47 partants) : F1 "Oui" = 0,35 (précision 0,32, rappel 0,38),
  accuracy 0,77 (un modèle qui répond toujours "Non" ferait 0,84).
- F1 "Oui" train = 0,83 contre 0,35 en test : surapprentissage.
- F1 "Oui" en validation croisée : 0,48 (+/- 0,05), estimation plus fiable que le test seul.
- Conclusion à présenter : performance modeste ; le modèle est une aide à la décision,
  pas un outil de décision automatique. Le Projet 5 porte sur le déploiement, pas sur la performance.

## Problèmes rencontrés

- **Windows a bloqué des fichiers techniques** ("Une stratégie de contrôle d'application a bloqué
  ce fichier") : `scipy 1.18.1`, puis `scikit-learn 1.9.1`. Solution : revenir aux versions
  déjà acceptées par la machine (`scipy 1.18.0`, `scikit-learn 1.9.0`) et les figer dans
  `requirements.txt`. À surveiller pour les autres bibliothèques et l'installation de PostgreSQL.
- `Ctrl + C` dans le terminal arrête le programme (ce n'est pas "copier").

## Ce que vérifie la fiche d'autoévaluation (points à ne pas oublier)

- Git : historique clair, branches dédiées, tags ; requirements.txt exhaustif ;
  installation automatisée lors du déploiement.
- Base de données : schéma détaillé avec relations et contraintes ; script de création ;
  dataset inséré ; exemples d'entrées ; **script de journalisation des interactions
  utilisateur / modèle** ; scripts de requêtes.
- API : FastAPI, expose le modèle, documentation Swagger (endpoints, schémas, exemples d'appels),
  pas d'erreur de validation des données.
- Tests : Pytest, cas critiques **et** cas d'erreur, tests sur la base (insertion, suppression,
  types, présence/absence de valeurs), rapport de couverture.
- CI/CD : YAML GitHub Actions qui lance les tests et le déploiement ; environnements
  développement/production (test optionnel) ; gestion des secrets.
- README : projet, installation, utilisation, déploiement, authentification, bonnes pratiques
  de sécurité (secrets, hachage), processus de stockage des données, besoins analytiques.
- Savoir justifier ses choix techniques.

## Questions probables du jury

1. Quels défis avec FastAPI et comment les avez-vous surmontés ?
2. Quelle est votre stratégie de tests et comment assurez-vous une couverture complète ?
3. Comment avez-vous géré la configuration de la base et son intégration avec le modèle ?

## À poser au mentor

- Comment montrer le "déploiement" dans le YAML alors que l'API est déployée en local ?
