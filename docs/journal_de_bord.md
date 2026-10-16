# Journal de bord - Projet 5 (déploiement du modèle TechNova)

Ce fichier garde la trace de ce qui a été fait, des choix techniques (et de leurs raisons),
des problèmes rencontrés et de ce qui reste à faire. Il sert aussi de base pour justifier
les choix techniques devant le jury.

## Contexte

- Mission : déployer le modèle de prédiction de départ des salariés du Projet 4 (TechNova)
  derrière une API, pour le client fictif Futurisys (interlocuteur : Aurélien, responsable technique).
- Soutenance : **reportée au lundi 19 octobre 2026** (initialement le 12 octobre).
  Format : 30 min = 15 min de présentation, 10 min de discussion, débrief.
- Livrables : dépôt Git, API FastAPI documentée, tests Pytest + couverture, base PostgreSQL,
  pipeline CI/CD (YAML, environnements, secrets), README complet.

## Planning

Le planning initial (soutenance le 12 octobre) a glissé : le projet a été suspendu plusieurs jours,
puis la soutenance a été reportée au 19 octobre. Planning mis à jour le 16 octobre :

| Jour | Contenu | État |
|---|---|---|
| Mar. 6 oct. | Git/GitHub, environnement, modèle sauvegardé | Fait |
| Ven. 16 oct. (matin) | API FastAPI + Pydantic + clé d'accès + Swagger | Fait |
| Ven. 16 oct. | PostgreSQL : installation, base `technova`, connexion testée | Fait |
| Ven. 16 oct. | Base : schéma (3 tables), script de création, chargement du dataset | À faire |
| Sam. 17 oct. | Journalisation des requêtes/prédictions dans l'API, scripts de requêtes, tests Pytest + couverture | À faire |
| Dim. 18 oct. | CI/CD GitHub Actions, README final, schéma UML, support de présentation, répétition | À faire |
| Lun. 19 oct. | Vérifications finales, soutenance | |

## Ce qui a été fait (6 octobre 2026)

- Dépôt GitHub `technova-ml-api`, branches de fonctionnalité + Pull Requests :
  `feature/structure-projet` (PR #1), `feature/versions-figees` (PR #2), `feature/modele-ml` (PR #3).
- Tag `v0.1.0` (structure initiale).
- Environnement virtuel `.venv` créé avec `uv`, dépendances installées depuis `requirements.txt`.
- Modèle entraîné et sauvegardé : `ml/modele_attrition.joblib` (+ `ml/modele_attrition_infos.json`).

## Ce qui a été fait (16 octobre 2026)

- Journal de bord ajouté au dépôt (PR #4).
- API FastAPI (PR #5) : `GET /health` et `POST /predict`, validation des 23 champs avec Pydantic
  (types, bornes, cohérence entre champs), clé d'accès dans l'en-tête `X-API-Key`
  (401 si absente ou fausse, 422 si les données sont invalides), documentation Swagger sur `/docs`.
  Testée à la main dans Swagger.
- PostgreSQL 16.15 installé sur la machine (service Windows `postgresql-x64-16`, port 5432),
  base `technova` créée, connexion testée depuis Python avec l'adresse lue dans `.env`.

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
  Le mot de passe PostgreSQL et la clé d'API ne sont que dans `.env`.
- **PostgreSQL en local** avec l'utilisateur administrateur `postgres` pour le développement.
  Limite connue : en production, il faudrait un utilisateur dédié à l'application avec des
  droits limités (principe du moindre privilège). À mentionner dans le README.
- **Pilote de connexion explicite** : l'adresse de la base est de la forme
  `postgresql+psycopg2://utilisateur:motdepasse@localhost:5432/technova`. Avec SQLAlchemy 2.1.3,
  l'adresse simple `postgresql://` cherche le pilote `psycopg` (v3), non installé ;
  on précise donc `+psycopg2` pour utiliser le pilote déjà installé (`psycopg2-binary`).
  Choix aussi prudent vis-à-vis du blocage Windows : pas de nouvelle bibliothèque binaire.
- Pas de caractères spéciaux (`@`, `:`, `/`, `#`, `%`) dans le mot de passe de la base,
  car il est écrit dans une adresse où ces symboles ont un sens particulier.

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
  `requirements.txt`. À surveiller pour les autres bibliothèques.
- `Ctrl + C` dans le terminal arrête le programme (ce n'est pas "copier").
- **Installation de PostgreSQL** :
  - `winget install PostgreSQL.PostgreSQL.16` a échoué deux fois en cours de téléchargement
    (erreur `0x80190193`, HTTP 403 « Interdit », vers 130 Mo sur 385 Mo). Cause non identifiée.
    Solution : télécharger l'installateur officiel EDB avec le navigateur
    (page https://www.enterprisedb.com/downloads/postgres-postgresql-downloads).
  - Un premier téléchargement a donné « fichier utilisé par une autre application » ;
    un second téléchargement, laissé finir, a fonctionné.
  - Pendant l'installation : « Échec lors du chargement des modules SQL dans le cluster de
    base de données ». Après validation du message, l'installation s'est terminée. Par prudence,
    le serveur a été vérifié : service en marche, connexion Python réussie, requête
    `SELECT version()` correcte (PostgreSQL 16.15). Cause de l'erreur non identifiée ;
    le journal de l'installateur (dossier `%TEMP%`) n'a pas été consulté.
- **Erreur de pilote** `No module named 'psycopg'` : voir « Pilote de connexion explicite » ci-dessus.

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
