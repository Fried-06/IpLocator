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
    mode: Optional[str] = None
    core_switch_ip: Optional[str] = None
    gateway_ip: Optional[str] = None
    core_switch_brand: Optional[str] = None
    snmp_version: Optional[str] = None
    snmp_community: Optional[str] = None
    ssh_username: Optional[str] = None
    ssh_password: Optional[str] = None
    theme: Optional[str] = None
    custom_logo_path: Optional[str] = None

class SchemaTestSnmp(BaseModel):
    ip: str
    version: str = "v2c"
    community: Optional[str] = "public"
    v3_user: Optional[str] = None
    v3_auth_key: Optional[str] = None
    v3_priv_key: Optional[str] = None
    v3_auth_proto: Optional[str] = "SHA"
    v3_priv_proto: Optional[str] = "AES"

@router.get("")
async def obtenir_parametres(user=Depends(require_admin)):
    data = charger_parametres()
    data_copie = dict(data)
    if data_copie.get("snmp_community"): data_copie["snmp_community"] = "********"
    if data_copie.get("ssh_password"): data_copie["ssh_password"] = "********"
    return data_copie

@router.post("")
async def enregistrer_parametres(params: SchemaParametres, user=Depends(require_admin)):
    existants = charger_parametres()
    nouvelles_donnees = params.dict(exclude_unset=True)
    
    # Préserver les valeurs existantes si masquées ou non modifiées
    if nouvelles_donnees.get("snmp_community") in ["********", "", None]:
        nouvelles_donnees["snmp_community"] = existants.get("snmp_community", "public")
    if nouvelles_donnees.get("ssh_password") in ["********", "", None]:
        nouvelles_donnees["ssh_password"] = existants.get("ssh_password", "")

    existants.update(nouvelles_donnees)
    sauvegarder_parametres(existants)
    return {"succes": True}

@router.post("/tester")
async def tester_snmp(test_params: SchemaTestSnmp, user=Depends(require_admin)):
    community = test_params.community or "public"
    if community == "********":
        actuel = charger_parametres()
        community = actuel.get("snmp_community", "public")
    
    resultat = await tester_connexion_snmp(
        test_params.ip,
        test_params.version,
        community=community,
        v3_user=test_params.v3_user,
        v3_auth_key=test_params.v3_auth_key,
        v3_priv_key=test_params.v3_priv_key,
        v3_auth_proto=test_params.v3_auth_proto,
        v3_priv_proto=test_params.v3_priv_proto
    )
    return resultat

