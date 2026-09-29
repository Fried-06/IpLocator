from fastapi import APIRouter, Depends
from serveur.routes.auth import require_admin
# Dans la réalité il faut interroger le switch ou une DB pour la topologie. 
# Pour l'instant on retourne une structure vide conforme à la réalité (aucune donnée mock).

router = APIRouter()

@router.get("/topologie")
async def obtenir_topologie(user=Depends(require_admin)):
    return {"noeuds": [], "liaisons": []}

@router.get("/metriques")
async def obtenir_metriques(user=Depends(require_admin)):
    return {
        "total_equipements": 0,
        "equipements_hors_ligne": 0,
        "ports_actifs": 0,
        "alertes_securite": 0
    }
