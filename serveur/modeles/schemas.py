from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class EquipementTopologie(BaseModel):
    id: str
    label: str
    type: str  # 'router', 'switch_core', 'switch_access', 'endpoint'
    ip: str
    status: str = "up"

class LienTopologie(BaseModel):
    id: str
    source: str
    target: str
    status: str = "active"

class TopologieReseau(BaseModel):
    noeuds: List[Dict[str, Any]]
    liaisons: List[Dict[str, Any]]
class MetriquesDashboard(BaseModel):
    total_equipements: int
    equipements_hors_ligne: int
    ports_actifs: int
    alertes_securite: int

class SwitchRattachement(BaseModel):
    nom: str
    ip: str
    port_acces: str
    vlan: str
    vitesse_port: str

class NoeudTrajectoire(BaseModel):
    type: str
    nom: str
    ip: Optional[str] = None
    port_entree: Optional[str] = None
    port_sortie: Optional[str] = None

class ResultatTracage(BaseModel):
    equipement: str
    ip: str
    mac: str
    statut: str
    latence_ms: float
    switch_rattachement: Optional[SwitchRattachement] = None
    emplacement_physique: str
    trajectoire_chemin: List[NoeudTrajectoire] = []

class RequeteIsolation(BaseModel):
    ip_equipement: str
    raison: str
    mot_de_passe_admin: str

class ReponseIsolation(BaseModel):
    statut: str
    message: str
    horodatage: str
