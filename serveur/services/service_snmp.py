from typing import Dict, Any

def get_topology_mock() -> Dict[str, Any]:
    return {
        "noeuds": [
            {"id": "GW", "label": "Passerelle Principale\n(192.168.1.254)", "type": "router", "ip": "192.168.1.254", "status": "up"},
            {"id": "SW1", "label": "Switch Cœur 1\n(192.168.1.1)", "type": "switch_core", "ip": "192.168.1.1", "status": "up"},
            {"id": "SW2", "label": "Switch Accès A\n(192.168.1.10)", "type": "switch_access", "ip": "192.168.1.10", "status": "up"},
            {"id": "SW3", "label": "Switch Accès B\n(192.168.1.11)", "type": "switch_access", "ip": "192.168.1.11", "status": "up"},
            {"id": "AMHS", "label": "Serveur AMHS\n(192.168.1.100)", "type": "endpoint", "ip": "192.168.1.100", "status": "up"},
            {"id": "SMT", "label": "Serveur SMT\n(192.168.1.101)", "type": "endpoint", "ip": "192.168.1.101", "status": "up"}
        ],
        "liens": [
            {"id": "L1", "source": "GW", "target": "SW1", "status": "active"},
            {"id": "L2", "source": "SW1", "target": "SW2", "status": "active"},
            {"id": "L3", "source": "SW1", "target": "SW3", "status": "active"},
            {"id": "L4", "source": "SW2", "target": "AMHS", "status": "active"},
            {"id": "L5", "source": "SW3", "target": "SMT", "status": "active"}
        ]
    }

def get_metrics_mock() -> Dict[str, int]:
    return {
        "total_equipements": 142,
        "equipements_hors_ligne": 3,
        "ports_actifs": 1024,
        "alertes_securite": 1
    }

def snmp_find_mac_port(mac_address: str) -> Dict[str, Any]:
    # Simulation de recherche dans la table CAM via SNMP
    if mac_address == "00:1A:2B:3C:4D:5E":
        return {
            "switch_ip": "10.20.0.12",
            "switch_nom": "SW-BLOC-TECH-01",
            "port_interface": "GigabitEthernet 1/0/14",
            "vlan": "VLAN 10 (AFTN/AMHS)",
            "vitesse_port": "1 Gbps / Full Duplex",
            "sys_location": "Bloc Technique - Salle Serveurs BGD - Baie 03 / Slot 4",
            "statut": "trouvé"
        }
    return {
        "switch_ip": "",
        "switch_nom": "",
        "port_interface": "",
        "vlan": "",
        "vitesse_port": "",
        "sys_location": "",
        "statut": "non_trouvé"
    }
