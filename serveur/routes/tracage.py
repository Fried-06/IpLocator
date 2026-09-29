from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from serveur.services.service_arp import resolve_name_to_ip, resolve_ip_to_mac, resolve_ip_to_hostname, get_mac_vendor
from serveur.services.service_snmp import tracer_chemin_reseau
from serveur.routes.parametres import charger_parametres as get_current_settings
from serveur.routes.auth import require_admin

router = APIRouter()

class RequeteTracage(BaseModel):
    cible: str

@router.post("")
async def executer_tracage(requete: RequeteTracage, user=Depends(require_admin)):
    cible = requete.cible.strip()
    is_ip = re.match(r"^(\d{1,3}\.){3}\d{1,3}$", cible)
    ip_address = cible if is_ip else resolve_name_to_ip(cible)
    
    if not ip_address:
        raise HTTPException(status_code=404, detail="Cible introuvable (impossible de résoudre l'IP)")
        
    mac = resolve_ip_to_mac(ip_address)
    if not mac:
        raise HTTPException(status_code=404, detail="Cible introuvable dans la table ARP")

    hostname = resolve_ip_to_hostname(ip_address) or "N/D"
    constructeur = get_mac_vendor(mac)
    
    settings = get_current_settings()
    ip_depart = settings.get("core_switch_ip")
    if not ip_depart:
        raise HTTPException(status_code=500, detail="Core switch IP non configurée")

    res_trace = await tracer_chemin_reseau(ip_depart, mac, settings.get("snmp_version", "v2c"), settings.get("snmp_community", "public"))
    if not res_trace.get("succes"):
        raise HTTPException(status_code=500, detail=res_trace.get("message", "Echec du traçage"))

    # Nettoyage complet des données statiques / fallback (plus de Wi-Fi factice)
    # Les vraies métriques de VLAN ou vitesse nécessiteraient plus de MIBs, on laisse "N/D" pour l'instant
    
    return {
        "succes": True,
        "ip": ip_address,
        "mac": mac,
        "hostname": hostname,
        "constructeur": constructeur,
        "vlan": "N/D",
        "localisation": "N/D",
        "chemin": res_trace.get("chemin", []),
        "port_acces_final": res_trace.get("port_acces_final", "N/D"),
        "type_connexion": "N/D"
    }
