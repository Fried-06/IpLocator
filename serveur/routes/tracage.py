from fastapi import APIRouter
from serveur.modeles.schemas import ResultatTracage, SwitchRattachement, NoeudTrajectoire

router = APIRouter()

@router.get("/recherche", response_model=ResultatTracage)
async def rechercher_equipement(cible: str):
    """
    Recherche un équipement et génère un rapport complet incluant le chemin réseau.
    Données mockées pour répondre à la demande ASECNA (AMHS ou autre).
    """
    # Mock des données tel que demandé dans l'étape 2
    cible_lower = cible.lower()
    
    # Si on cherche AMHS ou une IP spécifique
    if "amhs" in cible_lower or cible == "10.20.1.15":
        return ResultatTracage(
            equipement="Serveur AMHS",
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
    elif "smt" in cible_lower:
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
    
    # Par défaut (Non trouvé ou générique)
    return ResultatTracage(
        equipement="Équipement Inconnu",
        ip=cible if "." in cible else "N/A",
        mac="N/A",
        statut="HORS_LIGNE",
        latence_ms=0.0,
        switch_rattachement=None,
        emplacement_physique="Non localisé",
        trajectoire_chemin=[]
    )
