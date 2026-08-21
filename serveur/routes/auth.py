from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()

# ──────────────────────────────────────────────
# Schémas
# ──────────────────────────────────────────────
class RequeteLogin(BaseModel):
    identifiant: str
    mot_de_passe: str

class ReponseLogin(BaseModel):
    succes: bool
    role: str          # "ADMIN" | "OPERATEUR"
    nom: str
    message: str

# ──────────────────────────────────────────────
# Base d'utilisateurs mock
# ──────────────────────────────────────────────
UTILISATEURS = {
    "admin": {
        "mot_de_passe": "admin123",
        "role": "ADMIN",
        "nom": "Ousmane Diallo",
    },
    "operator": {
        "mot_de_passe": "user123",
        "role": "OPERATEUR",
        "nom": "Koffi Mensah",
    },
}

@router.post("/login", response_model=ReponseLogin)
async def login(requete: RequeteLogin):
    """
    Authentification RBAC simulée.
    Retourne le rôle et le nom de l'utilisateur si les identifiants sont corrects.
    """
    utilisateur = UTILISATEURS.get(requete.identifiant.lower())

    if not utilisateur or utilisateur["mot_de_passe"] != requete.mot_de_passe:
        raise HTTPException(
            status_code=401,
            detail="Identifiant ou mot de passe incorrect."
        )

    return ReponseLogin(
        succes=True,
        role=utilisateur["role"],
        nom=utilisateur["nom"],
        message=f"Bienvenue, {utilisateur['nom']} — Session ouverte le {datetime.now().strftime('%d/%m/%Y à %H:%M')}."
    )
