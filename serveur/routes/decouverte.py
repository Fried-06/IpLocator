from fastapi import APIRouter
from serveur.modeles.schemas import TopologieReseau, MetriquesDashboard
from serveur.services.service_snmp import get_topology_mock, get_metrics_mock

router = APIRouter()

@router.get("/topologie")
async def obtenir_topologie():
    """
    Retourne la topologie réseau dynamique pour l'affichage du graphe vis-network.
    """
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

@router.get("/metriques", response_model=MetriquesDashboard)
async def obtenir_metriques():
    """
    Retourne les métriques de base pour le tableau de bord NOC.
    """
    data = get_metrics_mock()
    return MetriquesDashboard(**data)
