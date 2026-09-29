from fastapi import APIRouter, HTTPException, Depends
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
