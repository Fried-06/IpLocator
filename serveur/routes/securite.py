from fastapi import APIRouter, HTTPException
from datetime import datetime
from serveur.modeles.schemas import RequeteIsolation, ReponseIsolation
from serveur.services.service_ssh import shutdown_port, no_shutdown_port

router = APIRouter()

@router.post("/isoler", response_model=ReponseIsolation)
async def isoler_equipement(requete: RequeteIsolation):
    """
    Simule la désactivation administrative d'un port (shutdown) pour isoler un équipement.
    """
    if requete.mot_de_passe_admin != "admin123":
        raise HTTPException(status_code=403, detail="Mot de passe administrateur incorrect.")
    
    # Mock lookup de l'IP pour trouver le switch et le port
    switch_ip = "10.20.0.12"
    switch_nom = "SW-BLOC-TECH-01"
    port = "Gi1/0/14"
    
    # Exécution du mock SSH
    succes = shutdown_port(switch_ip, port)
    
    if succes:
        return ReponseIsolation(
            statut="SUCCES",
            message=f"Le port {port} du switch {switch_nom} a été désactivé avec succès.",
            horodatage=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
    else:
        raise HTTPException(status_code=500, detail="Échec de l'exécution SSH sur le switch.")

@router.post("/restaurer", response_model=ReponseIsolation)
async def restaurer_equipement(requete: RequeteIsolation):
    """
    Simule la réactivation d'un port (no shutdown).
    """
    if requete.mot_de_passe_admin != "admin123":
        raise HTTPException(status_code=403, detail="Mot de passe administrateur incorrect.")
    
    # Mock lookup
    switch_ip = "10.20.0.12"
    switch_nom = "SW-BLOC-TECH-01"
    port = "Gi1/0/14"
    
    # Exécution du mock SSH
    succes = no_shutdown_port(switch_ip, port)
    
    if succes:
        return ReponseIsolation(
            statut="SUCCES",
            message=f"Le port {port} du switch {switch_nom} a été réactivé avec succès.",
            horodatage=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
    else:
        raise HTTPException(status_code=500, detail="Échec de l'exécution SSH sur le switch.")
