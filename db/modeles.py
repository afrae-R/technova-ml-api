"""Plan de la base de données : les 3 tables du projet.

  salaries     : les 1470 salariés du jeu de données (la « référence » d'entraînement)
  requetes     : une ligne par demande reçue par l'API (ce qui a été envoyé, et quand)
  predictions  : une ligne par réponse du modèle, reliée à sa demande

Chaque classe Python = une table. Chaque attribut = une colonne.
SQLAlchemy lit ce plan et construit les tables dans PostgreSQL.
"""
from datetime import datetime
from typing import get_args

from sqlalchemy import CheckConstraint, DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

# Les listes de valeurs autorisées sont celles de l'API : une seule source de vérité.
from app.schemas import (
    Departement,
    DomaineEtude,
    FrequenceDeplacement,
    Genre,
    OuiNon,
    Poste,
    StatutMarital,
)

# --- Les règles, copiées de app/schemas.py (l'API les vérifie, la base les re-vérifie) ---

# colonne -> (valeur minimale, valeur maximale), bornes incluses
BORNES = {
    "age": (18, 70),
    "revenu_mensuel": (1, 100000),
    "annee_experience_totale": (0, 50),
    "annees_dans_l_entreprise": (0, 50),
    "annees_dans_le_poste_actuel": (0, 50),
    "satisfaction_employe_environnement": (1, 4),
    "note_evaluation_precedente": (1, 4),
    "satisfaction_employe_nature_travail": (1, 4),
    "satisfaction_employe_equipe": (1, 4),
    "satisfaction_employe_equilibre_pro_perso": (1, 4),
    "augmentation_salaire_precedente": (0, 100),
    "nombre_participation_pee": (0, 10),
    "nb_formations_suivies": (0, 20),
    "distance_domicile_travail": (0, 200),
    "niveau_education": (1, 5),
    "annees_depuis_la_derniere_promotion": (0, 50),
}

# colonne -> les seules valeurs de texte permises
CHOIX = {
    "genre": get_args(Genre),
    "statut_marital": get_args(StatutMarital),
    "departement": get_args(Departement),
    "poste": get_args(Poste),
    "heures_supplementaires": get_args(OuiNon),
    "domaine_etude": get_args(DomaineEtude),
    "frequence_deplacement": get_args(FrequenceDeplacement),
}

# Règles qui comparent deux colonnes entre elles
COHERENCE = {
    "experience": "annees_dans_l_entreprise <= annee_experience_totale",
    "poste": "annees_dans_le_poste_actuel <= annees_dans_l_entreprise",
    "promotion": "annees_depuis_la_derniere_promotion <= annees_dans_l_entreprise",
}


def contraintes_fiche(table):
    """Fabrique les interdictions (CHECK) des 23 colonnes d'une fiche salarié.

    On en fabrique de nouvelles pour chaque table, avec le nom de la table dans le nom
    de la règle, pour que chaque règle soit unique et facile à repérer dans PostgreSQL.
    """
    regles = []
    for colonne, (mini, maxi) in BORNES.items():
        regles.append(
            CheckConstraint(f"{colonne} BETWEEN {mini} AND {maxi}", name=f"ck_{table}_{colonne}")
        )
    for colonne, valeurs in CHOIX.items():
        liste = ", ".join(f"'{valeur}'" for valeur in valeurs)
        regles.append(CheckConstraint(f"{colonne} IN ({liste})", name=f"ck_{table}_{colonne}"))
    for nom, condition in COHERENCE.items():
        regles.append(CheckConstraint(condition, name=f"ck_{table}_coherence_{nom}"))
    return regles


class Base(DeclarativeBase):
    """Classe mère : elle garde la liste de toutes les tables du projet."""


class ChampsFiche:
    """Les 23 colonnes d'une fiche salarié, communes aux tables salaries et requetes.

    Aucune n'a le droit d'être vide (NOT NULL) : Mapped[int] sans « Optional »
    veut dire « obligatoire ».
    """

    age: Mapped[int] = mapped_column(Integer)
    genre: Mapped[str] = mapped_column(String(1))
    revenu_mensuel: Mapped[int] = mapped_column(Integer)
    statut_marital: Mapped[str] = mapped_column(String(20))
    departement: Mapped[str] = mapped_column(String(30))
    poste: Mapped[str] = mapped_column(String(40))
    annee_experience_totale: Mapped[int] = mapped_column(Integer)
    annees_dans_l_entreprise: Mapped[int] = mapped_column(Integer)
    annees_dans_le_poste_actuel: Mapped[int] = mapped_column(Integer)
    satisfaction_employe_environnement: Mapped[int] = mapped_column(Integer)
    note_evaluation_precedente: Mapped[int] = mapped_column(Integer)
    satisfaction_employe_nature_travail: Mapped[int] = mapped_column(Integer)
    satisfaction_employe_equipe: Mapped[int] = mapped_column(Integer)
    satisfaction_employe_equilibre_pro_perso: Mapped[int] = mapped_column(Integer)
    heures_supplementaires: Mapped[str] = mapped_column(String(3))
    augmentation_salaire_precedente: Mapped[float] = mapped_column(Float)
    nombre_participation_pee: Mapped[int] = mapped_column(Integer)
    nb_formations_suivies: Mapped[int] = mapped_column(Integer)
    distance_domicile_travail: Mapped[int] = mapped_column(Integer)
    niveau_education: Mapped[int] = mapped_column(Integer)
    domaine_etude: Mapped[str] = mapped_column(String(40))
    frequence_deplacement: Mapped[str] = mapped_column(String(20))
    annees_depuis_la_derniere_promotion: Mapped[int] = mapped_column(Integer)


class Salarie(ChampsFiche, Base):
    """Table « salaries » : les salariés du jeu de données d'entraînement."""

    __tablename__ = "salaries"
    __table_args__ = (
        *contraintes_fiche("salaries"),
        CheckConstraint("a_quitte_l_entreprise IN ('Oui', 'Non')", name="ck_salaries_a_quitte"),
    )

    # Numéro du salarié, repris tel quel des fichiers d'origine (pas de numérotation automatique)
    id_employe: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)
    # La vraie réponse : le salarié est-il parti ?
    a_quitte_l_entreprise: Mapped[str] = mapped_column(String(3))


class Requete(ChampsFiche, Base):
    """Table « requetes » : une ligne par demande reçue par l'API."""

    __tablename__ = "requetes"
    __table_args__ = tuple(contraintes_fiche("requetes"))

    # Numéro unique, donné automatiquement par PostgreSQL
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # Date et heure de la demande, remplies automatiquement par PostgreSQL
    date_heure: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Lien vers la réponse : une demande a une seule réponse
    reponse: Mapped["Prediction"] = relationship(
        back_populates="requete", uselist=False, cascade="all, delete-orphan"
    )


class Prediction(Base):
    """Table « predictions » : la réponse du modèle à une demande."""

    __tablename__ = "predictions"
    __table_args__ = (
        CheckConstraint("prediction IN ('Oui', 'Non')", name="ck_predictions_prediction"),
        CheckConstraint(
            "probabilite_depart BETWEEN 0 AND 1", name="ck_predictions_probabilite_depart"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # Clé étrangère : le numéro de la demande à laquelle cette réponse répond.
    # unique=True : une demande ne peut avoir qu'une seule réponse.
    # ondelete="CASCADE" : si on supprime la demande, sa réponse disparaît avec elle.
    requete_id: Mapped[int] = mapped_column(
        ForeignKey("requetes.id", ondelete="CASCADE"), unique=True
    )
    prediction: Mapped[str] = mapped_column(String(3))
    probabilite_depart: Mapped[float] = mapped_column(Float)

    requete: Mapped["Requete"] = relationship(back_populates="reponse")
