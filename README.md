# TechNova - API de prédiction du départ des salariés

Projet 5 OpenClassrooms : déployer un modèle de Machine Learning.

## Objectif

Exposer, via une API, le modèle de prédiction de l'attrition construit au projet 4,
en respectant les bonnes pratiques d'ingénierie logicielle (Git, tests, base de données, CI/CD).

## Structure du projet

```
technova-ml-api/
├── app/             # L'API (FastAPI) : routes, validation des données, sécurité
├── ml/              # Entraînement et sauvegarde du modèle
├── db/              # Base PostgreSQL : schéma, création, chargement des données
├── tests/           # Tests automatiques (Pytest)
├── data/            # Jeux de données utilisés
├── docs/            # Documentation (schéma de la base, notes techniques)
├── requirements.txt # Bibliothèques Python nécessaires
├── .env.example     # Modèle de fichier de configuration (sans secrets)
└── README.md
```

*(Ce README sera complété au fil du projet : installation, utilisation, déploiement, authentification, sécurité.)*
