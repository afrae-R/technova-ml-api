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
- Limite connue : en développement, la base est utilisée avec l'administrateur `postgres` ; en production il faudrait
  un utilisateur dédié aux droits limités.

## Tests

```
python -m pytest
python -m pytest --cov=app --cov=db --cov-report=term-missing
```

Les 20 tests couvrent l'API (200, 401, 422, respect du seuil, enregistrement en base, API qui répond si la base est
en panne) et la base (tables, types, contraintes, suppression en cascade). Ils utilisent une base SQLite en mémoire
et une clé de test : ils ne touchent jamais à la vraie base ni à la vraie clé.

## CI/CD (GitHub Actions)

Le fichier `.github/workflows/ci.yml` :

- à chaque `push` et Pull Request : installe Python 3.14 et les bibliothèques, puis lance les tests avec la couverture ;
- ensuite, job `staging` (environnement GitHub `staging`) : démarre l'API et vérifie que `/health` répond ; il tourne aussi sur les Pull Request ;
- enfin, sur `main` seulement, job `production` (environnement GitHub `production`) : même vérification, uniquement si `staging` a réussi.

Chaque environnement a son propre secret `API_KEY`, enregistré dans les réglages du dépôt GitHub (Settings > Environments) :
la clé n'est jamais dans le code et elle est distincte de celle du fichier `.env` local.
Ces « déploiements » sont des vérifications de démarrage, pas une mise en ligne sur un serveur public.

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
