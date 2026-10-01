import asyncio
import logging
from typing import Optional, Dict, Any, List
from serveur.services.service_arp import ping_host
from pysnmp.hlapi.v1arch.asyncio import (
    SnmpDispatcher, CommunityData, UdpTransportTarget,
    ObjectType, ObjectIdentity, get_cmd, next_cmd
)

logger = logging.getLogger("service_snmp")

# Cache temporaire des VLANs découverts par switch pour accélérer les requêtes
_VLAN_CACHE: Dict[str, List[int]] = {}

async def tester_connexion_snmp(ip: str, version: str, community: str = "public", **v3_kwargs) -> Dict[str, Any]:
    """Teste la joignabilité ping et SNMP d'un équipement."""
    if version == "v3":
        return {"succes": False, "message": "SNMPv3 n'est pas encore supporté (utilisez SNMPv2c).", "status_code": 501}
    
    en_ligne, latence = ping_host(ip, timeout_ms=1000)
    if not en_ligne:
        return {"succes": False, "message": f"Équipement {ip} injoignable par ping."}

    try:
        return await _snmp_get_v2c(ip, community, latence)
    except Exception as e:
        logger.exception("Erreur SNMP lors du test de connexion:")
        return {"succes": False, "message": f"Erreur SNMP: {str(e)}"}

async def _snmp_get_v2c(ip: str, community: str, latence: float) -> Dict[str, Any]:
    with SnmpDispatcher() as dispatcher:
        errInd, errStat, errIdx, varBinds = await get_cmd(
            dispatcher,
            CommunityData(community, mpModel=1),
            await UdpTransportTarget.create((ip, 161), timeout=2.0, retries=1),
            ObjectType(ObjectIdentity('1.3.6.1.2.1.1.5.0')),  # sysName
            ObjectType(ObjectIdentity('1.3.6.1.2.1.1.1.0')),  # sysDescr
        )
        if errInd or errStat:
            return {"succes": False, "message": str(errInd or errStat)}
        
        sysName = str(varBinds[0][1]) if len(varBinds) > 0 and "No Such" not in str(varBinds[0][1]) else ip
        sysDescr = str(varBinds[1][1]) if len(varBinds) > 1 and "No Such" not in str(varBinds[1][1]) else "Inconnu"
        return {"succes": True, "ip": ip, "sysName": sysName, "sysDescr": sysDescr, "latence_ms": latence, "message": "Connexion SNMP réussie !"}

async def decouvrir_vlans_switch(ip: str, community: str = "public") -> List[int]:
    """Découvre dynamiquement les VLANs actifs d'un switch (Cisco VTP ou standard)."""
    if ip in _VLAN_CACHE:
        return _VLAN_CACHE[ip]

    vlans = {1}
    try:
        with SnmpDispatcher() as dispatcher:
            # 1. Tenter la table Cisco VTP (1.3.6.1.4.1.9.9.46.1.3.1.1.2.1 - vtpVlanState)
            target = await UdpTransportTarget.create((ip, 161), timeout=1.5, retries=1)
            var_bind = ObjectType(ObjectIdentity('1.3.6.1.4.1.9.9.46.1.3.1.1.2.1'))
            for _ in range(60):
                errInd, errStat, errIdx, varBinds = await next_cmd(
                    dispatcher, CommunityData(community, mpModel=1), target, var_bind
                )
                if errInd or errStat or not varBinds:
                    break
                var_bind = varBinds[0]
                oid_str = str(var_bind[0])
                if not oid_str.startswith('1.3.6.1.4.1.9.9.46.1.3.1.1.2.1.'):
                    break
                try:
                    vlan_id = int(oid_str.split('.')[-1])
                    if 0 < vlan_id < 4095:
                        vlans.add(vlan_id)
                except ValueError:
                    pass
    except Exception as e:
        logger.debug(f"Erreur découverte VLANs: {e}")

    # Compléter avec quelques VLANs standards au cas où
    for v in [1, 2, 10, 20, 30, 40, 50, 99, 100]:
        vlans.add(v)

    res = sorted(list(vlans))
    _VLAN_CACHE[ip] = res
    return res

async def obtenir_mac_depuis_switch_arp(ip_switch: str, ip_cible: str, community: str = "public") -> Optional[str]:
    """Interroge la table ARP du switch core via SNMP (ipNetToMediaPhysAddress) pour trouver la MAC de l'IP cible."""
    try:
        with SnmpDispatcher() as dispatcher:
            target = await UdpTransportTarget.create((ip_switch, 161), timeout=2.0, retries=1)
            var = ObjectType(ObjectIdentity('1.3.6.1.2.1.4.22.1.2'))
            for _ in range(200):
                errInd, errStat, errIdx, varBinds = await next_cmd(
                    dispatcher, CommunityData(community, mpModel=1), target, var
                )
                if errInd or errStat or not varBinds:
                    break
                var = varBinds[0]
                oid_str = str(var[0])
                if not oid_str.startswith('1.3.6.1.2.1.4.22.1.2.'):
                    break
                parts = oid_str.split('.')
                ip_found = '.'.join(parts[-4:])
                if ip_found == ip_cible:
                    raw_mac = bytes(var[1])
                    return ':'.join(f'{b:02x}' for b in raw_mac).upper()
    except Exception as e:
        logger.debug(f"Erreur recherche ARP switch: {e}")
    return None

async def rechercher_port_mac_snmp(ip: str, mac: str, version: str, community: str = "public") -> Dict[str, Any]:
    """Recherche le port physique correspondant à une adresse MAC sur le switch."""
    if version == "v3":
        return {"succes": False, "message": "SNMPv3 non supporté"}
    try:
        return await _snmp_find_mac_cisco_or_standard(ip, mac, community)
    except Exception as e:
        logger.exception("Erreur lors de la recherche du port MAC:")
        return {"succes": False, "message": f"Erreur SNMP MAC: {str(e)}"}

async def _snmp_find_mac_cisco_or_standard(ip: str, mac: str, community: str) -> Dict[str, Any]:
    if not mac or mac == "N/A":
        return {"succes": False, "message": "MAC invalide"}

    try:
        mac_parts = [str(int(p, 16)) for p in mac.replace("-", ":").split(":")]
    except ValueError:
        return {"succes": False, "message": "Format MAC invalide"}

    oid_mac_suffix = ".".join(mac_parts)
    oid_dot1d_tp_fdb_port = f"1.3.6.1.2.1.17.4.3.1.2.{oid_mac_suffix}"

    with SnmpDispatcher() as dispatcher:
        target = await UdpTransportTarget.create((ip, 161), timeout=1.5, retries=1)

        # 1. Essai Standard Bridge-MIB (non-Cisco ou VLAN par défaut)
        try:
            errInd, errStat, errIdx, vBinds = await get_cmd(
                dispatcher, CommunityData(community, mpModel=1), target,
                ObjectType(ObjectIdentity(oid_dot1d_tp_fdb_port))
            )
            if not errInd and not errStat and vBinds:
                val = str(vBinds[0][1]).strip()
                if val.isdigit() and int(val) > 0:
                    return await _resoudre_details_port(dispatcher, target, ip, community, community, val, vlan_id=1)
        except Exception:
            pass

        # 2. Essai Cisco Community String Indexing (community@vlan) sur tous les VLANs
        vlans = await decouvrir_vlans_switch(ip, community)
        for vlan in vlans:
            comm_vlan = f"{community}@{vlan}"
            try:
                errInd, errStat, errIdx, vBinds = await get_cmd(
                    dispatcher, CommunityData(comm_vlan, mpModel=1), target,
                    ObjectType(ObjectIdentity(oid_dot1d_tp_fdb_port))
                )
                if not errInd and not errStat and vBinds:
                    val = str(vBinds[0][1]).strip()
                    if val.isdigit() and int(val) > 0:
                        return await _resoudre_details_port(
                            dispatcher, target, ip, community, comm_vlan, val, vlan_id=vlan
                        )
            except Exception:
                continue

    return {"succes": False, "message": "MAC non trouvée dans la table de commutation"}

async def _resoudre_details_port(dispatcher, target, ip: str, community_base: str, comm_query: str, bridge_port: str, vlan_id: int) -> Dict[str, Any]:
    """Résout le port bridge en ifIndex puis en ifName et vitesse."""
    # Requête dot1dBasePortIfIndex
    oid_ifindex = f"1.3.6.1.2.1.17.1.4.1.2.{bridge_port}"
    ifindex = bridge_port
    try:
        errI, _, _, vB = await get_cmd(
            dispatcher, CommunityData(comm_query, mpModel=1), target,
            ObjectType(ObjectIdentity(oid_ifindex))
        )
        if not errI and vB and "No Such" not in str(vB[0][1]):
            val_if = str(vB[0][1]).strip()
            if val_if.isdigit():
                ifindex = val_if
    except Exception:
        pass

    # Requête ifName, ifDescr, ifHighSpeed
    ifname = f"Port-{bridge_port}"
    vitesse = "--"
    try:
        errI, _, _, vB = await get_cmd(
            dispatcher, CommunityData(community_base, mpModel=1), target,
            ObjectType(ObjectIdentity(f"1.3.6.1.2.1.31.1.1.1.1.{ifindex}")),  # ifName
            ObjectType(ObjectIdentity(f"1.3.6.1.2.1.2.2.1.2.{ifindex}")),      # ifDescr
            ObjectType(ObjectIdentity(f"1.3.6.1.2.1.31.1.1.1.15.{ifindex}"))  # ifHighSpeed (Mbps)
        )
        if not errI and vB:
            nom_candidat = str(vB[0][1]) if "No Such" not in str(vB[0][1]) else str(vB[1][1])
            if "No Such" not in nom_candidat:
                ifname = nom_candidat
            
            raw_speed = str(vB[2][1]) if len(vB) > 2 and "No Such" not in str(vB[2][1]) else ""
            if raw_speed.isdigit() and int(raw_speed) > 0:
                s_mbps = int(raw_speed)
                vitesse = f"{s_mbps // 1000} Gbps" if s_mbps >= 1000 else f"{s_mbps} Mbps"
    except Exception:
        pass

    return {
        "succes": True,
        "port": ifname,
        "ifindex": ifindex,
        "vlan": f"VLAN {vlan_id}",
        "vitesse": vitesse
    }

async def obtenir_voisin_lldp(ip: str, port_name: str, community: str) -> Optional[str]:
    """Découverte de switch voisin via LLDP / CDP."""
    # Possibilité future d'extension LLDP (1.0.8802.1.1.2.1.4.1.1) ou CDP (1.3.6.1.4.1.9.9.23.1.2.1.1)
    return None

async def tracer_chemin_reseau(ip_depart: str, mac: str, version: str, community: str) -> Dict[str, Any]:
    """Trace le chemin à travers les switchs jusqu'au port d'accès final."""
    chemin = []
    ip_actuelle = ip_depart
    dernier_port = "--"
    dernier_vlan = "--"
    derniere_vitesse = "--"

    for saut in range(5):
        res_snmp = await tester_connexion_snmp(ip_actuelle, version, community)
        nom_switch = res_snmp.get("sysName", ip_actuelle)
        res_port = await rechercher_port_mac_snmp(ip_actuelle, mac, version, community)

        if not res_port.get("succes"):
            chemin.append({
                "type": "SWITCH",
                "nom": nom_switch,
                "ip": ip_actuelle,
                "port_sortie": "N/D",
                "message": "Trace perdue ou MAC non trouvée sur ce switch"
            })
            return {
                "succes": False,
                "chemin": chemin,
                "dernier_switch_ip": ip_actuelle,
                "dernier_switch_nom": nom_switch,
                "message": res_port.get("message", "Port introuvable")
            }

        port_trouve = res_port.get("port")
        dernier_port = port_trouve
        dernier_vlan = res_port.get("vlan", "--")
        derniere_vitesse = res_port.get("vitesse", "--")

        est_premier = (saut == 0)
        chemin.append({
            "type": "SWITCH_CORE" if est_premier else "SWITCH_ACCES",
            "nom": nom_switch,
            "ip": ip_actuelle,
            "port_entree": "Uplink" if saut > 0 else "--",
            "port_sortie": port_trouve,
            "vlan": dernier_vlan,
            "vitesse": derniere_vitesse
        })

        prochain_switch_ip = await obtenir_voisin_lldp(ip_actuelle, port_trouve, community)
        if prochain_switch_ip and prochain_switch_ip != ip_actuelle:
            ip_actuelle = prochain_switch_ip
        else:
            # Ajouter le nœud final représentant l'équipement raccordé
            chemin.append({
                "type": "EQUIPEMENT_CIBLE",
                "nom": f"Hôte ({mac})",
                "ip": "--",
                "port_entree": port_trouve,
                "port_sortie": "--"
            })
            return {
                "succes": True,
                "chemin": chemin,
                "dernier_switch_ip": ip_actuelle,
                "dernier_switch_nom": nom_switch,
                "port_acces_final": port_trouve,
                "vlan": dernier_vlan,
                "vitesse": derniere_vitesse
            }

    return {
        "succes": True,
        "chemin": chemin,
        "port_acces_final": dernier_port,
        "vlan": dernier_vlan,
        "vitesse": derniere_vitesse
    }
