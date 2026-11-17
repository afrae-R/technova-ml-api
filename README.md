# TechNova - API de prédiction du départ des salariés

Projet 5 OpenClassrooms : déployer un modèle de Machine Learning.

## Objectif

Exposer, via une API, le modèle de prédiction de l'attrition construit au projet 4,
en respectant les bonnes pratiques d'ingénierie logicielle (Git, tests, base de données, CI/CD).

L'API reçoit la fiche d'UN salarié (23 informations) et renvoie une estimation de son risque de départ :
une note entre 0 et 1 (`probabilite_depart`) et une réponse `Oui` / `Non`.
La réponse est `Oui` quand la note atteint le seuil de décision **0,381**.

**Limites à connaître.** Sur le jeu de test (294 salariés dont 47 départs), le modèle détecte 37 départs
(rappel 0,79), mais environ 7 alertes sur 10 sont de fausses alertes (précision 0,30 ; F1 de la classe « Oui » 0,43).
C'est une aide à la décision, pas un outil de décision automatique.

## Installation (Windows, PowerShell)

Prérequis : Python 3.14 et Git. Les versions des bibliothèques sont figées dans `requirements.txt`
(testées avec Python 3.14.3) : une autre version de Python peut faire échouer l'installation.

1. Télécharger le projet et entrer dans son dossier :

   ```
   git clone https://github.com/afrae-R/technova-ml-api.git
   cd technova-ml-api
   ```

2. Créer l'environnement Python du projet, l'activer et installer les bibliothèques :

   ```
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

3. **Créer le fichier `.env`** (étape indispensable). Ce fichier contient les secrets : il n'est pas sur GitHub,
   il faut donc le créer sur chaque ordinateur.

   ```
   copy .env.example .env
   ```

   Puis ouvrir `.env` et remplacer la valeur de `API_KEY` par une vraie clé secrète. Pour en générer une :

   ```
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

   Sans clé valide, l'API **refuse volontairement de démarrer** et affiche :
   `API_KEY n'est pas configurée. Copiez .env.example en .env ...`.
   (La valeur d'exemple `change-moi` est refusée.)

   `DATABASE_URL` n'est pas nécessaire pour lancer l'API : sans elle, l'API démarre avec un avertissement
   et n'enregistre simplement pas les prédictions. Elle sert à la journalisation et aux scripts de la base de données.

## Lancer l'API

```
python -m uvicorn app.main:app
```

Attendre le message `Application startup complete.`, puis ouvrir http://127.0.0.1:8000/docs (page Swagger).

## Utiliser l'API

- `GET /health` : vérifie que l'API fonctionne (sans clé).
- `POST /predict` : estime le risque de départ d'un salarié.
  La clé doit être envoyée dans l'en-tête `X-API-Key`.

Dans Swagger :

1. Cliquer sur **Authorize**, coller la valeur de `API_KEY` de votre fichier `.env`, valider, fermer.
2. Ouvrir **POST /predict**, cliquer sur **Try it out** (Swagger pré-remplit un exemple de fiche), puis **Execute**.

D'autres fiches d'exemple sont dans `docs/exemples_entrees.json`.

Codes de réponse :

| Code | Signification |
|------|---------------|
| 200 | Prédiction réussie : `{"prediction": "Oui" ou "Non", "probabilite_depart": 0.xxxx}` |
| 401 | Clé d'API absente ou invalide |
| 422 | Fiche invalide (champ manquant, valeur hors des règles) |

## Authentification et sécurité

- Chaque appel à `/predict` doit présenter la clé secrète dans l'en-tête `X-API-Key` ; la comparaison est faite
  avec `secrets.compare_digest`.
- Les secrets (clé d'API, mot de passe de la base) sont uniquement dans le fichier `.env`, listé dans `.gitignore`
  et jamais publié. `.env.example` montre les variables à définir, sans valeur réelle.
- Toutes les fiches sont validées (types, bornes, valeurs permises, cohérence) avant d'atteindre le modèle,
  puis la base applique ses propres règles.
- Le projet ne stocke aucun mot de passe d'utilisateur : il n'y a qu'une clé d'API, lue dans `.env`. Le hachage de
  mots de passe n'est donc pas nécessaire ici. Si chaque utilisateur avait sa propre clé, on ne stockerait que son
  empreinte (hash), jamais la clé elle-même.
- Limite connue : en développement, la base est utilisée avec l'administrateur `postgres` ; en production il faudrait
  un utilisateur dédié aux droits limités.

## Tests

```
python -m pytest
python -m pytest --cov=app --cov=db --cov-report=term-missing
```

Les 29 tests couvrent l'API (200, 401, 422, respect du seuil, enregistrement en base, API qui répond si la base est
en panne), la base (tables, types, contraintes, suppression en cascade), les scripts de la base (création, chargement,
requêtes) et des cas limites (règles de cohérence de la fiche, clé d'API ou adresse de base non configurée).
Ils utilisent une clé de test et une base de test : SQLite en mémoire sur l'ordinateur local, et une base PostgreSQL 16 jetable
démarrée par le robot GitHub Actions (variable `TEST_DATABASE_URL`). Ils ne touchent jamais à la vraie base ni à la vraie clé.

La couverture totale est de 97 % (voir `docs/rapport_couverture.txt`). Les seules lignes non exécutées sont les 9 lignes
de lancement à la main des scripts (blocs `if __name__ == "__main__"`).

## CI/CD (GitHub Actions)

Le fichier `.github/workflows/ci.yml` :

- à chaque `push` et Pull Request : installe Python 3.14 et les bibliothèques, puis lance les tests avec la couverture ;
- ensuite, job `staging` (environnement GitHub `staging`) : démarre l'API et vérifie que `/health` répond ; il tourne aussi sur les Pull Request ;
- enfin, sur `main` seulement, job `production` (environnement GitHub `production`) : même vérification, uniquement si `staging` a réussi.

Chaque environnement a son propre secret `API_KEY`, enregistré dans les réglages du dépôt GitHub (Settings > Environments) :
la clé n'est jamais dans le code et elle est distincte de celle du fichier `.env` local.
Ces « déploiements » sont des vérifications de démarrage, pas une mise en ligne sur un serveur public.

## Déploiement et environnements

Ce projet ne comprend pas de mise en ligne sur un serveur public : les jobs `staging` et `production` de la CI/CD
vérifient que l'application démarre et répond sur `/health`. Pour la déployer sur un serveur, les étapes seraient :

1. Installer Python 3.14, puis les bibliothèques : `pip install -r requirements.txt`.
2. Installer PostgreSQL 16, créer la base `technova`, puis lancer `python -m db.create_db`.
3. Définir `API_KEY` et `DATABASE_URL` comme variables d'environnement du serveur (ou dans un fichier `.env` non publié).
   Ne jamais les écrire dans le code.
4. Lancer l'API : `python -m uvicorn app.main:app --host 0.0.0.0 --port 8000`.
5. Placer l'API derrière une connexion HTTPS, car les fiches contiennent des données personnelles.
6. Vérifier que `GET /health` répond `{"statut": "ok", ...}`.

Les environnements du projet :

| Environnement | Où | Clé d'API | Base de données |
|---------------|----|-----------|-----------------|
| Développement | Ordinateur local | `API_KEY` du fichier `.env` | PostgreSQL local (`DATABASE_URL`) |
| Test | `pytest` (local et GitHub) | Clé de test, jamais la vraie | SQLite en mémoire en local ; PostgreSQL 16 jetable sur GitHub |
| Staging | GitHub Actions (environnement `staging`) | Secret propre à `staging` | Aucune (vérification de démarrage) |
| Production | GitHub Actions (environnement `production`) | Secret propre à `production` | Aucune (vérification de démarrage) |

## Le modèle

Le modèle entraîné (`ml/modele_attrition.joblib`) et sa fiche d'identité (`ml/modele_attrition_infos.json`, qui contient
le seuil de décision) sont fournis dans le dépôt : il n'est pas nécessaire de ré-entraîner pour utiliser l'API.
Pour le ré-entraîner : `python -m ml.train`.

## Base de données PostgreSQL

Nécessite PostgreSQL 16 installé, une base nommée `technova` et `DATABASE_URL` renseignée dans `.env`.

```
python -m db.create_db          # crée les 3 tables
python -m db.charger_salaries   # charge les 1470 salariés
python -m db.journal            # compte les demandes et prédictions enregistrées
python -m db.requetes           # lance les requêtes SQL d'exemple
```

Trois tables : `salaries` (les 1470 salariés), `requetes` (chaque fiche reçue par l'API, avec la date) et
`predictions` (chaque réponse, reliée à sa demande). À chaque appel réussi de `/predict`, l'API écrit une ligne dans
`requetes` et une dans `predictions`. Le schéma et les règles sont décrits dans `docs/modele_donnees.md`.

### Parcours des données

1. **Entraînement** : les 3 fichiers CSV du dossier `data/` sont assemblés et nettoyés (`ml/preprocessing.py`), puis
   `ml/train.py` fabrique le modèle et son seuil de décision.
2. **Référence** : `python -m db.charger_salaries` charge une seule fois les 1470 salariés (avec la vraie réponse)
   dans la table `salaries`.
3. **À chaque appel de l'API** : la fiche est validée, le modèle calcule le score, puis une ligne est écrite dans
   `requetes` (la fiche et la date) et une dans `predictions` (la réponse et le score), dans une même transaction.
   Si la base est indisponible, l'API répond quand même et l'erreur est notée dans le terminal.
4. **Protection** : les fiches ne contiennent ni nom ni prénom, mais ce sont des données personnelles (âge, revenu,
   situation familiale). En production : accès restreint à la base, HTTPS et durée de conservation à définir.

### Besoins analytiques (data analyse / tableau de bord)

Non réalisé dans ce projet, mais le besoin est le suivant : un tableau de bord pour les RH et l'équipe data, qui lirait
les tables `requetes` et `predictions` pour suivre le nombre de prédictions par jour, la part de réponses « Oui », la
répartition des scores et les profils les plus souvent signalés. À terme, il comparerait les prédictions aux départs
réels pour surveiller la qualité du modèle dans le temps.

Un point de départ existe : `python -m db.requetes` exécute 4 requêtes SQL d'exemple (départs et restés, revenu moyen
par département, 5 dernières prédictions avec jointure, répartition des réponses « Oui » et « Non »). Un outil de
tableau de bord pourrait se connecter à PostgreSQL avec un utilisateur en lecture seule.

## Conventions Git

- Chaque sujet est travaillé dans une **branche dédiée**, créée depuis `main`. Nom de la branche : `feature/<sujet>` pour
  une fonctionnalité (exemple : `feature/tests-couverture`) et `docs/<sujet>` pour la documentation (exemple :
  `docs/correction-journal`).
- Une branche est fusionnée dans `main` par **Pull Request** ; les tests de la CI se lancent à chaque Pull Request.
- Un **message de commit** décrit ce qui a changé, en une phrase (exemple : « Ajoute les tests Pytest de l'API et de la
  base de données »).
- Les **versions** sont marquées par des tags `vMAJEUR.MINEUR.CORRECTIF`, posés sur `main` après une fusion
  (exemple : `v1.2.1` pour une petite correction).
- **Gestion des conflits** : un conflit apparaît quand deux branches modifient la même ligne ; Git ne choisit pas
  lui-même, pour ne pas effacer le travail de l'autre. Aucun conflit n'a été rencontré dans ce projet (une seule
  personne, une branche par sujet). Le cas échéant, on le résout avec l'outil de VS Code (garder ma version, l'autre
  ou les deux), puis `git add`, `git commit` et `git push`.
- Les standards de code et d'expérimentation ML sont décrits dans `docs/standards_code_et_ml.md`.

## Structure du projet

```
technova-ml-api/
├── .github/workflows/  # Pipeline CI/CD (GitHub Actions)
├── app/                # L'API (FastAPI) : routes, validation des données, sécurité
├── ml/                 # Entraînement et sauvegarde du modèle
├── db/                 # Base PostgreSQL : schéma, création, chargement, journalisation, requêtes
├── tests/              # Tests automatiques (Pytest)
├── data/               # Jeux de données utilisés
├── docs/               # Documentation (journal de bord, schéma de la base, exemples d'entrées)
├── requirements.txt    # Bibliothèques Python nécessaires
├── pytest.ini          # Configuration des tests
├── .env.example        # Modèle de fichier de configuration (sans secrets)
└── README.md
```
