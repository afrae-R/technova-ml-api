"""L'API : la porte d'entrée du modèle.

Lancer (depuis la racine du projet) :
    python -m uvicorn app.main:app --reload
Puis ouvrir http://127.0.0.1:8000/docs dans le navigateur (page Swagger).
"""
import secrets
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Request, Security
from fastapi.security import APIKeyHeader

from app.config import CHEMIN_MODELE, lire_cle_api
from app.modele import ModeleAttrition
from app.schemas import FicheSalarie, PredictionReponse


@asynccontextmanager
async def cycle_de_vie(app: FastAPI):
    """Exécuté une seule fois au démarrage : on charge la clé et le modèle en mémoire."""
    app.state.cle_api = lire_cle_api()  # refuse de démarrer si la clé n'est pas configurée
    app.state.modele = ModeleAttrition(CHEMIN_MODELE)
    yield


app = FastAPI(
    title="TechNova - API de prédiction du départ des salariés",
    version="0.2.0",
    description=(
        "Reçoit la fiche d'un salarié et renvoie l'estimation du risque de départ.\n\n"
        "**Attention :** le modèle a des performances modestes (F1 de la classe « Oui » "
        "d'environ 0,35 sur le jeu de test). Il constitue une aide à la décision, "
        "pas un outil de décision automatique.\n\n"
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
def predire(fiche: FicheSalarie, request: Request):
    """Vérification n°1 faite par Pydantic (FicheSalarie), puis calcul par le modèle."""
    etiquette, score = request.app.state.modele.predire(fiche.model_dump())
    return PredictionReponse(prediction=etiquette, probabilite_depart=score)
