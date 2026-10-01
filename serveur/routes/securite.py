from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from serveur.services.service_ssh import modifier_etat_port, log_audit
from serveur.routes.auth import require_admin
import sqlite3

router = APIRouter()

class RequeteIsolation(BaseModel):
    ip_cible: str
    mac_cible: str
    motif: str
    # Les switchs et ports devraient être déduits du traçage, donc on les prend
    ip_switch: str
    port: str

@router.post("/isoler")
async def isoler_equipement(requete: RequeteIsolation, user=Depends(require_admin)):
    resultat = modifier_etat_port(requete.ip_switch, requete.port, "ISOLER")
    statut = "SUCCES" if resultat["succes"] else "ECHEC"
    log_audit(user["sub"], requete.ip_cible, requete.ip_switch, requete.port, requete.motif, "ISOLER", statut)
    
    if not resultat["succes"]:
        raise HTTPException(status_code=502, detail=resultat["message"])
    return {"succes": True, "message": resultat["message"]}

@router.post("/restaurer")
async def restaurer_equipement(requete: RequeteIsolation, user=Depends(require_admin)):
    resultat = modifier_etat_port(requete.ip_switch, requete.port, "RESTAURER")
    statut = "SUCCES" if resultat["succes"] else "ECHEC"
    log_audit(user["sub"], requete.ip_cible, requete.ip_switch, requete.port, requete.motif, "RESTAURER", statut)
    
    if not resultat["succes"]:
        raise HTTPException(status_code=502, detail=resultat["message"])
    return {"succes": True, "message": resultat["message"]}

@router.get("/historique")
async def obtenir_historique(user=Depends(require_admin)):
    try:
        conn = sqlite3.connect("iplocator.db")
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM audit_logs ORDER BY date DESC LIMIT 50").fetchall()
        return {"historique": [dict(r) for r in rows]}
    except:
        return {"historique": []}
