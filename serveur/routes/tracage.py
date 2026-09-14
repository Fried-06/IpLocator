import re
import socket
from fastapi import APIRouter
from serveur.modeles.schemas import ResultatTracage, SwitchRattachement, NoeudTrajectoire
from serveur.routes.parametres import charger_parametres
from serveur.services.service_arp import (
    ping_host,
    resolve_ip_to_mac,
    resolve_name_to_ip,
    resolve_ip_to_hostname,
    get_mac_vendor
)
from serveur.services.service_snmp import tester_connexion_snmp

router = APIRouter()

@router.get("/recherche", response_model=ResultatTracage)
async def rechercher_equipement(cible: str):
    """
    Recherche un équipement et génère un rapport complet incluant le chemin réseau.
    Gère le mode MOCK (données pédagogiques ASECNA) et le mode REAL_NETWORK (vrai réseau Wi-Fi/Ethernet).
    """
    cible = cible.strip()
    parametres = charger_parametres()
    mode = parametres.get("mode", "MOCK")

    # Si la cible est un nom d'hôte, on tente de trouver son IP
    ip_cible = cible
    nom_cible = cible
    
    # Vérification si c'est déjà une IP
    est_ip = bool(re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", cible))
    
    if not est_ip:
        ip_resolue = resolve_name_to_ip(cible)
        if ip_resolue:
            ip_cible = ip_resolue
        else:
            ip_cible = cible

    # ═════════════════════════════════════════════════════════════════
    # MODE 1 : MOCK / SIMULATION (Pour présentations ou hors ligne)
    # ═════════════════════════════════════════════════════════════════
    if mode == "MOCK":
        cible_lower = cible.lower()
        if "amhs" in cible_lower or ip_cible in ["10.20.1.15", "10.20.0.1"]:
            return ResultatTracage(
                equipement="Serveur AMHS (Aéronautique)",
                ip="10.20.1.15",
                mac="00:1A:2B:3C:4D:5E",
                statut="EN_LIGNE",
                latence_ms=1.8,
                switch_rattachement=SwitchRattachement(
                    nom="SW-BLOC-TECH-01",
                    ip="10.20.0.12",
                    port_acces="GigabitEthernet 1/0/14",
                    vlan="VLAN 10 (AFTN/AMHS)",
                    vitesse_port="1 Gbps / Full Duplex"
                ),
                emplacement_physique="Bloc Technique - Salle Serveurs BGD - Baie 03 / Slot 4",
                trajectoire_chemin=[
                    NoeudTrajectoire(type="POSTE_DEPART", nom="Poste Opérateur NOC", port_sortie="Eth0"),
                    NoeudTrajectoire(type="SWITCH_CORE", nom="SW-CORE-ASECNA", ip="10.20.0.1", port_entree="Gi0/1", port_sortie="Gi0/24"),
                    NoeudTrajectoire(type="SWITCH_ACCES", nom="SW-BLOC-TECH-01", ip="10.20.0.12", port_entree="Gi0/24", port_sortie="Gi1/0/14"),
                    NoeudTrajectoire(type="EQUIPEMENT_CIBLE", nom="Serveur AMHS", ip="10.20.1.15", port_entree="Eth0")
                ]
            )
        elif "smt" in cible_lower or ip_cible == "10.20.1.20":
            return ResultatTracage(
                equipement="Serveur SMT (Météo)",
                ip="10.20.1.20",
                mac="AA:BB:CC:DD:EE:FF",
                statut="EN_LIGNE",
                latence_ms=2.1,
                switch_rattachement=SwitchRattachement(
                    nom="SW-BLOC-TECH-02",
                    ip="10.20.0.13",
                    port_acces="GigabitEthernet 1/0/2",
                    vlan="VLAN 20 (METEO)",
                    vitesse_port="1 Gbps / Full Duplex"
                ),
                emplacement_physique="Bloc Technique - Salle Serveurs BGD - Baie 02",
                trajectoire_chemin=[
                    NoeudTrajectoire(type="POSTE_DEPART", nom="Poste Opérateur NOC", port_sortie="Eth0"),
                    NoeudTrajectoire(type="SWITCH_CORE", nom="SW-CORE-ASECNA", ip="10.20.0.1", port_entree="Gi0/1", port_sortie="Gi0/20"),
                    NoeudTrajectoire(type="SWITCH_ACCES", nom="SW-BLOC-TECH-02", ip="10.20.0.13", port_entree="Gi0/20", port_sortie="Gi1/0/2"),
                    NoeudTrajectoire(type="EQUIPEMENT_CIBLE", nom="Serveur SMT", ip="10.20.1.20", port_entree="Eth0")
                ]
            )
        else:
            return ResultatTracage(
                equipement="Équipement Simulation Non Trouvé",
                ip=ip_cible,
                mac="N/A",
                statut="HORS_LIGNE",
                latence_ms=0.0,
                switch_rattachement=None,
                emplacement_physique="Non localisé dans la maquette MOCK",
                trajectoire_chemin=[]
            )

    # ═════════════════════════════════════════════════════════════════
    # MODE 2 : REAL_NETWORK (Vrai Réseau Physique / Wi-Fi / Ethernet)
    # ═════════════════════════════════════════════════════════════════
    # 1. Test de connectivité Réel (Ping)
    en_ligne, latence = ping_host(ip_cible, timeout_ms=1200)

    # 2. Résolution ARP réelle
    mac_trouvee = resolve_ip_to_mac(ip_cible) or "N/A"
    vendor = get_mac_vendor(mac_trouvee)
    
    # 3. Nom d'hôte réel
    nom_hote = resolve_ip_to_hostname(ip_cible) if en_ligne else cible
    if nom_hote == f"Hôte-{ip_cible}" and vendor != "Générique / Inconnu":
        nom_hote = f"Équipement {vendor}"

    # Récupération des paramètres réseau configurés
    core_switch_ip = parametres.get("core_switch_ip", "192.168.1.1")
    snmp_community = parametres.get("snmp_community", "public")
    snmp_version = parametres.get("snmp_version", "v2c")

    # 4. Test si le Switch/Routeur configuré répond en SNMP
    info_switch = None
    statut_snmp = tester_connexion_snmp(core_switch_ip, version=snmp_version, community=snmp_community)
    
    nom_switch_detecte = info_switch.get("sysName") if (info_switch and info_switch.get("succes")) else f"Passerelle-{core_switch_ip}"
    
    # 5. Déduction du chemin et du port (Wi-Fi ou Switch Ethernet)
    # Détermination du type de connexion
    is_wifi = False
    if "10.28." in ip_cible or "192.168." in ip_cible or "172." in ip_cible:
        # Si on est sur le même sous-réseau sans accès SNMP switch complet
        is_wifi = not statut_snmp.get("succes")

    port_libelle = "Liaison Sans-Fil (Borne AP / Wi-Fi)" if is_wifi else "Port Dynamique (Ethernet)"
    vlan_libelle = "VLAN Local (Défaut)" if is_wifi else "VLAN Réseau"
    type_connexion = "Wi-Fi (Sans-fil)" if is_wifi else "Filaire RJ45"
    emplacement = "Segment Réseau Sans-Fil (Zone Wi-Fi)" if is_wifi else f"Raccordé au Switch {nom_switch_detecte}"

    if en_ligne or mac_trouvee != "N/A":
        statut_str = "EN_LIGNE" if en_ligne else "HORS_LIGNE"
        
        switch_rattachement = SwitchRattachement(
            nom=nom_switch_detecte,
            ip=core_switch_ip,
            port_acces=port_libelle,
            vlan=vlan_libelle,
            vitesse_port="Auto-Negotiation (Actif)" if en_ligne else "Non connecté"
        )

        trajectoire = [
            NoeudTrajectoire(type="POSTE_DEPART", nom="Poste Opérateur (Local)", port_sortie="Interface Réseau"),
            NoeudTrajectoire(type="SWITCH_CORE", nom=nom_switch_detecte, ip=core_switch_ip, port_entree="Uplink", port_sortie="LAN"),
            NoeudTrajectoire(type="SWITCH_ACCES", nom=f"Point d'Accès / {type_connexion}", ip=core_switch_ip, port_entree="LAN", port_sortie=port_libelle),
            NoeudTrajectoire(type="EQUIPEMENT_CIBLE", nom=f"{nom_hote} ({vendor})", ip=ip_cible, port_entree="Interface")
        ]

        return ResultatTracage(
            equipement=f"{nom_hote} ({vendor})",
            ip=ip_cible,
            mac=mac_trouvee,
            statut=statut_str,
            latence_ms=latence,
            switch_rattachement=switch_rattachement,
            emplacement_physique=emplacement,
            trajectoire_chemin=trajectoire
        )
    else:
        # Équipement introuvable sur le réseau réel
        return ResultatTracage(
            equipement=f"Équipement {cible}",
            ip=ip_cible,
            mac="N/A",
            statut="HORS_LIGNE",
            latence_ms=0.0,
            switch_rattachement=None,
            emplacement_physique="Équipement introuvable ou injoignable sur le réseau actuel",
            trajectoire_chemin=[]
        )
