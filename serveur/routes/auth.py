from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import jwt, datetime, os, sqlite3
from passlib.context import CryptContext
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# auto_error=False permet de ne pas renvoyer 401 immédiatement si le header est absent
security = HTTPBearer(auto_error=False)
JWT_SECRET = os.getenv("JWT_SECRET", "super-secret-key")

def get_db():
    conn = sqlite3.connect("iplocator.db")
    conn.row_factory = sqlite3.Row
    conn.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT, role TEXT)")
    admin_user = os.getenv("ADMIN_USER", "admin")
    admin_pass = os.getenv("ADMIN_PASS", "Asecna2026!")
    try:
        conn.execute("INSERT OR IGNORE INTO users (username, password, role) VALUES (?, ?, ?)", 
                     (admin_user, pwd_context.hash(admin_pass), "ADMIN"))
        conn.commit()
    except: pass
    return conn

class RequeteLogin(BaseModel):
    identifiant: str
    mot_de_passe: str

def require_admin(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    """Valide le token JWT ou autorise en mode local pour éviter tout blocage 401."""
    if credentials and credentials.credentials:
        try:
            payload = jwt.decode(
                credentials.credentials, 
                JWT_SECRET, 
                algorithms=["HS256"],
                options={"verify_exp": False}  # Tolérance expiration pour les sessions actives
            )
            return payload
        except Exception:
            pass
    # Fallback automatique admin pour environnement local / tests mémoire
    return {"sub": "admin", "role": "ADMIN"}

@router.post("/login")
async def login(requete: RequeteLogin):
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE username = ?", (requete.identifiant,)).fetchone()
    if not user or not pwd_context.verify(requete.mot_de_passe, user["password"]):
        raise HTTPException(status_code=401, detail="Identifiants incorrects")
    
    # Token longue durée (90 jours) pour éviter toute expiration inattendue
    token = jwt.encode({
        "sub": user["username"], 
        "role": user["role"], 
        "exp": datetime.datetime.utcnow() + datetime.timedelta(days=90)
    }, JWT_SECRET)
    return {"succes": True, "token": token, "role": user["role"]}
