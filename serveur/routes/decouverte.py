from fastapi import APIRouter
from serveur.modeles.schemas import TopologieReseau, MetriquesDashboard
from serveur.services.service_snmp import get_topology_mock, get_metrics_mock

router = APIRouter()

@router.get("/topologie")
async def obtenir_topologie():
    """
    Retourne la topologie réseau dynamique pour l'affichage du graphe vis-network.
    """
    return get_topology_mock()

@router.get("/metriques", response_model=MetriquesDashboard)
async def obtenir_metriques():
    """
    Retourne les métriques de base pour le tableau de bord NOC.
    """
    data = get_metrics_mock()
    return MetriquesDashboard(**data)
