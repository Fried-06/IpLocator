import re
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from serveur.services.service_arp import (
    resolve_name_to_ip, resolve_ip_to_mac,
    resolve_ip_to_hostname, get_mac_vendor, ping_host
)
from serveur.services.service_snmp import tracer_chemin_reseau, obtenir_mac_depuis_switch_arp
from serveur.routes.parametres import charger_parametres as get_current_settings
from serveur.routes.auth import require_admin

logger = logging.getLogger("routes.tracage")
router = APIRouter()

class RequeteTracage(BaseModel):
    cible: str

@router.get("/recherche")
async def executer_tracage(cible: str, user=Depends(require_admin)):
    cible = cible.strip()
    is_ip = re.match(r"^(\d{1,3}\.){3}\d{1,3}$", cible)
    ip_address = cible if is_ip else resolve_name_to_ip(cible)
    
    if not ip_address:
        raise HTTPException(status_code=404, detail="Cible introuvable (impossible de résoudre l'adresse IP)")
        
    en_ligne, latence = ping_host(ip_address, timeout_ms=800)
    mac = resolve_ip_to_mac(ip_address)

    settings = get_current_settings()
    ip_depart = settings.get("core_switch_ip")
    comm = settings.get("snmp_community", "public")
    if comm == "********":
        comm = "public"

    gateway_ip = settings.get("gateway_ip")

    # Si la MAC n'est pas dans la table ARP locale de la machine hôte :
    # 1. Tenter d'interroger la table ARP de la passerelle (pour joindre d'autres sous-réseaux)
    if not mac and gateway_ip:
        mac = await obtenir_mac_depuis_switch_arp(gateway_ip, ip_address, comm)

    # 2. Tenter d'interroger la table ARP du switch cœur via SNMP
    if not mac and ip_depart:
        mac = await obtenir_mac_depuis_switch_arp(ip_depart, ip_address, comm)
    
    if not mac:
        raise HTTPException(
            status_code=404, 
            detail="Cible introuvable dans la table ARP locale et switch (équipement éteint ou inaccessible)"
        )

    hostname = resolve_ip_to_hostname(ip_address) or "--"
    constructeur = get_mac_vendor(mac)
    if hostname != "--":
        nom_affiche = hostname
    elif constructeur != "Inconnu":
        nom_affiche = f"{constructeur} ({ip_address})"
    else:
        nom_affiche = f"Hôte-{ip_address}"

    switch_info = None
    trajectoire = []

    if ip_depart:
        try:
            res_trace = await tracer_chemin_reseau(
                ip_depart, 
                mac, 
                settings.get("snmp_version", "v2c"), 
                comm
            )
            if res_trace.get("succes") and res_trace.get("port_acces_final"):
                switch_info = {
                    "nom": res_trace.get("dernier_switch_nom", ip_depart),
                    "ip": res_trace.get("dernier_switch_ip", ip_depart),
                    "port_acces": res_trace.get("port_acces_final", "--"),
                    "vitesse_port": res_trace.get("vitesse", "--"),
                    "vlan": res_trace.get("vlan", "--")
                }
                trajectoire = res_trace.get("chemin", [])
                
                # Enregistrer immédiatement l'équipement dans la cartographie réseau
                from serveur.routes.decouverte import enregistrer_noeud_topologie
                enregistrer_noeud_topologie(
                    ip=ip_address,
                    mac=mac,
                    nom=nom_affiche,
                    switch_ip=switch_info["ip"],
                    switch_nom=switch_info["nom"],
                    port=switch_info["port_acces"],
                    vlan=switch_info["vlan"],
                    vitesse=switch_info["vitesse_port"],
                    statut="EN_LIGNE" if en_ligne else "HORS_LIGNE"
                )
            else:
                logger.warning(f"Trace SNMP échouée pour MAC {mac} sur {ip_depart}: {res_trace.get('message')}")
        except Exception as e:
            logger.exception(f"Erreur inattendue durant le traçage SNMP: {e}")

    return {
        "succes": True,
        "equipement": nom_affiche,
        "ip": ip_address,
        "mac": mac,
        "hostname": hostname,
        "constructeur": constructeur,
        "latence_ms": latence if en_ligne else None,
        "statut": "EN_LIGNE" if (en_ligne or mac) else "HORS_LIGNE",
        "switch_rattachement": switch_info,
        "emplacement_physique": "--",
        "trajectoire_chemin": trajectoire
    }
