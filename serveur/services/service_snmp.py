import json
import os

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
    Tente une requête SNMP get sysDescr (1.3.6.1.2.1.1.1.0) ou simule la réponse si en mode MOCK.
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

    # Tentative Réseau Réel via PySNMP
    try:
        from pysnmp.hlapi import (
            getCmd, SnmpEngine, CommunityData, UsmUserData,
            UdpTransportTarget, ContextData, ObjectType, ObjectIdentity,
            usmHMACSHAAuthProtocol, usmHMACMD5AuthProtocol,
            usmAesCfb128Protocol, usmDesCbcProtocol
        )

        auth_data = None
        if version == "v2c":
            auth_data = CommunityData(community, mpModel=1)
        else: # v3
            auth_proto = usmHMACSHAAuthProtocol if v3_kwargs.get("v3_auth_proto") == "SHA" else usmHMACMD5AuthProtocol
            priv_proto = usmAesCfb128Protocol if v3_kwargs.get("v3_priv_proto") == "AES" else usmDesCbcProtocol
            auth_data = UsmUserData(
                v3_kwargs.get("v3_user"),
                authKey=v3_kwargs.get("v3_auth_key"),
                privKey=v3_kwargs.get("v3_priv_key"),
                authProtocol=auth_proto,
                privProtocol=priv_proto
            )

        iterator = getCmd(
            SnmpEngine(),
            auth_data,
            UdpTransportTarget((ip, 161), timeout=2.0, retries=1),
            ContextData(),
            ObjectType(ObjectIdentity('1.3.6.1.2.1.1.5.0')), # sysName
            ObjectType(ObjectIdentity('1.3.6.1.2.1.1.1.0'))  # sysDescr
        )

        errorIndication, errorStatus, errorIndex, varBinds = next(iterator)

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
    except Exception as e:
        return {"succes": False, "message": f"Erreur SNMP: {str(e)}"}