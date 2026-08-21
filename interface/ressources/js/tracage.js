document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('form-tracing');
    const input = document.getElementById('input-target');
    const shortcuts = document.querySelectorAll('.btn-shortcut');

    if (form) {
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            const target = input.value.trim();
            if (target) {
                lancerTracage(target, form.querySelector('button[type="submit"]'));
            }
        });
    }

    shortcuts.forEach(btn => {
        btn.addEventListener('click', () => {
            const target = btn.getAttribute('data-target');
            input.value = target;
            // Highlight animation on input
            input.classList.add('ring-2', 'ring-primary');
            setTimeout(() => input.classList.remove('ring-2', 'ring-primary'), 500);
            
            const submitBtn = form.querySelector('button[type="submit"]');
            lancerTracage(target, submitBtn);
        });
    });
});

async function lancerTracage(target, btnElement) {
    const originalText = btnElement.innerHTML;
    btnElement.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> Traçage...';
    btnElement.disabled = true;
    
    // Masquer les résultats pendant la recherche
    const resultContainer = document.getElementById('tracing-result-container');
    resultContainer.classList.add('hidden');
    resultContainer.classList.remove('fadeIn');

    try {
        // En vrai: fetch(`http://localhost:8000/api/v1/tracage/recherche?cible=${encodeURIComponent(target)}`)
        // Pour le POC, on assume le port 8000
        const response = await fetch(`http://localhost:8000/api/v1/tracage/recherche?cible=${encodeURIComponent(target)}`);
        
        if (response.ok) {
            const data = await response.json();
            afficherResultats(data);
        } else {
            alert("Erreur de communication avec le backend API.");
        }
    } catch (error) {
        console.error("Erreur:", error);
        alert("Impossible de joindre le serveur API. Assurez-vous qu'uvicorn tourne.");
    } finally {
        btnElement.innerHTML = originalText;
        btnElement.disabled = false;
    }
}

function afficherResultats(data) {
    const container = document.getElementById('tracing-result-container');
    
    // Panneau A
    document.getElementById('res-equipement').textContent = data.equipement;
    document.getElementById('res-ip').textContent = data.ip;
    document.getElementById('res-mac').textContent = data.mac;
    document.getElementById('res-latency').textContent = data.latence_ms ? `${data.latence_ms} ms` : '--';
    
    const badge = document.getElementById('res-status-badge');
    if (data.statut === "EN_LIGNE") {
        badge.textContent = "EN LIGNE";
        badge.className = "px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider bg-primary/20 text-primary border border-primary/30";
    } else {
        badge.textContent = "HORS LIGNE";
        badge.className = "px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider bg-gray-500/20 text-gray-400 border border-gray-500/30";
    }

    // Panneau B & C & D
    if (data.switch_rattachement) {
        document.getElementById('res-switch-name').textContent = data.switch_rattachement.nom;
        document.getElementById('res-switch-ip').textContent = data.switch_rattachement.ip;
        document.getElementById('res-port').textContent = data.switch_rattachement.port_acces;
        document.getElementById('res-speed').textContent = data.switch_rattachement.vitesse_port;
        document.getElementById('res-vlan').textContent = data.switch_rattachement.vlan;
        document.getElementById('res-location').textContent = data.emplacement_physique;
    } else {
        document.getElementById('res-switch-name').textContent = "--";
        document.getElementById('res-switch-ip').textContent = "--";
        document.getElementById('res-port').textContent = "--";
        document.getElementById('res-speed').textContent = "--";
        document.getElementById('res-vlan').textContent = "--";
        document.getElementById('res-location').textContent = "Localisation Inconnue";
    }

    // Génération du graphe de trajectoire
    dessinerTrajectoire(data.trajectoire_chemin);

    // Affichage avec animation
    container.classList.remove('hidden');
    container.classList.add('view-section'); // triggers fadeIn
}

function dessinerTrajectoire(chemin) {
    const pathContainer = document.getElementById('path-container');
    pathContainer.innerHTML = '';

    if (!chemin || chemin.length === 0) {
        pathContainer.innerHTML = '<div class="text-gray-500 italic w-full text-center py-4">Aucun chemin détecté (Équipement hors ligne ou introuvable)</div>';
        return;
    }

    chemin.forEach((noeud, index) => {
        // Déterminer l'icône et les couleurs en fonction du type
        let icon = "fa-server";
        let colorClass = "text-blue-500";
        let bgClass = "bg-blue-500/10 border-blue-500/30";
        
        if (noeud.type === "POSTE_DEPART") {
            icon = "fa-laptop-code";
            colorClass = "text-gray-400";
            bgClass = "bg-surface border-border";
        } else if (noeud.type === "SWITCH_CORE") {
            icon = "fa-sitemap";
            colorClass = "text-purple-500";
            bgClass = "bg-purple-500/10 border-purple-500/30";
        } else if (noeud.type === "SWITCH_ACCES") {
            icon = "fa-network-wired";
            colorClass = "text-emerald-500";
            bgClass = "bg-emerald-500/10 border-emerald-500/30";
        } else if (noeud.type === "EQUIPEMENT_CIBLE") {
            icon = "fa-bullseye";
            colorClass = "text-primary";
            bgClass = "bg-primary/20 border-primary/50 shadow-[0_0_15px_rgba(16,185,129,0.3)]";
        }

        const isLast = index === chemin.length - 1;

        // Html Node
        const nodeHtml = `
            <div class="relative flex flex-col items-center group cursor-pointer w-48 shrink-0">
                <!-- Info Bulle (Hover) -->
                <div class="absolute -top-16 opacity-0 group-hover:opacity-100 transition-opacity bg-dark border border-border rounded-lg p-2 text-xs shadow-xl z-20 whitespace-nowrap pointer-events-none">
                    <p class="font-bold text-white mb-1">${noeud.nom}</p>
                    ${noeud.ip ? `<p class="text-gray-400 font-mono">IP: ${noeud.ip}</p>` : ''}
                </div>

                <!-- Entrée du Lien (Sauf premier nœud) -->
                ${index > 0 ? `
                <div class="absolute top-6 -left-[5.5rem] w-20 flex justify-center -translate-y-1/2 z-10">
                    <div class="bg-dark px-1 text-[9px] font-mono text-gray-500 border border-border rounded">
                        ${noeud.port_entree}
                    </div>
                </div>
                ` : ''}

                <!-- Le Cercle du Nœud -->
                <div class="w-14 h-14 rounded-full ${bgClass} border-2 flex items-center justify-center ${colorClass} text-xl relative z-10 bg-dark hover:scale-110 transition-transform shadow-lg">
                    <i class="fa-solid ${icon}"></i>
                </div>

                <!-- Sortie du Lien (Sauf dernier nœud) -->
                ${!isLast ? `
                <div class="absolute top-6 left-[4.5rem] w-20 flex justify-center -translate-y-1/2 z-10">
                    <div class="bg-dark px-1 text-[9px] font-mono text-gray-500 border border-border rounded">
                        ${noeud.port_sortie}
                    </div>
                </div>
                ` : ''}

                <!-- Labels sous le nœud -->
                <div class="mt-4 text-center">
                    <h5 class="text-sm font-semibold text-white truncate w-40">${noeud.nom}</h5>
                    <p class="text-[10px] text-gray-500 mt-1">${noeud.type.replace('_', ' ')}</p>
                </div>
            </div>
        `;

        pathContainer.insertAdjacentHTML('beforeend', nodeHtml);
    });
}
