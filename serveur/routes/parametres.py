import json
import os
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, Literal
from serveur.services.service_snmp import tester_connexion_snmp

router = APIRouter()

CONFIG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config")
CONFIG_FILE = os.path.join(CONFIG_DIR, "settings.json")

# Configuration par défaut
DEFAULT_SETTINGS = {
    "mode": "MOCK",  # "MOCK" ou "REAL_NETWORK"
    "core_switch_ip": "10.20.0.1",
    "core_switch_brand": "Cisco",
    "snmp_version": "v2c",
    "snmp_community": "ASECNA_READ",
    "snmp_v3_user": "asecna_admin",
    "snmp_v3_auth_key": "AuthKeySecure123",
    "snmp_v3_priv_key": "PrivKeySecure123",
    "snmp_v3_auth_proto": "SHA",
    "snmp_v3_priv_proto": "AES",
    "ssh_username": "admin",
    "ssh_password": "adminpassword",
    "theme": "Dark NOC",
    "custom_logo_path": "../image/Logo_ASECNA.png"
}

def charger_parametres():
    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR, exist_ok=True)
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_SETTINGS, f, indent=4)
        return DEFAULT_SETTINGS
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return DEFAULT_SETTINGS

def sauvegarder_parametres(data: dict):
    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

class SchemaParametres(BaseModel):
    mode: Literal["MOCK", "REAL_NETWORK"] = "MOCK"
    core_switch_ip: str
    core_switch_brand: Literal["Cisco", "Huawei", "Generic"] = "Cisco"
    snmp_version: Literal["v2c", "v3"] = "v2c"
    snmp_community: Optional[str] = "public"
    snmp_v3_user: Optional[str] = ""
    snmp_v3_auth_key: Optional[str] = ""
    snmp_v3_priv_key: Optional[str] = ""
    snmp_v3_auth_proto: Optional[Literal["MD5", "SHA"]] = "SHA"
    snmp_v3_priv_proto: Optional[Literal["DES", "AES"]] = "AES"
    ssh_username: Optional[str] = ""
    ssh_password: Optional[str] = ""
    theme: Optional[Literal["Dark NOC", "Cyberpunk", "Light Professional"]] = "Dark NOC"
    custom_logo_path: Optional[str] = "../image/Logo_ASECNA.png"

class RequeteTestSNMP(BaseModel):
    ip: str
    version: str
    community: Optional[str] = "public"
    v3_user: Optional[str] = ""
    v3_auth_key: Optional[str] = ""
    v3_priv_key: Optional[str] = ""
    v3_auth_proto: Optional[str] = "SHA"
    v3_priv_proto: Optional[str] = "AES"

@router.get("", response_model=SchemaParametres)
async def obtenir_parametres():
    """Récupère les paramètres de configuration actuels."""
    return charger_parametres()

@router.post("")
async def enregistrer_parametres(params: SchemaParametres):
    """Enregistre les nouveaux paramètres (Réservé ADMIN)."""
    sauvegarder_parametres(params.dict())
    return {"succes": True, "message": "Paramètres réseau mis à jour avec succès."}

@router.post("/tester")
async def tester_snmp(requete: RequeteTestSNMP):
    """Teste la connexion SNMP vers l'IP Cœur configurée."""
    resultat = tester_connexion_snmp(
        ip=requete.ip,
        version=requete.version,
        community=requete.community,
        v3_user=requete.v3_user,
        v3_auth_key=requete.v3_auth_key,
        v3_priv_key=requete.v3_priv_key,
        v3_auth_proto=requete.v3_auth_proto,
        v3_priv_proto=requete.v3_priv_proto
    )
    if not resultat.get("succes"):
        raise HTTPException(status_code=400, detail=resultat.get("message", "Échec du test SNMP."))
    return resultat