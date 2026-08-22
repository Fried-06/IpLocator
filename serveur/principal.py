from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from serveur.routes import decouverte, tracage, securite, auth, parametres

app = FastAPI(
    title="ASECNA IpLocator API",
    description="API pour le traçage topologique et la sécurité réseau.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(decouverte.router, prefix="/api/v1/decouverte", tags=["Découverte"])
app.include_router(tracage.router, prefix="/api/v1/tracage", tags=["Traçage"])
app.include_router(securite.router, prefix="/api/v1/securite", tags=["Sécurité"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentification"])
app.include_router(parametres.router, prefix="/api/v1/parametres", tags=["Paramètres"])

@app.get("/")
def read_root():
    return {"message": "Bienvenue sur l'API ASECNA IpLocator"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("serveur.principal:app", host="0.0.0.0", port=8000, reload=True)