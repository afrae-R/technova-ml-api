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

   `DATABASE_URL` n'est pas nécessaire pour lancer l'API pour le moment ; elle sert aux scripts de la base de données.

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

Codes de réponse :

| Code | Signification |
|------|---------------|
| 200 | Prédiction réussie : `{"prediction": "Oui" ou "Non", "probabilite_depart": 0.xxxx}` |
| 401 | Clé d'API absente ou invalide |
| 422 | Fiche invalide (champ manquant, valeur hors des règles) |

## Le modèle

Le modèle entraîné (`ml/modele_attrition.joblib`) et sa fiche d'identité (`ml/modele_attrition_infos.json`, qui contient
le seuil de décision) sont fournis dans le dépôt : il n'est pas nécessaire de ré-entraîner pour utiliser l'API.
Pour le ré-entraîner : `python -m ml.train`.

## Base de données PostgreSQL

Nécessite PostgreSQL 16 installé, une base nommée `technova` et `DATABASE_URL` renseignée dans `.env`.

```
python -m db.create_db
python -m db.charger_salaries
```

Trois tables sont créées : `salaries` (les 1470 salariés), `requetes` et `predictions`.

## Structure du projet

```
technova-ml-api/
├── app/             # L'API (FastAPI) : routes, validation des données, sécurité
├── ml/              # Entraînement et sauvegarde du modèle
├── db/              # Base PostgreSQL : schéma, création, chargement des données
├── tests/           # Tests automatiques (Pytest)
├── data/            # Jeux de données utilisés
├── docs/            # Documentation (journal de bord, notes techniques)
├── requirements.txt # Bibliothèques Python nécessaires
├── .env.example     # Modèle de fichier de configuration (sans secrets)
└── README.md
```

*(Ce README sera complété au fil du projet : journalisation en base, tests, déploiement automatique.)*
