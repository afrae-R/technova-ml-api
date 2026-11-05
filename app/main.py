"""L'API : la porte d'entrée du modèle.

Lancer (depuis la racine du projet) :
    python -m uvicorn app.main:app --reload
Puis ouvrir http://127.0.0.1:8000/docs dans le navigateur (page Swagger).
"""
import logging
import secrets
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Request, Security
from fastapi.security import APIKeyHeader
from sqlalchemy.engine import Engine

from app.config import CHEMIN_INFOS, CHEMIN_MODELE, lire_cle_api
from app.modele import ModeleAttrition
from app.schemas import FicheSalarie, PredictionReponse
from db.connexion import creer_moteur
from db.journal import enregistrer_prediction

# Les messages écrits ici apparaissent dans le terminal où tourne l'API
journal = logging.getLogger("uvicorn.error")


@asynccontextmanager
async def cycle_de_vie(app: FastAPI):
    """Exécuté une seule fois au démarrage : on charge la clé et le modèle en mémoire."""
    app.state.cle_api = lire_cle_api()  # refuse de démarrer si la clé n'est pas configurée
    app.state.modele = ModeleAttrition(CHEMIN_MODELE, CHEMIN_INFOS)
    # Moteur de la base PostgreSQL (pour enregistrer les prédictions).
    # Si DATABASE_URL n'est pas configurée, l'API démarre quand même, sans enregistrement.
    try:
        app.state.moteur = creer_moteur()
    except RuntimeError as erreur:
        app.state.moteur = None
        journal.warning("Enregistrement en base désactivé : %s", erreur)
    yield


app = FastAPI(
    title="TechNova - API de prédiction du départ des salariés",
    version="0.4.0",
    description=(
        "Reçoit la fiche d'un salarié et renvoie l'estimation du risque de départ.\n\n"
        "**Attention :** le modèle est réglé pour ne manquer presque aucun départ : sur le jeu de test "
        "(294 salariés dont 47 départs) il en détecte 37 (rappel de 79 %), mais environ 7 alertes sur 10 "
        "sont de fausses alertes (précision de 0,30 ; F1 de la classe « Oui » de 0,43). "
        "La réponse est « Oui » quand le score atteint le seuil de décision (environ 0,38). "
        "Il constitue une aide à la décision, pas un outil de décision automatique.\n\n"
        "Chaque prédiction réussie est enregistrée dans PostgreSQL (tables `requetes` et `predictions`).\n\n"
        "Les requêtes de prédiction nécessitent la clé d'accès dans l'en-tête `X-API-Key` "
        "(bouton **Authorize** ci-dessous)."
    ),
    lifespan=cycle_de_vie,
)

# Déclare l'en-tête attendu ; fait aussi apparaître le bouton "Authorize" dans Swagger
en_tete_cle = APIKeyHeader(name="X-API-Key", auto_error=False, description="Clé d'accès à l'API")


def verifier_cle(request: Request, cle: str | None = Security(en_tete_cle)):
    """Vérification n°2 : l'expéditeur connaît-il la clé secrète ?"""
    attendue = request.app.state.cle_api
    # compare_digest compare sans révéler, par le temps de calcul, combien de caractères sont corrects
    if cle is None or not secrets.compare_digest(cle.encode(), attendue.encode()):
        raise HTTPException(
            status_code=401,
            detail="Clé d'API absente ou invalide.",
            headers={"WWW-Authenticate": "ApiKey"},
        )


def obtenir_moteur(request: Request) -> Engine | None:
    """Fournit le moteur de la base de données (ou None si la base n'est pas configurée).

    C'est une « dépendance » FastAPI : les tests pourront la remplacer par une base de test.
    """
    return request.app.state.moteur


def journaliser(moteur: Engine | None, fiche: dict, etiquette: str, score: float):
    """Enregistre la prédiction en base, sans jamais empêcher l'API de répondre.

    Si la base est absente ou en panne, on note l'erreur dans le terminal, mais l'utilisateur
    reçoit quand même sa réponse : la prédiction reste utile même sans journal.
    """
    if moteur is None:
        return
    try:
        enregistrer_prediction(moteur, fiche, etiquette, score)
    except Exception:
        journal.exception("Impossible d'enregistrer la prédiction dans la base")


@app.get("/health", tags=["Supervision"], summary="Vérifier que l'API fonctionne")
def sante():
    """Accessible sans clé : sert à vérifier que le service tourne."""
    return {"statut": "ok", "modele_charge": True}


@app.post(
    "/predict",
    response_model=PredictionReponse,
    dependencies=[Depends(verifier_cle)],
    tags=["Prédiction"],
    summary="Estimer le risque de départ d'un salarié",
    responses={
        401: {"description": "Clé d'API absente ou invalide"},
        422: {"description": "Fiche invalide (champ manquant, valeur hors des règles...)"},
    },
)
def predire(fiche: FicheSalarie, request: Request, moteur: Engine | None = Depends(obtenir_moteur)):
    """Vérification n°1 faite par Pydantic (FicheSalarie), puis calcul par le modèle, puis journal."""
    donnees = fiche.model_dump()
    etiquette, score = request.app.state.modele.predire(donnees)
    journaliser(moteur, donnees, etiquette, score)
    return PredictionReponse(prediction=etiquette, probabilite_depart=score)
