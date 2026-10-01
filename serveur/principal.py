import os
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from serveur.routes import decouverte, tracage, securite, auth, parametres, supervision
from serveur.services.service_supervision import sonder_toutes_les_machines

app = FastAPI(title="ASECNA IpLocator API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def au_demarrage():
    """Au démarrage de l'application, sonde automatiquement toutes les machines L3 & L7."""
    asyncio.create_task(sonder_toutes_les_machines())

app.include_router(decouverte.router, prefix="/api/v1/decouverte", tags=["Découverte"])
app.include_router(tracage.router, prefix="/api/v1/tracage", tags=["Traçage"])
app.include_router(securite.router, prefix="/api/v1/securite", tags=["Sécurité"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentification"])
app.include_router(parametres.router, prefix="/api/v1/parametres", tags=["Paramètres"])
app.include_router(supervision.router, prefix="/api/v1/supervision", tags=["Supervision"])
