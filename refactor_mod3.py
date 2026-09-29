import os
import re

BASE_DIR = 'E:/projet mémoire/iplocator_light/IpLocator'

def write_file(filepath, content):
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

# tracage.py
tracage_content = '''from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from serveur.services.service_arp import resolve_name_to_ip, resolve_ip_to_mac, resolve_ip_to_hostname, get_mac_vendor
from serveur.services.service_snmp import tracer_chemin_reseau, get_current_settings
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
'''
write_file(os.path.join(BASE_DIR, 'serveur', 'routes', 'tracage.py'), tracage_content)

# decouverte.py
decouverte_content = '''from fastapi import APIRouter, Depends
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
'''
write_file(os.path.join(BASE_DIR, 'serveur', 'routes', 'decouverte.py'), decouverte_content)

# service_ssh.py
ssh_content = '''import asyncio
import sqlite3
import datetime
from netmiko import ConnectHandler
from typing import Dict, Any
from serveur.configuration import SSH_USERNAME, SSH_PASSWORD

def log_audit(username: str, cible: str, switch: str, port: str, motif: str, action: str, statut: str):
    try:
        conn = sqlite3.connect("iplocator.db")
        conn.execute("""CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY, date TEXT, user TEXT, cible TEXT, 
            switch TEXT, port TEXT, motif TEXT, action TEXT, statut TEXT)""")
        conn.execute("INSERT INTO audit_logs (date, user, cible, switch, port, motif, action, statut) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                     (datetime.datetime.now().isoformat(), username, cible, switch, port, motif, action, statut))
        conn.commit()
    except: pass

def executer_commande_ssh(ip_switch: str, commande: str) -> str:
    device = {
        'device_type': 'cisco_ios',
        'host': ip_switch,
        'username': SSH_USERNAME,
        'password': SSH_PASSWORD,
        'secret': SSH_PASSWORD, 
        'port': 22,
        'timeout': 10
    }
    try:
        with ConnectHandler(**device) as net_connect:
            net_connect.enable()
            output = net_connect.send_command(commande)
            return output
    except Exception as e:
        raise Exception(f"Erreur SSH: {str(e)}")

def modifier_etat_port(ip_switch: str, port: str, action: str) -> Dict[str, Any]:
    cmd_action = "shutdown" if action == "ISOLER" else "no shutdown"
    try:
        device = {
            'device_type': 'cisco_ios', 'host': ip_switch, 'username': SSH_USERNAME,
            'password': SSH_PASSWORD, 'secret': SSH_PASSWORD, 'port': 22, 'timeout': 10
        }
        with ConnectHandler(**device) as net_connect:
            net_connect.enable()
            net_connect.send_config_set([f"interface {port}", cmd_action])
            
            # Vérification réelle du statut
            verification = net_connect.send_command(f"show interface {port} | include line protocol")
            statut_reel = "down" if "is down" in verification.lower() or "administratively down" in verification.lower() else "up"
            succes = (action == "ISOLER" and statut_reel == "down") or (action == "RESTAURER" and statut_reel == "up")
            
            if succes: return {"succes": True, "message": f"Port {port} modifié avec succès."}
            else: return {"succes": False, "message": f"L'état réel du port est {statut_reel}."}
    except Exception as e:
        return {"succes": False, "message": f"Erreur SSH: {str(e)}"}
'''
write_file(os.path.join(BASE_DIR, 'serveur', 'services', 'service_ssh.py'), ssh_content)

# securite.py
securite_content = '''from fastapi import APIRouter, HTTPException, Depends
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
'''
write_file(os.path.join(BASE_DIR, 'serveur', 'routes', 'securite.py'), securite_content)

print("Module 3 refactored")
