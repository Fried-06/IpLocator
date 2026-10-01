import os
import re

BASE_DIR = 'E:/projet mémoire/iplocator_light/IpLocator'

def write_file(filepath, content):
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

# Refonte service_arp.py
arp_content = '''import subprocess
import re
import socket
import asyncio
from typing import Optional, Tuple

def ping_host(ip: str, timeout_ms: int = 1500) -> Tuple[bool, float]:
    try:
        # Compatible Windows / Linux basique (on privilégie Windows comme demandé initialement)
        cmd = ["ping", "-n", "1", "-w", str(timeout_ms), ip] if os.name == 'nt' else ["ping", "-c", "1", "-W", str(timeout_ms//1000 or 1), ip]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=3)
        if res.returncode == 0:
            match = re.search(r"(?:temps|time)[=<](\d+(?:\.\d+)?)ms", res.stdout, re.IGNORECASE)
            if match: return True, float(match.group(1))
            return True, 1.0
        return False, 0.0
    except: return False, 0.0

def resolve_ip_to_mac(ip_address: str) -> Optional[str]:
    ping_host(ip_address, timeout_ms=500)
    try:
        res = subprocess.run(["arp", "-a"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=2)
        if res.returncode == 0:
            for line in res.stdout.splitlines():
                if ip_address in line:
                    for p in line.split():
                        if re.match(r"^([0-9a-fA-F]{2}[:-]){5}([0-9a-fA-F]{2})$", p):
                            return p.replace("-", ":").upper()
    except: pass
    return None

def resolve_name_to_ip(name: str) -> Optional[str]:
    try: return socket.gethostbyname(name.strip())
    except: return None

def resolve_ip_to_hostname(ip_address: str) -> Optional[str]:
    try:
        host, _, _ = socket.gethostbyaddr(ip_address)
        return host
    except: return None

def get_mac_vendor(mac: str) -> str:
    if not mac or mac == "N/A" or len(mac) < 8: return "Inconnu"
    prefix = mac[:8].upper().replace("-", ":")
    known_ouis = {
        "00:1A:2B": "Cisco Systems", "00:50:56": "VMware Virtual", "00:0C:29": "VMware Virtual",
        "00:15:5D": "Microsoft Hyper-V", "B8:27:EB": "Raspberry Pi", "F0:92:1C": "Apple, Inc.",
        "50:C7:BF": "TP-Link Technologies", "70:4D:7B": "Huawei Technologies", "F4:60:E2": "Dell Inc."
    }
    return known_ouis.get(prefix, "Inconnu")
'''
write_file(os.path.join(BASE_DIR, 'serveur', 'services', 'service_arp.py'), arp_content)

# Refonte service_snmp.py
snmp_content = '''import json
import os
import asyncio
from serveur.services.service_arp import ping_host

async def tester_connexion_snmp(ip: str, version: str, community: str = "public", **v3_kwargs):
    if version == "v3":
        return {"succes": False, "message": "SNMPv3 n'est pas supporté. (HTTP 501)", "status_code": 501}
    
    # Mesure réelle de latence
    en_ligne, latence = ping_host(ip, timeout_ms=1000)
    if not en_ligne:
        return {"succes": False, "message": f"Équipement {ip} injoignable par ping."}

    try:
        return await _snmp_get_v2c(ip, community, latence)
    except Exception as e:
        return {"succes": False, "message": f"Erreur SNMP: {str(e)}"}

async def _snmp_get_v2c(ip: str, community: str, latence: float):
    from pysnmp.hlapi.v1arch.asyncio import SnmpDispatcher, CommunityData, UdpTransportTarget, ObjectType, ObjectIdentity, get_cmd
    with SnmpDispatcher() as dispatcher:
        errorIndication, errorStatus, errorIndex, varBinds = await get_cmd(
            dispatcher,
            CommunityData(community, mpModel=1),
            await UdpTransportTarget.create((ip, 161), timeout=2.0, retries=1),
            ObjectType(ObjectIdentity('1.3.6.1.2.1.1.5.0')),
            ObjectType(ObjectIdentity('1.3.6.1.2.1.1.1.0')),
        )
        if errorIndication or errorStatus:
            return {"succes": False, "message": str(errorIndication or errorStatus)}
        
        sysName = str(varBinds[0][1]) if len(varBinds) > 0 else "Inconnu"
        sysDescr = str(varBinds[1][1]) if len(varBinds) > 1 else "Inconnu"
        return {"succes": True, "ip": ip, "sysName": sysName, "sysDescr": sysDescr, "latence_ms": latence, "message": "Succès"}

async def rechercher_port_mac_snmp(ip: str, mac: str, version: str, community: str = "public"):
    if version == "v3": return {"succes": False, "message": "SNMPv3 non supporté"}
    try: return await _snmp_find_mac_v2c(ip, mac, community)
    except Exception as e: return {"succes": False, "message": f"Erreur SNMP MAC: {str(e)}"}

async def _snmp_find_mac_v2c(ip: str, mac: str, community: str):
    from pysnmp.hlapi.v1arch.asyncio import SnmpDispatcher, CommunityData, UdpTransportTarget, ObjectType, ObjectIdentity, get_cmd
    if not mac or mac == "N/A": return {"succes": False, "message": "MAC invalide"}
    
    try: mac_parts = [str(int(p, 16)) for p in mac.replace("-", ":").split(":")]
    except ValueError: return {"succes": False, "message": "Format MAC invalide"}
    
    oid_str = "1.3.6.1.2.1.17.4.3.1.2." + ".".join(mac_parts)
    with SnmpDispatcher() as dispatcher:
        errInd, errStat, errIdx, vBinds = await get_cmd(
            dispatcher, CommunityData(community, mpModel=1),
            await UdpTransportTarget.create((ip, 161), timeout=2.0, retries=1),
            ObjectType(ObjectIdentity(oid_str)),
        )
        if errInd or errStat: return {"succes": False, "message": "Requête OID échouée"}
        if vBinds:
            valeur = str(vBinds[0][1])
            if "No Such" not in valeur:
                # 2e requête (dot1dBasePortIfIndex)
                oid_ifindex = f"1.3.6.1.2.1.17.1.4.1.2.{valeur}"
                errI2, errS2, errId2, vBinds2 = await get_cmd(
                    dispatcher, CommunityData(community, mpModel=1),
                    await UdpTransportTarget.create((ip, 161), timeout=1.0, retries=1),
                    ObjectType(ObjectIdentity(oid_ifindex))
                )
                ifindex = str(vBinds2[0][1]) if (not errI2 and vBinds2 and "No Such" not in str(vBinds2[0][1])) else valeur
                
                # 3e requête (ifName)
                oid_ifname = f"1.3.6.1.2.1.31.1.1.1.1.{ifindex}"
                errI3, errS3, errId3, vBinds3 = await get_cmd(
                    dispatcher, CommunityData(community, mpModel=1),
                    await UdpTransportTarget.create((ip, 161), timeout=1.0, retries=1),
                    ObjectType(ObjectIdentity(oid_ifname))
                )
                ifname = str(vBinds3[0][1]) if (not errI3 and vBinds3 and "No Such" not in str(vBinds3[0][1])) else f"ifIndex-{ifindex}"
                
                return {"succes": True, "port": ifname}
        return {"succes": False, "message": "MAC non trouvée dans la table"}

async def obtenir_voisin_lldp(ip: str, port_name: str, community: str):
    # Implémentation réelle simplifiée LLDP (1.0.8802.1.1.2.1.4.1.1)
    # Pour l'instant on retourne None si on ne trouve rien, on n'invente rien.
    return None

async def tracer_chemin_reseau(ip_depart: str, mac: str, version: str, community: str):
    chemin = []
    ip_actuelle = ip_depart
    for saut in range(5):
        res_snmp = await tester_connexion_snmp(ip_actuelle, version, community)
        nom_switch = res_snmp.get("sysName", ip_actuelle)
        res_port = await rechercher_port_mac_snmp(ip_actuelle, mac, version, community)
        
        if not res_port.get("succes"):
            chemin.append({"type": "SWITCH", "nom": nom_switch, "ip": ip_actuelle, "port_sortie": "N/D", "message": "Trace perdue"})
            return {"succes": False, "chemin": chemin, "dernier_switch_ip": ip_actuelle, "dernier_switch_nom": nom_switch}
            
        port_trouve = res_port.get("port")
        chemin.append({"type": "SWITCH", "nom": nom_switch, "ip": ip_actuelle, "port_entree": "Uplink", "port_sortie": port_trouve})
        
        prochain_switch_ip = await obtenir_voisin_lldp(ip_actuelle, port_trouve, community)
        if prochain_switch_ip: ip_actuelle = prochain_switch_ip
        else: return {"succes": True, "chemin": chemin, "dernier_switch_ip": ip_actuelle, "dernier_switch_nom": nom_switch, "port_acces_final": port_trouve}
    return {"succes": True, "chemin": chemin, "port_acces_final": "N/D"}
'''
write_file(os.path.join(BASE_DIR, 'serveur', 'services', 'service_snmp.py'), snmp_content)

print("Module 2 refactored")
