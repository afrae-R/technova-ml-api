"""Requêtes SQL d'exemple sur la base TechNova.

Chaque requête pose une question à PostgreSQL. Le résultat est affiché dans le terminal.

Lancer :
    python -m db.requetes
"""
from sqlalchemy import text

from db.connexion import creer_moteur

# nom de la question -> requête SQL
REQUETES = {
    "1. Combien de salariés sont partis, et combien sont restés ?": """
        SELECT a_quitte_l_entreprise AS parti, COUNT(*) AS nombre
        FROM salaries
        GROUP BY a_quitte_l_entreprise
        ORDER BY nombre DESC
    """,
    "2. Revenu mensuel moyen par département": """
        SELECT departement, ROUND(AVG(revenu_mensuel)) AS revenu_moyen, COUNT(*) AS effectif
        FROM salaries
        GROUP BY departement
        ORDER BY revenu_moyen DESC
    """,
    "3. Les 5 dernières prédictions (demande + réponse)": """
        SELECT r.id, r.date_heure, r.age, r.poste, p.prediction, p.probabilite_depart
        FROM requetes r
        JOIN predictions p ON p.requete_id = r.id
        ORDER BY r.date_heure DESC
        LIMIT 5
    """,
    "4. Combien de prédictions « Oui » et « Non » l'API a-t-elle rendues ?": """
        SELECT prediction, COUNT(*) AS nombre
        FROM predictions
        GROUP BY prediction
    """,
}


def lancer_requetes(moteur=None):
    """Exécute chaque requête et affiche le résultat."""
    moteur = moteur or creer_moteur()
    with moteur.connect() as connexion:
        for question, sql in REQUETES.items():
            print(f"\n{question}")
            lignes = connexion.execute(text(sql)).all()
            if not lignes:
                print("   (aucun résultat)")
            for ligne in lignes:
                print("   ", tuple(ligne))


if __name__ == "__main__":
    lancer_requetes()
