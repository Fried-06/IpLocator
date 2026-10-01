import asyncio
import socket
import time
import sqlite3
import logging
from typing import Dict, Any, List, Tuple
from serveur.services.service_arp import ping_host

logger = logging.getLogger("service_supervision")

def get_db():
    conn = sqlite3.connect("iplocator.db")
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS supervision_machines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip TEXT UNIQUE NOT NULL,
            nom TEXT NOT NULL,
            est_critique INTEGER DEFAULT 0,
            port_l7 INTEGER DEFAULT 80,
            protocole_l7 TEXT DEFAULT 'HTTP',
            statut_l3 TEXT DEFAULT 'INCONNU',
            latence_l3 REAL,
            statut_l7 TEXT DEFAULT 'INCONNU',
            latence_l7 REAL,
            detail_l7 TEXT,
            derniere_verification TEXT,
            date_creation TEXT
        )
    """)
    conn.commit()
    return conn

def initialiser_machines_par_defaut():
    """Initialise une liste de départ si la table est vide."""
    try:
        conn = get_db()
        count = conn.execute("SELECT COUNT(*) FROM supervision_machines").fetchone()[0]
        if count == 0:
            machines = [
                ("10.28.12.99", "Switch-Cœur Cisco 2960", 1, 22, "SSH"),
                ("10.28.40.5", "Poste NOC (Administrateur)", 1, 445, "SMB/RDP"),
                ("10.28.8.9", "Serveur TGO-00RP", 0, 80, "HTTP"),
                ("10.28.16.114", "Station DESKTOP-BL4V220", 0, 80, "HTTP")
            ]
            for ip, nom, critique, port, proto in machines:
                conn.execute("""
                    INSERT OR IGNORE INTO supervision_machines 
                    (ip, nom, est_critique, port_l7, protocole_l7, date_creation)
                    VALUES (?, ?, ?, ?, ?, datetime('now'))
                """, (ip, nom, critique, port, proto))
            conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Erreur initialisation supervision_machines: {e}")

async def tester_couche_l3(ip: str) -> Tuple[str, float]:
    """Test de niveau Couche 3 (Réseau) via Ping ICMP."""
    loop = asyncio.get_event_loop()
    en_ligne, latence = await loop.run_in_executor(None, ping_host, ip, 800)
    if en_ligne:
        return "UP", round(latence, 1)
    return "DOWN", 0.0

PORTS_CONNUES = {
    80: "HTTP",
    443: "HTTPS",
    8080: "HTTP",
    8443: "HTTPS",
    22: "SSH",
    21: "FTP",
    25: "SMTP",
    53: "DNS",
    110: "POP3",
    143: "IMAP",
    445: "SMB",
    3389: "RDP",
    3306: "MySQL",
    5432: "PostgreSQL",
    1521: "Oracle",
    1433: "MSSQL"
}

async def tester_couche_l7_unitaire(ip: str, port: int, protocole: str = "AUTO", timeout: float = 1.5) -> Tuple[str, float, str]:
    """Test unitaire de niveau Couche 7 via sonde TCP avec identification protocolaire."""
    debut = time.time()
    
    # Détection du protocole selon le port ou la consigne
    proto_label = PORTS_CONNUES.get(port, protocole.upper() if protocole and protocole != "AUTO" else f"TCP")

    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(ip, port),
            timeout=timeout
        )
        duree_ms = round((time.time() - debut) * 1000, 1)
        detail = f"{proto_label}:{port} UP"
        
        if proto_label in ["HTTP", "WEB"] or port in [80, 8080]:
            try:
                requete = f"HEAD / HTTP/1.1\r\nHost: {ip}\r\nUser-Agent: AsecnaSupervision/1.0\r\nConnection: close\r\n\r\n".encode()
                writer.write(requete)
                await writer.drain()
                reponse = await asyncio.wait_for(reader.read(128), timeout=1.0)
                if reponse:
                    premiere_ligne = reponse.decode(errors='ignore').split('\r\n')[0]
                    # ex: HTTP/1.1 200 OK -> "HTTP:80 (200 OK)"
                    parties = premiere_ligne.split(' ', 2)
                    code_http = " ".join(parties[1:]) if len(parties) > 1 else premiere_ligne[:15]
                    detail = f"HTTP:{port} ({code_http})"
            except Exception:
                detail = f"HTTP:{port} Ouvert"
        elif proto_label == "SSH" or port == 22:
            try:
                banniere = await asyncio.wait_for(reader.read(64), timeout=1.0)
                if banniere:
                    txt = banniere.decode(errors='ignore').strip()
                    detail = f"SSH:{port} ({txt[:16]})"
            except Exception:
                detail = f"SSH:{port} Ouvert"
        elif proto_label == "HTTPS" or port in [443, 8443]:
            detail = f"HTTPS:{port} Ouvert"
        elif proto_label == "SMB" or port == 445:
            detail = f"SMB:{port} Ouvert"
        elif proto_label == "RDP" or port == 3389:
            detail = f"RDP:{port} Ouvert"

        writer.close()
        await writer.wait_closed()
        return "UP", duree_ms, detail

    except asyncio.TimeoutError:
        duree_ms = round((time.time() - debut) * 1000, 1)
        return "DOWN", duree_ms, f"{proto_label}:{port} (timeout)"
    except ConnectionRefusedError:
        duree_ms = round((time.time() - debut) * 1000, 1)
        return "DOWN", duree_ms, f"{proto_label}:{port} (fermé)"
    except Exception as e:
        duree_ms = round((time.time() - debut) * 1000, 1)
        return "DOWN", duree_ms, f"{proto_label}:{port} ({str(e)[:15]})"

async def tester_couche_l7(ip: str, ports_str: Any, protocole: str = "HTTP", timeout: float = 1.5) -> Tuple[str, float, str]:
    """Test de niveau Couche 7 gérant un ou plusieurs ports séparés par des virgules."""
    ports = []
    if isinstance(ports_str, int):
        ports = [ports_str]
    else:
        for p in str(ports_str).replace(" ", "").split(","):
            if p.isdigit():
                ports.append(int(p))
                
    if not ports:
        return "DOWN", 0.0, "Aucun port valide"
        
    tasks = [tester_couche_l7_unitaire(ip, p, protocole, timeout) for p in ports]
    resultats = await asyncio.gather(*tasks, return_exceptions=False)
    
    ups = [r for r in resultats if r[0] == "UP"]
    downs = [r for r in resultats if r[0] == "DOWN"]
    
    if ups:
        duree_ms = round(sum(u[1] for u in ups) / len(ups), 1)
        details = " | ".join([u[2] for u in ups])
        if downs:
            details += f" (et {len(downs)} DOWN)"
        return "UP", duree_ms, details
    else:
        duree_ms = round(sum(d[1] for d in downs) / len(downs), 1) if downs else 0.0
        details = " | ".join([d[2] for d in downs])
        return "DOWN", duree_ms, details

async def sonder_machine_individuelle(id_machine: int, ip: str, port_l7: int, proto_l7: str) -> Dict[str, Any]:
    """Exécute les sondages L3 et L7 en parallèle pour une machine donnée."""
    res_l3, res_l7 = await asyncio.gather(
        tester_couche_l3(ip),
        tester_couche_l7(ip, port_l7, proto_l7),
        return_exceptions=False
    )
    statut_l3, latence_l3 = res_l3
    statut_l7, latence_l7, detail_l7 = res_l7

    try:
        conn = get_db()
        conn.execute("""
            UPDATE supervision_machines
            SET statut_l3 = ?, latence_l3 = ?,
                statut_l7 = ?, latence_l7 = ?, detail_l7 = ?,
                derniere_verification = datetime('now')
            WHERE id = ?
        """, (statut_l3, latence_l3, statut_l7, latence_l7, detail_l7, id_machine))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Erreur mise à jour sondage machine {ip}: {e}")

    return {
        "id": id_machine,
        "ip": ip,
        "statut_l3": statut_l3,
        "latence_l3": latence_l3,
        "statut_l7": statut_l7,
        "latence_l7": latence_l7,
        "detail_l7": detail_l7
    }

async def sonder_toutes_les_machines() -> List[Dict[str, Any]]:
    """Sonde l'intégralité des machines supervisées en parallèle."""
    initialiser_machines_par_defaut()
    conn = get_db()
    lignes = conn.execute("SELECT id, ip, port_l7, protocole_l7 FROM supervision_machines").fetchall()
    conn.close()

    if not lignes:
        return []

    taches = [
        sonder_machine_individuelle(row["id"], row["ip"], row["port_l7"] or 80, row["protocole_l7"] or "HTTP")
        for row in lignes
    ]
    resultats = await asyncio.gather(*taches, return_exceptions=True)
    return [r for r in resultats if isinstance(r, dict)]
