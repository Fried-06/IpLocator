document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('form-tracing');
    const input = document.getElementById('input-target');
    const shortcuts = document.querySelectorAll('.btn-shortcut');

    // 1. Écouteur sur le formulaire complet (gère 'Entrée' et le clic sur le bouton type="submit")
    if (form) {
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            const target = input.value.trim();
            if (target) {
                lancerTracage(target, form.querySelector('button[type="submit"]'));
            }
        });
    }

    // 2. Écouteurs sur les raccourcis
    shortcuts.forEach(btn => {
        btn.addEventListener('click', () => {
            const target = btn.getAttribute('data-target');
            if (input) {
                input.value = target;
                input.focus();
            }
            const submitBtn = form ? form.querySelector('button[type="submit"]') : null;
            lancerTracage(target, submitBtn);
        });
    });
});

async function lancerTracage(target, btnElement) {
    let originalText = '';
    if (btnElement) {
        originalText = btnElement.innerHTML;
        btnElement.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> Traçage...';
        btnElement.disabled = true;
    }
    
    // Masquer les résultats pendant la recherche en utilisant style.display
    const resultContainer = document.getElementById('tracing-result-container');
    if (resultContainer) {
        resultContainer.style.display = 'none';
    }

    try {
        const response = await fetch(`http://localhost:8000/api/v1/tracage/recherche?cible=${encodeURIComponent(target)}`);
        
        if (response.ok) {
            const data = await response.json();
            afficherResultats(data);
        } else {
            alert("Équipement non trouvé ou erreur de communication API.");
        }
    } catch (error) {
        console.error("Erreur:", error);
        alert("Impossible de joindre le serveur API. Assurez-vous qu'uvicorn tourne.");
    } finally {
        if (btnElement) {
            btnElement.innerHTML = originalText;
            btnElement.disabled = false;
        }
    }
}

function afficherResultats(data) {
    const container = document.getElementById('tracing-result-container');
    if (!container) return;
    
    // Panneau A
    document.getElementById('res-equipement').textContent = data.equipement || '--';
    document.getElementById('res-ip').textContent = data.ip || '--';
    document.getElementById('res-mac').textContent = data.mac || '--';
    
    const elLatency = document.getElementById('res-latency');
    if (elLatency) elLatency.textContent = data.latence_ms ? `${data.latence_ms} ms` : '--';
    
    const badge = document.getElementById('res-status-badge');
    if (badge) {
        if (data.statut === "EN_LIGNE") {
            badge.textContent = "EN LIGNE";
            badge.style.cssText = "background:rgba(16,185,129,0.1);color:#10b981;border:1px solid rgba(16,185,129,0.3);";
        } else {
            badge.textContent = "HORS LIGNE";
            badge.style.cssText = "background:rgba(239,68,68,0.1);color:#f87171;border:1px solid rgba(239,68,68,0.3);";
        }
    }

    // Panneau B & C & D
    if (data.switch_rattachement) {
        document.getElementById('res-switch-name').textContent = data.switch_rattachement.nom || '--';
        document.getElementById('res-switch-ip').textContent = data.switch_rattachement.ip || '--';
        document.getElementById('res-port').textContent = data.switch_rattachement.port_acces || '--';
        document.getElementById('res-speed').textContent = data.switch_rattachement.vitesse_port || '--';
        document.getElementById('res-vlan').textContent = data.switch_rattachement.vlan || '--';
        document.getElementById('res-location').textContent = data.emplacement_physique || '--';
    } else {
        ['res-switch-name', 'res-switch-ip', 'res-port', 'res-speed', 'res-vlan'].forEach(id => {
            const el = document.getElementById(id);
            if(el) el.textContent = "--";
        });
        const loc = document.getElementById('res-location');
        if(loc) loc.textContent = "Localisation Inconnue";
    }

    // Génération du graphe de trajectoire
    dessinerTrajectoire(data.trajectoire_chemin);

    // Affichage avec animation via style.display
    container.style.display = 'block';
}

function dessinerTrajectoire(chemin) {
    const pathContainer = document.getElementById('path-container');
    if (!pathContainer) return;
    
    pathContainer.innerHTML = '';

    if (!chemin || chemin.length === 0) {
        pathContainer.innerHTML = '<div class="text-gray-500 italic w-full text-center py-4">Aucun chemin détecté (Équipement hors ligne ou introuvable)</div>';
        return;
    }

    chemin.forEach((noeud, index) => {
        let icon = "fa-server";
        let colorClass = "text-cyan";
        let bgClass = "bg-cyan/10 border-cyan/30";
        
        if (noeud.type === "POSTE_DEPART") {
            icon = "fa-laptop-code";
            colorClass = "text-gray-400";
            bgClass = "bg-[#0F172A] border-[#1F2937]";
        } else if (noeud.type === "SWITCH_CORE") {
            icon = "fa-sitemap";
            colorClass = "text-primary";
            bgClass = "bg-primary/10 border-primary/30";
        } else if (noeud.type === "SWITCH_ACCES") {
            icon = "fa-network-wired";
            colorClass = "text-amber-500";
            bgClass = "bg-amber-500/10 border-amber-500/30";
        } else if (noeud.type === "EQUIPEMENT_CIBLE") {
            icon = "fa-bullseye";
            colorClass = "text-primary";
            bgClass = "bg-primary/20 border-primary/50 shadow-[0_0_15px_rgba(16,185,129,0.3)]";
        }

        const isLast = index === chemin.length - 1;

        const nodeHtml = `
            <div class="relative flex flex-col items-center group cursor-pointer w-48 shrink-0">
                ${index > 0 ? `
                <div class="absolute top-6 -left-[5.5rem] w-20 flex justify-center -translate-y-1/2 z-10">
                    <div class="bg-[#0B111E] px-1 text-[9px] font-mono text-gray-500 border border-[#1F2937] rounded">${noeud.port_entree || '?'}</div>
                </div>` : ''}

                <div class="w-14 h-14 rounded-full ${bgClass} border flex items-center justify-center ${colorClass} text-xl relative z-10 bg-[#0B111E] hover:scale-110 transition-transform shadow-lg">
                    <i class="fa-solid ${icon}"></i>
                </div>

                ${!isLast ? `
                <div class="absolute top-6 left-[4.5rem] w-20 flex justify-center -translate-y-1/2 z-10">
                    <div class="bg-[#0B111E] px-1 text-[9px] font-mono text-gray-500 border border-[#1F2937] rounded">${noeud.port_sortie || '?'}</div>
                </div>` : ''}

                <div class="mt-4 text-center">
                    <h5 class="text-sm font-semibold text-white truncate w-40">${noeud.nom}</h5>
                    <p class="text-[10px] text-gray-500 mt-1 uppercase tracking-widest">${noeud.type.replace('_', ' ')}</p>
                </div>
            </div>
        `;
        pathContainer.insertAdjacentHTML('beforeend', nodeHtml);
    });
}