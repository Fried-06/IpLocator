from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from serveur.routes.auth import require_admin
from serveur.services.service_supervision import (
    get_db, initialiser_machines_par_defaut,
    sonder_machine_individuelle, sonder_toutes_les_machines
)

router = APIRouter()

class SchemaNouvelleMachine(BaseModel):
    ip: str
    nom: Optional[str] = None
    est_critique: bool = False
    port_l7: str = "80"
    protocole_l7: str = "HTTP"

class SchemaModifierCritique(BaseModel):
    est_critique: bool = True

@router.get("/machines")
async def lister_machines_supervisees(user=Depends(require_admin)):
    initialiser_machines_par_defaut()
    conn = get_db()
    rows = conn.execute("""
        SELECT id, ip, nom, est_critique, port_l7, protocole_l7,
               statut_l3, latence_l3, statut_l7, latence_l7, detail_l7,
               derniere_verification, date_creation
        FROM supervision_machines
        ORDER BY est_critique DESC, id ASC
    """).fetchall()
    conn.close()

    machines = [dict(r) for r in rows]

    total = len(machines)
    critiques_tot = sum(1 for m in machines if m["est_critique"])
    critiques_up = sum(1 for m in machines if m["est_critique"] and m["statut_l3"] == "UP")
    l3_up = sum(1 for m in machines if m["statut_l3"] == "UP")
    l7_up = sum(1 for m in machines if m["statut_l7"] == "UP")
    
    latences = [m["latence_l3"] for m in machines if m["latence_l3"] is not None and m["latence_l3"] > 0]
    latence_moy = round(sum(latences) / len(latences), 1) if latences else 1.0
    dispo_l3 = round((l3_up / total * 100), 1) if total > 0 else 100.0

    kpis = {
        "total_machines": total,
        "machines_critiques_total": critiques_tot,
        "machines_critiques_en_ligne": critiques_up,
        "machines_l3_up": l3_up,
        "taux_disponibilite_l3": f"{dispo_l3}%",
        "services_l7_actifs": l7_up,
        "latence_moyenne_ms": latence_moy
    }

    # Alias pratique pour le front
    for m in machines:
        m["latence_l3_ms"] = m["latence_l3"]

    return {
        "succes": True,
        "total": total,
        "kpis": kpis,
        "kpi": kpis,
        "machines": machines
    }

@router.post("/machines")
async def ajouter_machine_supervisee(machine: SchemaNouvelleMachine, user=Depends(require_admin)):
    ip_clean = machine.ip.strip()
    nom_clean = machine.nom.strip() if machine.nom and machine.nom.strip() else f"Station-{ip_clean}"
    
    conn = get_db()
    existant = conn.execute("SELECT id FROM supervision_machines WHERE ip = ?", (ip_clean,)).fetchone()
    if existant:
        conn.close()
        raise HTTPException(status_code=400, detail=f"L'adresse IP {ip_clean} est déjà surveillée.")

    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO supervision_machines (ip, nom, est_critique, port_l7, protocole_l7, date_creation)
        VALUES (?, ?, ?, ?, ?, datetime('now'))
    """, (ip_clean, nom_clean, 1 if machine.est_critique else 0, machine.port_l7, machine.protocole_l7.upper()))
    nouvel_id = cursor.lastrowid
    conn.commit()
    conn.close()

    # Sondage immédiat L3 et L7 pour afficher les données dès l'ajout
    resultat_sonde = await sonder_machine_individuelle(nouvel_id, ip_clean, machine.port_l7, machine.protocole_l7.upper())

    return {
        "succes": True,
        "message": f"Machine {nom_clean} ({ip_clean}) ajoutée et sondée avec succès.",
        "machine_id": nouvel_id,
        "sonde": resultat_sonde
    }

@router.put("/machines/{machine_id}/critique")
async def modifier_criticite_machine(
    machine_id: int,
    est_critique: Optional[bool] = None,
    modif: Optional[SchemaModifierCritique] = None,
    user=Depends(require_admin)
):
    valeur = est_critique if est_critique is not None else (modif.est_critique if modif else True)
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE supervision_machines SET est_critique = ? WHERE id = ?", (1 if valeur else 0, machine_id))
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Machine introuvable.")
    conn.commit()
    conn.close()
    return {"succes": True, "est_critique": valeur}

@router.delete("/machines/{machine_id}")
async def supprimer_machine_supervisee(machine_id: int, user=Depends(require_admin)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM supervision_machines WHERE id = ?", (machine_id,))
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Machine introuvable.")
    conn.commit()
    conn.close()
    return {"succes": True, "message": "Machine supprimée de la supervision."}

@router.post("/sonder")
async def declencher_sondage_manuel(user=Depends(require_admin)):
    """Déclenche un sondage immédiat de toutes les machines."""
    resultats = await sonder_toutes_les_machines()
    return {"succes": True, "sondages": resultats}
