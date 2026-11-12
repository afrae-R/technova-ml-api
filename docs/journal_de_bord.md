# Journal de bord - Projet 5 (déploiement du modèle TechNova)

Ce fichier garde la trace de ce qui a été fait, des choix techniques (et de leurs raisons),
des problèmes rencontrés et de ce qui reste à faire. Il sert aussi de base pour justifier
les choix techniques devant le jury.

## Contexte

- Mission : déployer le modèle de prédiction de départ des salariés du Projet 4 (TechNova)
  derrière une API, pour le client fictif Futurisys (interlocuteur : Aurélien, responsable technique).
- Soutenance : **mardi 17 novembre 2026** (reportée plusieurs fois : 12 octobre, 19 octobre, 31 octobre, 10 novembre).
  Format : 30 min = 15 min de présentation, 10 min de discussion, débrief.
- Livrables : dépôt Git, API FastAPI documentée, tests Pytest + couverture, base PostgreSQL,
  pipeline CI/CD (YAML, environnements, secrets), README complet.

## Planning (état au 10 novembre 2026)

Le projet a pris du retard à cause de plusieurs suspensions et de reports de soutenance.

| Étape | Contenu | État |
|---|---|---|
| 1 | Git/GitHub, environnement, modèle sauvegardé | Fait |
| 2 | API FastAPI + Pydantic + clé d'accès + Swagger | Fait |
| 3 | PostgreSQL : installation, base `technova`, 3 tables, chargement des 1 470 salariés | Fait |
| 4 | Mise en conformité avec le modèle final du Projet 4 (seuil de décision 0,381) | Fait |
| 5 | README complété : installation et création du fichier `.env` | Fait |
| 6 | Journalisation des demandes et prédictions dans PostgreSQL | Fait |
| 7 | Tests Pytest (29) avec couverture (97 %) | Fait |
| 8 | CI/CD GitHub Actions (tests, puis vérification de démarrage en `staging` et en `production`) | Fait |
| 9 | Requêtes SQL d'exemple, schéma de la base, exemples d'entrées | Fait |
| 10 | Présentation, archive zip, auto-évaluation, répétition | En cours |

## Ce qui a été fait

### Début octobre
- Dépôt GitHub `technova-ml-api`, branches de fonctionnalité + Pull Requests
  (`feature/structure-projet`, `feature/versions-figees`, `feature/modele-ml`).
- Tag `v0.1.0` (structure initiale).
- Environnement virtuel `.venv` créé avec `uv`, dépendances installées depuis `requirements.txt`.
- Modèle entraîné et sauvegardé : `ml/modele_attrition.joblib` (+ `ml/modele_attrition_infos.json`).

### 16 octobre
- API FastAPI : `GET /health` et `POST /predict`, validation des 23 champs avec Pydantic
  (types, bornes, cohérence entre champs), clé d'accès dans l'en-tête `X-API-Key`
  (401 si absente ou fausse, 422 si les données sont invalides), documentation Swagger sur `/docs`.
- PostgreSQL 16.15 installé (service Windows `postgresql-x64-16`, port 5432), base `technova` créée.

### Fin octobre
- Base de données : plan des 3 tables (`db/modeles.py`), connexion (`db/connexion.py`),
  création (`db/create_db.py`), chargement des 1 470 salariés (`db/charger_salaries.py`).
- **Mise à jour du modèle après les remarques de l'examinateur du Projet 4** : le modèle final utilise
  un seuil de décision de 0,381 au lieu de 0,50. `ml/train.py` reproduit exactement le modèle du
  Projet 4 (mêmes colonnes, même ordre, même encodage, mêmes réglages) et calcule le seuil sur le
  jeu d'entraînement uniquement ; `app/modele.py` lit ce seuil dans `modele_attrition_infos.json`.

### 3 au 5 novembre
- En visio avec le mentor, l'application ne démarrait pas sur mon ordinateur. Pour le diagnostic, le mentor a mis en commentaire
  deux lignes de sécurité et l'application a démarré ; ce contournement temporaire a ensuite été retiré.
  README complété : étapes d'installation et de création du fichier `.env`.
- **Journalisation** (`db/journal.py`, `app/main.py`) : chaque prédiction réussie est enregistrée
  dans `requetes` et `predictions`. Vérifié : 0 ligne avant, 1 demande et 1 prédiction après un appel.

### 8 novembre
- **Tests Pytest** : 20 tests (API : 200, 401, 422, seuil, enregistrement en base, API qui répond
  si la base est en panne ; base : tables, types, contraintes, suppression en cascade).
  Couverture : `main.py` 100 %, `modele.py` 100 %, `db/modeles.py` 100 %, total 78 % à cette date (mesuré sur `app/` et `db/`) ; complété ensuite, voir le 12 novembre.
- **CI/CD** (`.github/workflows/ci.yml`, PR #12) : tests à chaque push et Pull Request ;
  sur `main`, vérification du démarrage de l'API. Exécutions vertes.
- Requêtes SQL d'exemple (`db/requetes.py`), schéma de la base (`docs/modele_donnees.md`),
  exemples d'entrées (`docs/exemples_entrees.json`) (PR #13).
- Présentation de 11 diapositives.

### 10 novembre
- **CI/CD à deux environnements** : le job de déploiement est remplacé par deux jobs, `staging` (aussi lancé sur les Pull Requests)
  puis `production` (sur `main` seulement, uniquement si `staging` a réussi). Chaque environnement a son secret `API_KEY`.
- Ajout de l'environnement `staging` et de son secret dans les réglages GitHub ; README et journal mis à jour.

### 12 novembre
- **Tests complétés** : 9 nouveaux tests (`tests/test_scripts_base.py` et `tests/test_cas_limites.py`) : les scripts de création,
  de chargement et de requêtes de la base testés avec une base SQLite temporaire, deux règles de cohérence de la fiche,
  clé d'API ou adresse de base non configurée. Au total 29 tests, couverture 97 % (78 % avant).

## Choix techniques et pourquoi

- **Branches + Pull Requests** : `main` reste propre ; chaque idée est isolée dans une branche
  et relue avant fusion. Un commit = une idée.
- **Environnement virtuel + versions figées** : le modèle est lié à la version de scikit-learn
  qui l'a créé ; tout le monde (API, CI) doit utiliser les mêmes versions (Python 3.14.3).
- **Pipeline scikit-learn** (OneHotEncoder + RandomForest) au lieu de `pd.get_dummies` :
  une API reçoit un seul salarié à la fois ; `get_dummies` ne connaît que ce qu'il voit.
  `OneHotEncoder` mémorise les catégories vues à l'entraînement ; `handle_unknown="ignore"`
  évite un plantage sur une catégorie inconnue. Le traducteur et le modèle sont sauvegardés
  ensemble avec `joblib`.
- **`ml/preprocessing.py` partagé** entre l'entraînement et l'API : une seule version du
  nettoyage et de la création des variables (`surcharge_travail`, `experience_externe`).
- **Seuil de décision 0,381** : rater un départ coûte plus cher qu'une fausse alerte. Le seuil est le
  plus élevé qui garde un rappel d'au moins 70 % en validation croisée sur l'entraînement
  (le jeu de test n'est jamais utilisé pour le choisir). Il est stocké avec le modèle.
- **Variables retirées** (décisions du Projet 4) : `ayant_enfants`, `nombre_experiences_precedentes`,
  `niveau_hierarchique_poste`, `note_evaluation_actuelle`, `annees_sous_responsable_actuel`.
- **Secrets** : `.env` n'est jamais publié (`.gitignore`) ; `.env.example` sert de modèle.
  L'API refuse de démarrer si `API_KEY` est absente ou égale à la valeur d'exemple.
- **Journalisation tolérante aux pannes** : si la base est absente ou en panne, l'erreur est notée
  dans le terminal mais l'utilisateur reçoit quand même sa réponse. Les deux lignes (demande et
  réponse) sont écrites dans une seule transaction.
- **Base de données avec règles** : colonnes obligatoires, contraintes CHECK (bornes, valeurs
  permises, cohérence entre colonnes), clé étrangère unique avec suppression en cascade.
- **Tests sans toucher à la vraie base** : une base SQLite en mémoire et une clé de test ;
  la dépendance `obtenir_moteur` de l'API est remplacée pendant les tests.
- **PostgreSQL en local** avec l'utilisateur administrateur `postgres` pour le développement.
  Limite : en production, il faudrait un utilisateur dédié aux droits limités (moindre privilège).
- **Pilote de connexion explicite** : adresse `postgresql+psycopg2://...` (SQLAlchemy 2.1.3 cherche
  sinon `psycopg` v3, non installé).
- Pas de caractères spéciaux (`@`, `:`, `/`, `#`, `%`) dans le mot de passe de la base.

## Résultats du modèle (honnêtes)

Modèle final (forêt aléatoire, seuil 0,381), jeu de test de 294 salariés dont 47 partants :

- 37 départs détectés sur 47 (rappel 0,79), 10 manqués.
- 87 fausses alertes : précision 0,30 (environ 7 alertes sur 10 sont fausses).
- F1 de la classe « Oui » : 0,43 (0,46 au seuil de 0,50).
- Matrice de confusion (réel Non / Oui, prédit Non / Oui) : [[160, 87], [10, 37]].
- Validation croisée sur l'entraînement (seuil 0,50) : F1 0,49 (+/- 0,06) ; rappel 0,52 (+/- 0,07).
- F1 « Oui » train 0,60 contre 0,43 en test : léger surapprentissage.
- Le score n'est pas une probabilité calibrée.
- Conclusion à présenter : performance modeste ; le modèle est une aide à la décision, pas un outil
  de décision automatique. Le Projet 5 porte sur le déploiement, pas sur la performance.

## Problèmes rencontrés

- **Windows a bloqué des fichiers techniques** (`scipy 1.18.1`, puis `scikit-learn 1.9.1`).
  Solution : revenir aux versions acceptées (`scipy 1.18.0`, `scikit-learn 1.9.0`) et les figer.
- **Installation de PostgreSQL** : `winget` a échoué deux fois (erreur `0x80190193`, HTTP 403) ;
  installateur officiel EDB téléchargé avec le navigateur. Message « Échec lors du chargement des
  modules SQL dans le cluster » pendant l'installation : après validation, le serveur fonctionne
  (service en marche, `SELECT version()` correct). Cause non identifiée.
- **Erreur de pilote** `No module named 'psycopg'` : voir « Pilote de connexion explicite ».
- **Modèle du Projet 5 différent du modèle final du Projet 4** (ordre des colonnes, encodage) :
  F1 de 0,35 contre 0,43. Corrigé dans `ml/train.py` et vérifié.
- **L'application ne démarrait pas sur mon ordinateur** (constaté en visio avec le mentor). Contournement temporaire pendant le
  diagnostic : deux lignes de sécurité mises en commentaire, puis retirées. Pour toute personne qui installe le projet,
  le README décrit les étapes de création du fichier `.env` (non publié sur GitHub).
- **Fichier `ci.yml` créé au mauvais endroit** (dans `app/.github`) : recréé à la racine.
  VS Code gardait l'ancienne erreur affichée en rouge jusqu'au redémarrage.

## Limites assumées

- Le « déploiement » du CI/CD est une vérification de démarrage de l'API dans le robot GitHub Actions,
  pas une mise en ligne sur un serveur public.
- Deux environnements GitHub (`staging` puis `production`) qui font la même vérification de démarrage ; le développement se fait sur l'ordinateur local.
- Chaque environnement GitHub (`staging`, `production`) a son propre secret `API_KEY`, enregistré dans les réglages du dépôt ;
  ce sont des clés distinctes de celle du `.env` local.
- Les 9 lignes de lancement à la main des scripts (blocs `if __name__ == "__main__"` de `db/create_db.py`,
  `db/charger_salaries.py`, `db/requetes.py` et `db/journal.py`) ne sont pas testées, et `ml/train.py` est hors du
  périmètre mesuré (couverture totale mesurée sur `app/` et `db/` : 97 %, voir `docs/rapport_couverture.txt`).
