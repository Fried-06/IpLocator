from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from serveur.routes import decouverte, tracage, securite, auth

app = FastAPI(
    title="ASECNA IpLocator API",
    description="API pour le traçage topologique et la sécurité réseau.",
    version="1.0.0"
)

# Configuration CORS pour autoriser l'interface Frontend à communiquer avec l'API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Dans un environnement de prod strict, spécifier l'origine exacte
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclusion des routeurs
app.include_router(decouverte.router, prefix="/api/v1/decouverte", tags=["Découverte"])
app.include_router(tracage.router, prefix="/api/v1/tracage", tags=["Traçage"])
app.include_router(securite.router, prefix="/api/v1/securite", tags=["Sécurité"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentification"])

@app.get("/")
def read_root():
    return {"message": "Bienvenue sur l'API ASECNA IpLocator"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("serveur.principal:app", host="0.0.0.0", port=8000, reload=True)
