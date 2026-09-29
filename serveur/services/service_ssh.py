import asyncio
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
