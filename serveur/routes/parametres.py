import json, os
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Literal
from serveur.routes.auth import require_admin
from serveur.services.service_snmp import tester_connexion_snmp

router = APIRouter()
CONFIG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config")
CONFIG_FILE = os.path.join(CONFIG_DIR, "settings.json")

def charger_parametres():
    if not os.path.exists(CONFIG_FILE): return {}
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except: return {}

def sauvegarder_parametres(data: dict):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

class SchemaParametres(BaseModel):
    core_switch_ip: Optional[str] = None
    core_switch_brand: Optional[str] = None
    snmp_version: Optional[str] = None
    snmp_community: Optional[str] = None
    ssh_username: Optional[str] = None
    ssh_password: Optional[str] = None

@router.get("")
async def obtenir_parametres(user=Depends(require_admin)):
    data = charger_parametres()
    if data.get("snmp_community"): data["snmp_community"] = "********"
    if data.get("ssh_password"): data["ssh_password"] = "********"
    return data

@router.post("")
async def enregistrer_parametres(params: SchemaParametres, user=Depends(require_admin)):
    sauvegarder_parametres(params.dict(exclude_unset=True))
    return {"succes": True}
