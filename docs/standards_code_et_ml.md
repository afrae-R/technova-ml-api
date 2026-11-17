# Standards de code et d'expérimentation ML

Ce document décrit les règles suivies dans le projet TechNova. Il est écrit à partir de ce qui est réellement
appliqué dans le dépôt.

## 1. Standards de code

- **Organisation** : un dossier = un rôle. `app/` (l'API), `ml/` (fabrication du modèle), `db/` (base de données),
  `tests/` (tests Pytest), `docs/` (documentation).
- **Langue** : les noms de variables, de fonctions et les commentaires sont en français, pour rester lisibles par
  toute l'équipe métier.
- **Documentation du code** : chaque fichier commence par une phrase qui explique son rôle, et chaque fonction
  importante a une courte description.
- **Données vérifiées à l'entrée** : tout ce que l'API reçoit est validé par Pydantic (types, bornes, valeurs permises,
  cohérence) avant d'atteindre le modèle ; la base applique ensuite ses propres règles (contraintes `CHECK`).
- **Secrets** : jamais dans le code. Ils sont lus dans le fichier `.env` (ignoré par Git) ou dans les secrets GitHub
  de chaque environnement.
- **Dépendances** : versions figées dans `requirements.txt`, pour une installation identique partout.
- **Tests** : tout comportement important est couvert par un test Pytest, y compris les cas d'erreur (clé absente,
  fiche invalide, base en panne). La couverture est mesurée avec `pytest-cov` (voir `docs/rapport_couverture.txt`).
- **Git** : une branche par sujet (`feature/<sujet>` ou `docs/<sujet>`), des commits descriptifs, des Pull Requests,
  des tags de version (voir le README, section « Conventions Git »).

## 2. Standards d'expérimentation ML

- **Reproductibilité** : le modèle se refabrique avec une seule commande, `python -m ml.train`. Le hasard est fixé
  (`random_state=42`) pour obtenir les mêmes résultats à chaque lancement.
- **Une seule préparation des données** : `ml/preprocessing.py` est utilisé à la fois à l'entraînement et par l'API,
  pour que les données soient préparées de la même façon aux deux endroits.
- **Découpage** : 80 % des salariés pour l'entraînement (1176), 20 % pour le test (294), stratifié pour garder la même
  proportion de départs dans les deux.
- **Le jeu de test ne sert qu'à l'évaluation finale** : le seuil de décision est calculé uniquement sur le jeu
  d'entraînement, par validation croisée à 5 plis, en visant un rappel d'au moins 70 % des départs.
- **Métriques** : on suit le rappel, la précision et le F1 de la classe « Oui » (les départs), et pas seulement
  l'accuracy, qui est trompeuse quand il y a peu de départs (16 %).
- **Traçabilité** : le modèle est sauvegardé (`ml/modele_attrition.joblib`) avec sa fiche d'identité
  (`ml/modele_attrition_infos.json` : seuil, scores, versions des bibliothèques).
- **Limites assumées** : le score n'est pas une probabilité calibrée, beaucoup d'alertes sont de fausses alertes
  (précision 0,30), et le modèle surapprend légèrement (F1 0,60 à l'entraînement contre 0,43 au test). Il constitue une
  aide à la décision.

## 3. Étapes du pipeline CI/CD (définies avant l'écriture du fichier `ci.yml`)

| Étape | Rôle | Condition de démarrage |
|-------|------|------------------------|
| 1. `tests` | Installer Python et les bibliothèques, lancer les 29 tests Pytest avec la couverture | Chaque Pull Request et chaque push sur `main` |
| 2. `staging` | Démarrer l'API et vérifier que `/health` répond (environnement d'essai, secret propre) | Les tests ont réussi (`needs: tests`) |
| 3. `production` | Même vérification, avec le secret de production | `staging` a réussi, et seulement sur `main` |

Règles : une étape ne démarre que si la précédente a réussi ; chaque environnement a son propre secret ; la durée
totale reste courte (environ 2 min 20). Les tests tournent sur un PostgreSQL 16 jetable dans le robot GitHub (SQLite
en mémoire en local). Limite connue : les étapes `staging` et `production` vérifient le démarrage, sans mise en ligne sur un serveur public.
