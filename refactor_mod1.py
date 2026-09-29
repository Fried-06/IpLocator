import os
import json

BASE_DIR = 'E:/projet mémoire/iplocator_light/IpLocator'

def write_file(filepath, content):
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

# configuration.py
write_file(os.path.join(BASE_DIR, 'serveur', 'configuration.py'), '''import os
SNMP_COMMUNITY = os.getenv("SNMP_COMMUNITY")
SNMP_VERSION = 2
SNMP_PORT = int(os.getenv("SNMP_PORT", 161))
SSH_USERNAME = os.getenv("SSH_USERNAME")
SSH_PASSWORD = os.getenv("SSH_PASSWORD")
SSH_PORT = int(os.getenv("SSH_PORT", 22))
JWT_SECRET = os.getenv("JWT_SECRET", "change-me-in-production")
''')

# principal.py
write_file(os.path.join(BASE_DIR, 'serveur', 'principal.py'), '''from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from serveur.routes import decouverte, tracage, securite, auth, parametres

app = FastAPI(title="ASECNA IpLocator API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_URL", "http://localhost:8000")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(decouverte.router, prefix="/api/v1/decouverte", tags=["Découverte"])
app.include_router(tracage.router, prefix="/api/v1/tracage", tags=["Traçage"])
app.include_router(securite.router, prefix="/api/v1/securite", tags=["Sécurité"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentification"])
app.include_router(parametres.router, prefix="/api/v1/parametres", tags=["Paramètres"])
'''.replace('os.getenv', 'import os\nos.getenv'))

# parametres.py
write_file(os.path.join(BASE_DIR, 'serveur', 'routes', 'parametres.py'), '''import json, os
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Literal
from serveur.routes.auth import require_admin
from serveur.services.service_snmp import tester_connexion_snmp

router = APIRouter()
CONFIG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config")
CONFIG_FILE = os.path.join(CONFIG_DIR, "settings.json")

def charger_parametres():
    if not os.path.exists(CONFIG_FILE): return {}
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except: return {}

def sauvegarder_parametres(data: dict):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

class SchemaParametres(BaseModel):
    core_switch_ip: Optional[str] = None
    core_switch_brand: Optional[str] = None
    snmp_version: Optional[str] = None
    snmp_community: Optional[str] = None
    ssh_username: Optional[str] = None
    ssh_password: Optional[str] = None

@router.get("")
async def obtenir_parametres(user=Depends(require_admin)):
    data = charger_parametres()
    if data.get("snmp_community"): data["snmp_community"] = "********"
    if data.get("ssh_password"): data["ssh_password"] = "********"
    return data

@router.post("")
async def enregistrer_parametres(params: SchemaParametres, user=Depends(require_admin)):
    sauvegarder_parametres(params.dict(exclude_unset=True))
    return {"succes": True}
''')

# auth.py
write_file(os.path.join(BASE_DIR, 'serveur', 'routes', 'auth.py'), '''from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import jwt, datetime, os, sqlite3
from passlib.context import CryptContext
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()
JWT_SECRET = os.getenv("JWT_SECRET", "super-secret-key")

def get_db():
    conn = sqlite3.connect("iplocator.db")
    conn.row_factory = sqlite3.Row
    conn.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT, role TEXT)")
    # Default admin from env
    admin_user = os.getenv("ADMIN_USER")
    admin_pass = os.getenv("ADMIN_PASS")
    if admin_user and admin_pass:
        try:
            conn.execute("INSERT OR IGNORE INTO users (username, password, role) VALUES (?, ?, ?)", 
                         (admin_user, pwd_context.hash(admin_pass), "ADMIN"))
            conn.commit()
        except: pass
    return conn

class RequeteLogin(BaseModel):
    identifiant: str
    mot_de_passe: str

def require_admin(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=["HS256"])
        if payload.get("role") != "ADMIN": raise HTTPException(status_code=403, detail="Role ADMIN required")
        return payload
    except: raise HTTPException(status_code=401, detail="Invalid token")

@router.post("/login")
async def login(requete: RequeteLogin):
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE username = ?", (requete.identifiant,)).fetchone()
    if not user or not pwd_context.verify(requete.mot_de_passe, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = jwt.encode({"sub": user["username"], "role": user["role"], "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=2)}, JWT_SECRET)
    return {"succes": True, "token": token, "role": user["role"]}
''')
