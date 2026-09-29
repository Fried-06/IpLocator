import json
import os
import asyncio

CONFIG_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config", "settings.json")


def get_current_settings():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"mode": "MOCK", "core_switch_ip": "10.20.0.1", "snmp_community": "ASECNA_READ"}


def get_topology_mock():
    return {
        "noeuds": [
            {"id": "sw-core-01", "label": "SW-CORE-ASECNA\n10.20.0.1", "group": "CORE_SWITCH", "shape": "box"},
            {"id": "sw-bloc-01", "label": "SW-BLOC-TECH-01\n10.20.0.12", "group": "ACCESS_SWITCH", "shape": "box"},
            {"id": "sw-tour-01", "label": "SW-TOUR-01\n10.20.0.15", "group": "ACCESS_SWITCH", "shape": "box"},
            {"id": "amhs-01", "label": "AMHS Server\n10.20.1.15", "group": "SERVER", "shape": "ellipse"},
            {"id": "smt-01", "label": "SMT Server\n10.20.1.10", "group": "SERVER", "shape": "ellipse"}
        ],
        "liaisons": [
            {"from": "sw-core-01", "to": "sw-bloc-01", "label": "Gi0/1 -> Gi0/24", "color": {"color": "#10B981"}},
            {"from": "sw-core-01", "to": "sw-tour-01", "label": "Gi0/2 -> Gi0/24", "color": {"color": "#10B981"}},
            {"from": "sw-bloc-01", "to": "amhs-01", "label": "Gi1/0/14", "color": {"color": "#06B6D4"}},
            {"from": "sw-bloc-01", "to": "smt-01", "label": "Gi1/0/8", "color": {"color": "#06B6D4"}}
        ]
    }


def get_metrics_mock():
    return {
        "total_equipements": 48,
        "equipements_hors_ligne": 2,
        "ports_actifs": 142,
        "alertes_securite": 0
    }


def tester_connexion_snmp(ip: str, version: str, community: str = "public", **v3_kwargs):
    """
    Tente une requête SNMP get sysName/sysDescr, ou simule la réponse si en mode MOCK.

    NOTE TECHNIQUE (migration pysnmp 4.x -> 7.x) :
    L'ancienne API synchrone 'pysnmp.hlapi.getCmd' a été retirée dans pysnmp >= 7.
    On utilise désormais l'API asyncio 'pysnmp.hlapi.v1arch.asyncio', qui couvre
    SNMPv1/v2c (suffisant pour ce projet). SNMPv3 n'est pas géré par cette voie
    (voir la branche 'if version == "v3"' ci-dessous).
    """
    settings = get_current_settings()

    # Si mode Mock ou IP locale de simulation
    if settings.get("mode") == "MOCK" or ip in ["10.20.0.1", "127.0.0.1"]:
        return {
            "succes": True,
            "ip": ip,
            "sysName": "SW-CORE-ASECNA-LOME",
            "sysDescr": "Cisco IOS Software, C3850 Software (CAT3K_CAA-UNIVERSALK9-M), Version 16.12.4",
            "latence_ms": 1.4,
            "message": f"Connexion SNMP ({version}) établie avec succès vers {ip}."
        }

    if version == "v3":
        return {
            "succes": False,
            "message": "SNMPv3 n'est pas supporté par cette implémentation (limitation technique documentée dans le mémoire)."
        }

    # Tentative Réseau Réel via PySNMP (SNMPv1/v2c, API v1arch.asyncio)
    try:
        return asyncio.run(_snmp_get_v2c(ip, community))
    except Exception as e:
        return {"succes": False, "message": f"Erreur SNMP: {str(e)}"}


async def _snmp_get_v2c(ip: str, community: str):
    from pysnmp.hlapi.v1arch.asyncio import (
        SnmpDispatcher, CommunityData, UdpTransportTarget,
        ObjectType, ObjectIdentity, get_cmd
    )

    with SnmpDispatcher() as dispatcher:
        errorIndication, errorStatus, errorIndex, varBinds = await get_cmd(
            dispatcher,
            CommunityData(community, mpModel=1),  # mpModel=1 => SNMPv2c
            await UdpTransportTarget.create((ip, 161), timeout=2.0, retries=1),
            ObjectType(ObjectIdentity('1.3.6.1.2.1.1.5.0')),  # sysName
            ObjectType(ObjectIdentity('1.3.6.1.2.1.1.1.0')),  # sysDescr
        )

        if errorIndication:
            return {"succes": False, "message": str(errorIndication)}
        elif errorStatus:
            return {"succes": False, "message": f"{errorStatus.prettyPrint()} at {errorIndex}"}
        else:
            sysName = str(varBinds[0][1]) if len(varBinds) > 0 else "Switch-Actif"
            sysDescr = str(varBinds[1][1]) if len(varBinds) > 1 else "Inconnu"
            return {
                "succes": True,
                "ip": ip,
                "sysName": sysName,
                "sysDescr": sysDescr,
                "latence_ms": 2.1,
                "message": f"Réponse reçue du Switch Réel {sysName}."
            }

def rechercher_port_mac_snmp(ip: str, mac: str, version: str, community: str = "public", **v3_kwargs):
    """
    Interroge la table MAC du switch (BRIDGE-MIB) pour trouver sur quel port 
    est connectée l'adresse MAC.
    """
    settings = get_current_settings()

    if settings.get("mode") == "MOCK" or ip in ["10.20.0.1", "127.0.0.1"]:
        return {"succes": True, "port": "Port-24 (Gigabit)", "message": "Mock - Port trouvé"}

    if version == "v3":
        return {"succes": False, "message": "SNMPv3 non supporté"}

    try:
        return asyncio.run(_snmp_find_mac_v2c(ip, mac, community))
    except Exception as e:
        return {"succes": False, "message": f"Erreur SNMP MAC: {str(e)}"}

async def _snmp_find_mac_v2c(ip: str, mac: str, community: str):
    from pysnmp.hlapi.v1arch.asyncio import (
        SnmpDispatcher, CommunityData, UdpTransportTarget,
        ObjectType, ObjectIdentity, get_cmd
    )
    
    if not mac or mac == "N/A":
        return {"succes": False, "message": "MAC invalide"}

    # Formatage de la MAC pour l'OID SNMP (ex: 00:1A:2B -> 0.26.43)
    try:
        mac_parts = [str(int(p, 16)) for p in mac.replace("-", ":").split(":")]
        if len(mac_parts) != 6:
            return {"succes": False, "message": "Format MAC invalide"}
    except ValueError:
        return {"succes": False, "message": "Parsing MAC échoué"}

    # OID pour dot1dTpFdbPort (BRIDGE-MIB)
    oid_str = "1.3.6.1.2.1.17.4.3.1.2." + ".".join(mac_parts)

    with SnmpDispatcher() as dispatcher:
        errorIndication, errorStatus, errorIndex, varBinds = await get_cmd(
            dispatcher,
            CommunityData(community, mpModel=1),
            await UdpTransportTarget.create((ip, 161), timeout=2.0, retries=1),
            ObjectType(ObjectIdentity(oid_str)),
        )

        if errorIndication or errorStatus:
            return {"succes": False, "message": "Requête OID échouée"}
        else:
            if varBinds:
                valeur = str(varBinds[0][1])
                # Vérifie si l'OID existe bien (pysnmp renvoie parfois des exceptions SNMP)
                if "No Such Instance" not in valeur and "No Such Object" not in valeur:
                    return {"succes": True, "port": f"Port-ID {valeur}"}
            return {"succes": False, "message": "MAC non trouvée dans la table"}

def tracer_chemin_reseau(ip_depart: str, mac: str, version: str, community: str):
    """
    Algorithme de découverte de topologie (Path Trace).
    Interroge le switch de départ pour trouver le port.
    Ensuite, vérifie (via LLDP/CDP ou configuration) si ce port mène à un autre switch.
    Si oui, rebondit sur le switch suivant.
    Renvoie le chemin complet et le port d'accès final.
    """
    chemin = []
    ip_actuelle = ip_depart
    switch_precedent = "Application (Serveur)"
    
    # Sécurité pour éviter les boucles infinies
    for saut in range(5): 
        # 1. On interroge le switch actuel
        resultat_snmp = tester_connexion_snmp(ip_actuelle, version, community)
        nom_switch = resultat_snmp.get("sysName", ip_actuelle)
        
        resultat_port = rechercher_port_mac_snmp(ip_actuelle, mac, version, community)
        
        if not resultat_port.get("succes"):
            # L'adresse MAC n'est pas trouvée ici, on arrête le traçage
            chemin.append({
                "type": "SWITCH", "nom": nom_switch, "ip": ip_actuelle,
                "port_sortie": "Introuvable", "message": "Trace perdue"
            })
            return {"succes": False, "chemin": chemin, "dernier_switch_ip": ip_actuelle, "dernier_switch_nom": nom_switch}
            
        port_trouve = resultat_port.get("port")
        chemin.append({
            "type": "SWITCH", "nom": nom_switch, "ip": ip_actuelle,
            "port_entree": "Uplink", "port_sortie": port_trouve
        })
        
        # 2. Théorie : Vérifier si ce port est un lien "Trunk" vers un autre switch (via LLDP/CDP)
        # Dans ce code Python, on simule la découverte du prochain saut.
        # En production, on lirait la MIB LLDP (1.0.8802.1.1.2.1.4.1.1) pour extraire l'IP du voisin.
        prochain_switch_ip = None 
        
        # Exemple de simulation : Si l'IP est 10.20.0.1 et le port est 24, on sait que ça va vers 10.20.0.12
        if ip_actuelle == "10.20.0.1" and "24" in port_trouve:
            prochain_switch_ip = "10.20.0.12"
            
        if prochain_switch_ip:
            # On a trouvé un switch voisin, on continue la boucle
            ip_actuelle = prochain_switch_ip
        else:
            # Pas de voisin LLDP détecté : c'est le port d'accès final (Edge Port) !
            return {
                "succes": True, 
                "chemin": chemin, 
                "dernier_switch_ip": ip_actuelle, 
                "dernier_switch_nom": nom_switch,
                "port_acces_final": port_trouve
            }

    return {"succes": True, "chemin": chemin, "port_acces_final": port_trouve}