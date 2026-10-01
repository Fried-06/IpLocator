/**
 * tableau_de_bord.js — Cockpit NOC & Supervision Proactive L3 / L7
 * Visualisation du trafic, KPIs réseau et télémétrie multi-couches.
 */

let trafficChartInstance = null;
let portsChartInstance = null;
let listeMachinesSupervision = [];
let filtreSupervisionActif = 'tous';
let timerAutoRefresh = null;

// Initialisation des graphiques Chart.js du tableau de bord
function initDashboardCharts() {
    const ctxTraffic = document.getElementById('chart-traffic');
    if (ctxTraffic && !trafficChartInstance) {
        const labels = ['10:00', '10:05', '10:10', '10:15', '10:20', '10:25', '10:30', '10:35', '10:40', '10:45'];
        const dataIn = [120, 145, 130, 210, 312, 280, 340, 420, 310, 312];
        const dataOut = [80, 95, 85, 140, 190, 170, 220, 260, 195, 210];

        trafficChartInstance = new Chart(ctxTraffic, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Trafic Entrant (Mbps)',
                        data: dataIn,
                        borderColor: '#10B981',
                        backgroundColor: 'rgba(16, 185, 129, 0.1)',
                        fill: true,
                        tension: 0.4,
                        borderWidth: 2,
                        pointRadius: 3,
                        pointBackgroundColor: '#10B981'
                    },
                    {
                        label: 'Trafic Sortant (Mbps)',
                        data: dataOut,
                        borderColor: '#06B6D4',
                        backgroundColor: 'rgba(6, 182, 212, 0.05)',
                        fill: true,
                        tension: 0.4,
                        borderWidth: 2,
                        pointRadius: 3,
                        pointBackgroundColor: '#06B6D4'
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    x: {
                        grid: { color: 'rgba(31, 41, 55, 0.5)' },
                        ticks: { color: '#6B7280', font: { family: 'Roboto Mono', size: 10 } }
                    },
                    y: {
                        grid: { color: 'rgba(31, 41, 55, 0.5)' },
                        ticks: { color: '#6B7280', font: { family: 'Roboto Mono', size: 10 } }
                    }
                }
            }
        });
    }

    const ctxPorts = document.getElementById('chart-ports');
    if (ctxPorts && !portsChartInstance) {
        portsChartInstance = new Chart(ctxPorts, {
            type: 'doughnut',
            data: {
                labels: ['En Ligne (UP)', 'Dégradé / Partiel', 'Hors Ligne (DOWN)'],
                datasets: [{
                    data: [0, 0, 0],
                    backgroundColor: ['#10B981', '#F59E0B', '#EF4444'],
                    borderColor: '#111827',
                    borderWidth: 3,
                    hoverOffset: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '72%',
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const val = context.raw || 0;
                                return ` ${context.label} : ${val} machine${val > 1 ? 's' : ''}`;
                            }
                        }
                    }
                }
            }
        });
    }

    if (typeof mettreAJourGraphiqueCritiques === 'function') {
        mettreAJourGraphiqueCritiques();
    }
}

// ═══════════════════════════════════════════════════════════════════
// GESTION DE LA SUPERVISION PROACTIVE (COUCHE 3 & COUCHE 7)
// ═══════════════════════════════════════════════════════════════════

/**
 * Récupère l'en-tête d'authentification Bearer
 */
function getAuthHeaders() {
    const token = typeof getToken === 'function' ? getToken() : localStorage.getItem('token');
    const headers = { 'Content-Type': 'application/json' };
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }
    return headers;
}

/**
 * Charge les machines et met à jour les indicateurs du Dashboard
 */
async function chargerSupervision() {
    const tbody = document.getElementById('tbody-supervision');
    try {
        const response = await fetch('http://localhost:8000/api/v1/supervision/machines', {
            method: 'GET',
            headers: getAuthHeaders()
        });

        if (!response.ok) {
            if (tbody) {
                tbody.innerHTML = `<tr><td colspan="6" class="py-6 text-center text-danger">
                    <i class="fa-solid fa-triangle-exclamation mr-1.5"></i> Erreur lors du chargement (${response.status})
                </td></tr>`;
            }
            return;
        }

        const data = await response.json();
        listeMachinesSupervision = data.machines || [];

        // 1. Mettre à jour les KPIs du haut
        mettreAJourKpis(data.kpis);

        // 2. Mettre à jour les compteurs des onglets de filtre
        mettreAJourCompteursFiltres();

        // 3. Rendu du tableau des machines
        rendreTableauSupervision();

        // 4. Mettre à jour le graphique donut des Machines Critiques
        mettreAJourGraphiqueCritiques();

        // 5. Synchroniser les accès rapides de la vue Traçage
        if (typeof window.chargerRaccourcisCritiques === 'function') {
            window.chargerRaccourcisCritiques(listeMachinesSupervision);
        }

    } catch (err) {
        console.error('Erreur chargement supervision:', err);
        if (tbody) {
            tbody.innerHTML = `<tr><td colspan="6" class="py-6 text-center text-gray-500 italic">
                <i class="fa-solid fa-triangle-exclamation text-warning mr-1.5"></i> Impossible de contacter l'API de supervision.
            </td></tr>`;
        }
    }
}

/**
 * Met à jour les 4 cartes KPI du haut du Dashboard
 */
function mettreAJourKpis(kpis) {
    if (!kpis) return;

    const elDispoL3 = document.getElementById('kpi-dispo-l3');
    if (elDispoL3) elDispoL3.textContent = kpis.taux_disponibilite_l3 || '0%';

    const elCritiquesOnline = document.getElementById('kpi-critiques-online');
    if (elCritiquesOnline) elCritiquesOnline.textContent = kpis.machines_critiques_en_ligne ?? 0;

    const elCritiquesTotal = document.getElementById('kpi-critiques-total');
    if (elCritiquesTotal) elCritiquesTotal.textContent = kpis.machines_critiques_total ?? 0;

    const elServicesL7 = document.getElementById('kpi-services-l7');
    if (elServicesL7) elServicesL7.textContent = `${kpis.services_l7_actifs ?? 0}/${kpis.total_machines ?? 0}`;

    const elLatenceMoy = document.getElementById('kpi-latence-moy');
    if (elLatenceMoy) elLatenceMoy.textContent = kpis.latence_moyenne_ms ?? 0;
}

/**
 * Met à jour le graphique donut et la télémétrie des Machines Critiques
 */
function mettreAJourGraphiqueCritiques() {
    const critiques = listeMachinesSupervision.filter(m => m.est_critique);
    const totalCritiques = critiques.length;

    let upCount = 0;
    let warnCount = 0;
    let downCount = 0;

    critiques.forEach(m => {
        const l3Up = m.statut_l3 === 'UP';
        const l7Up = m.statut_l7 === 'UP';

        if (l3Up && l7Up) {
            upCount++;
        } else if (l3Up || l7Up) {
            warnCount++;
        } else {
            downCount++;
        }
    });

    // Badge total
    const elBadge = document.getElementById('badge-total-critiques');
    if (elBadge) {
        elBadge.textContent = `${totalCritiques} critique${totalCritiques > 1 ? 's' : ''}`;
    }

    // Pourcentage au centre du donut
    const elPct = document.getElementById('chart-critiques-pct');
    if (elPct) {
        const pct = totalCritiques > 0 ? Math.round((upCount / totalCritiques) * 100) : 0;
        elPct.textContent = `${pct}%`;
    }

    // Mini-légende sous le donut
    const elUp = document.getElementById('donut-critiques-up');
    if (elUp) elUp.textContent = upCount;
    const elWarn = document.getElementById('donut-critiques-warn');
    if (elWarn) elWarn.textContent = warnCount;
    const elDown = document.getElementById('donut-critiques-down');
    if (elDown) elDown.textContent = downCount;

    // Mise à jour visuelle du Donut Chart
    if (portsChartInstance) {
        if (totalCritiques === 0) {
            // Pas encore de machines critiques définies
            portsChartInstance.data.datasets[0].data = [0, 0, 0];
        } else {
            portsChartInstance.data.datasets[0].data = [upCount, warnCount, downCount];
        }
        portsChartInstance.update();
    }
}

/**
 * Met à jour les compteurs des boutons de filtrage
 */
function mettreAJourCompteursFiltres() {
    const total = listeMachinesSupervision.length;
    const critiques = listeMachinesSupervision.filter(m => m.est_critique).length;
    const alertes = listeMachinesSupervision.filter(m => m.statut_l3 !== 'UP' || m.statut_l7 !== 'UP').length;

    const cTous = document.getElementById('compteur-tous');
    if (cTous) cTous.textContent = total;

    const cCrit = document.getElementById('compteur-critiques');
    if (cCrit) cCrit.textContent = critiques;

    const cAlertes = document.getElementById('compteur-alertes');
    if (cAlertes) cAlertes.textContent = alertes;
}

/**
 * Formate un timestamp pour affichage clair
 */
function formaterDateSondage(isoStr) {
    if (!isoStr) return '--:--:--';
    try {
        const d = new Date(isoStr);
        return d.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    } catch {
        return isoStr;
    }
}

/**
 * Rendu HTML des lignes du tableau de supervision
 */
function rendreTableauSupervision() {
    const tbody = document.getElementById('tbody-supervision');
    if (!tbody) return;

    let machinesAffichees = listeMachinesSupervision;

    if (filtreSupervisionActif === 'critiques') {
        machinesAffichees = listeMachinesSupervision.filter(m => m.est_critique);
    } else if (filtreSupervisionActif === 'alertes') {
        machinesAffichees = listeMachinesSupervision.filter(m => m.statut_l3 !== 'UP' || m.statut_l7 !== 'UP');
    }

    if (machinesAffichees.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6" class="py-10 text-center text-gray-500">
                    <i class="fa-solid fa-server text-gray-600 text-2xl mb-2 block"></i>
                    Aucun équipement ne correspond au filtre actif.
                    <div class="mt-3">
                        <button type="button" onclick="ouvrirModalAjoutMachine()" class="text-xs text-primary underline hover:text-emerald-400">
                            + Ajouter une machine en supervision
                        </button>
                    </div>
                </td>
            </tr>
        `;
        return;
    }

    let html = '';
    machinesAffichees.forEach(m => {
        // Détermination du badge Criticité
        const badgeCritique = m.est_critique
            ? `<button type="button" onclick="basculerCriticiteMachine(${m.id}, false)"
                    class="group inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] font-bold tracking-wider uppercase transition-all"
                    style="background:rgba(245,158,11,0.15);color:#fbbf24;border:1px solid rgba(245,158,11,0.4);"
                    title="Machine Critique NOC — Cliquer pour repasser en standard">
                    <i class="fa-solid fa-star text-warning text-xs"></i>
                    <span>CRITIQUE</span>
                    <i class="fa-solid fa-pen text-[9px] opacity-0 group-hover:opacity-100 transition-opacity ml-1"></i>
               </button>`
            : `<button type="button" onclick="basculerCriticiteMachine(${m.id}, true)"
                    class="group inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] font-medium tracking-wider uppercase text-gray-400 hover:text-white hover:border-amber-500/50 transition-all"
                    style="background:#0F172A;border:1px solid #1F2937;"
                    title="Équipement Standard — Cliquer pour définir comme CRITIQUE">
                    <i class="fa-regular fa-star text-xs text-gray-500 group-hover:text-warning"></i>
                    <span>Standard</span>
                    <i class="fa-solid fa-plus text-[9px] opacity-0 group-hover:opacity-100 transition-opacity ml-1 text-warning"></i>
               </button>`;

        // Badge Couche 3 (Ping Réseau)
        let badgeL3 = '';
        if (m.statut_l3 === 'UP') {
            const latence = m.latence_l3_ms !== null ? `${m.latence_l3_ms.toFixed(1)} ms` : '&lt; 1 ms';
            badgeL3 = `
                <div class="inline-flex items-center gap-2 px-2.5 py-1 rounded-lg text-xs font-mono font-bold"
                    style="background:rgba(16,185,129,0.1);color:#10b981;border:1px solid rgba(16,185,129,0.3);">
                    <span class="h-2 w-2 rounded-full bg-primary badge-pulse"></span>
                    <span>UP</span>
                    <span class="text-[10px] text-gray-400 font-normal">(${latence})</span>
                </div>
            `;
        } else if (m.statut_l3 === 'DOWN') {
            badgeL3 = `
                <div class="inline-flex items-center gap-2 px-2.5 py-1 rounded-lg text-xs font-mono font-bold"
                    style="background:rgba(239,68,68,0.12);color:#ef4444;border:1px solid rgba(239,68,68,0.35);">
                    <i class="fa-solid fa-circle-xmark text-danger text-xs"></i>
                    <span>DOWN</span>
                </div>
            `;
        } else {
            badgeL3 = `
                <div class="inline-flex items-center gap-2 px-2.5 py-1 rounded-lg text-xs font-mono"
                    style="background:rgba(107,114,128,0.15);color:#9ca3af;border:1px solid #374151;">
                    <i class="fa-solid fa-spinner fa-spin text-xs"></i>
                    <span>EN COURS</span>
                </div>
            `;
        }

        // Badge Couche 7 (Service Applicatif)
        let badgeL7 = '';
        const protoLabel = (m.protocole_l7 === 'AUTO') ? 'Multi-L7' : m.protocole_l7;

        if (m.statut_l7 === 'UP') {
            badgeL7 = `
                <div>
                    <div class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-mono font-bold"
                        style="background:rgba(6,182,212,0.1);color:#06b6d4;border:1px solid rgba(6,182,212,0.3);">
                        <i class="fa-solid fa-check text-[10px]"></i>
                        <span>${protoLabel} : ${m.port_l7} UP</span>
                    </div>
                    ${m.detail_l7 ? `<div class="text-[10px] text-gray-400 font-mono mt-0.5 max-w-xs" title="${m.detail_l7}">${m.detail_l7}</div>` : ''}
                </div>
            `;
        } else if (m.statut_l7 === 'DOWN') {
            badgeL7 = `
                <div>
                    <div class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-mono font-bold"
                        style="background:rgba(239,68,68,0.12);color:#f87171;border:1px solid rgba(239,68,68,0.35);">
                        <i class="fa-solid fa-xmark text-[10px]"></i>
                        <span>${protoLabel} : ${m.port_l7} DOWN</span>
                    </div>
                    ${m.detail_l7 ? `<div class="text-[10px] text-rose-400/80 font-mono mt-0.5 max-w-xs" title="${m.detail_l7}">${m.detail_l7}</div>` : ''}
                </div>
            `;
        } else {
            badgeL7 = `
                <div class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-mono text-gray-400"
                    style="background:#0F172A;border:1px solid #1F2937;">
                    <i class="fa-solid fa-minus text-[10px]"></i>
                    <span>${m.protocole_l7}:${m.port_l7}</span>
                </div>
            `;
        }

        // Horodatage
        const dateSondage = formaterDateSondage(m.derniere_verification);

        // Icone selon le nom ou type
        let iconeMachine = 'fa-desktop';
        const nomMin = (m.nom || '').toLowerCase();
        if (nomMin.includes('switch') || nomMin.includes('commutateur') || nomMin.includes('routeur')) iconeMachine = 'fa-network-wired';
        else if (nomMin.includes('serveur') || nomMin.includes('srv') || nomMin.includes('dns') || nomMin.includes('dc')) iconeMachine = 'fa-server';
        else if (nomMin.includes('noc')) iconeMachine = 'fa-shield-halved';

        html += `
            <tr class="hover:bg-slate-800/40 transition-colors ${m.est_critique && (m.statut_l3 === 'DOWN' || m.statut_l7 === 'DOWN') ? 'bg-red-950/20' : ''}">
                <!-- Équipement / IP -->
                <td class="py-3 px-4">
                    <div class="flex items-center gap-3">
                        <div class="h-8 w-8 rounded-lg flex items-center justify-center shrink-0 ${m.est_critique ? 'bg-amber-500/10 border border-amber-500/30 text-warning' : 'bg-slate-800 border border-slate-700 text-gray-400'}">
                            <i class="fa-solid ${iconeMachine} text-xs"></i>
                        </div>
                        <div>
                            <div class="font-bold text-white text-xs tracking-wide flex items-center gap-1.5">
                                ${m.nom || 'Station Réseau'}
                                ${m.est_critique ? '<span class="h-1.5 w-1.5 rounded-full bg-warning inline-block" title="Priorité Haute"></span>' : ''}
                            </div>
                            <div class="font-mono text-[11px] text-gray-400 flex items-center gap-1 mt-0.5">
                                <span class="text-primary">${m.ip}</span>
                            </div>
                        </div>
                    </div>
                </td>

                <!-- Criticité -->
                <td class="py-3 px-4">
                    ${badgeCritique}
                </td>

                <!-- Couche 3 (Ping) -->
                <td class="py-3 px-4">
                    ${badgeL3}
                </td>

                <!-- Couche 7 (Service) -->
                <td class="py-3 px-4">
                    ${badgeL7}
                </td>

                <!-- Horodatage -->
                <td class="py-3 px-4 font-mono text-[11px] text-gray-400">
                    <i class="fa-regular fa-clock text-[10px] mr-1 text-gray-600"></i>${dateSondage}
                </td>

                <!-- Actions -->
                <td class="py-3 px-4 text-right">
                    <div class="inline-flex items-center gap-1.5">
                        <button type="button" onclick="tracerDepuisDashboard('${m.ip}')"
                            class="px-2.5 py-1.5 rounded text-[11px] font-semibold text-primary hover:text-white transition-all flex items-center gap-1"
                            style="background:rgba(16,185,129,0.08);border:1px solid rgba(16,185,129,0.25);"
                            title="Localiser sur le commutateur physique">
                            <i class="fa-solid fa-crosshairs text-[10px]"></i>
                            <span>Tracer</span>
                        </button>
                        <button type="button" onclick="supprimerMachineSupervision(${m.id}, '${m.ip}')"
                            class="p-1.5 rounded text-gray-500 hover:text-danger transition-colors"
                            style="background:#0F172A;border:1px solid #1F2937;"
                            title="Retirer de la supervision">
                            <i class="fa-solid fa-trash-can text-xs"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `;
    });

    tbody.innerHTML = html;
}

/**
 * Bascule la criticité d'une machine (PUT /api/v1/supervision/machines/{id}/critique)
 */
async function basculerCriticiteMachine(machineId, estCritique) {
    try {
        const response = await fetch(`http://localhost:8000/api/v1/supervision/machines/${machineId}/critique?est_critique=${estCritique}`, {
            method: 'PUT',
            headers: getAuthHeaders()
        });

        if (response.ok) {
            await chargerSupervision();
        } else {
            const err = await response.json();
            alert(err.detail || 'Erreur lors du changement de criticité');
        }
    } catch (e) {
        console.error('Erreur bascule criticité:', e);
        alert('Erreur réseau lors de la mise à jour.');
    }
}

/**
 * Supprime une machine de la supervision
 */
async function supprimerMachineSupervision(machineId, ip) {
    if (!confirm(`Confirmez-vous le retrait de la machine ${ip} de la supervision active ?`)) {
        return;
    }

    try {
        const response = await fetch(`http://localhost:8000/api/v1/supervision/machines/${machineId}`, {
            method: 'DELETE',
            headers: getAuthHeaders()
        });

        if (response.ok) {
            await chargerSupervision();
        } else {
            const err = await response.json();
            alert(err.detail || 'Erreur lors de la suppression');
        }
    } catch (e) {
        console.error('Erreur suppression machine:', e);
        alert('Erreur réseau lors de la suppression.');
    }
}

/**
 * Déclenche un sondage complet immédiat L3/L7 de toutes les machines
 */
async function declencherSondageManuel() {
    const btn = document.getElementById('btn-sonder-tout');
    const icon = btn?.querySelector('i');
    if (btn) btn.disabled = true;
    if (icon) icon.classList.add('fa-spin');

    try {
        const response = await fetch('http://localhost:8000/api/v1/supervision/sonder', {
            method: 'POST',
            headers: getAuthHeaders()
        });

        if (response.ok) {
            await chargerSupervision();
        } else {
            alert('Erreur lors du sondage des machines.');
        }
    } catch (e) {
        console.error('Erreur sondage:', e);
        alert('Impossible de joindre le serveur pour le sondage.');
    } finally {
        if (btn) btn.disabled = false;
        if (icon) icon.classList.remove('fa-spin');
    }
}

/**
 * Redirige vers la vue de Traçage avec l'IP pré-remplie
 */
function tracerDepuisDashboard(ip) {
    if (typeof afficherVue === 'function') {
        if (typeof mettreAJourMenu === 'function') {
            mettreAJourMenu('nav-tracing', 'TRAÇAGE & LOCALISATION');
        }
        afficherVue('view-tracing');
        const inputTarget = document.getElementById('input-target');
        if (inputTarget) {
            inputTarget.value = ip;
            inputTarget.focus();
            // Déclenchement automatique du traçage si la fonction existe
            const btnTracer = document.getElementById('btn-tracer');
            if (btnTracer) btnTracer.click();
        }
    }
}

/**
 * Ouvre la modal d'ajout d'équipement
 */
function ouvrirModalAjoutMachine() {
    const modal = document.getElementById('modal-ajouter-machine');
    if (modal) {
        modal.classList.remove('hidden');
        modal.classList.add('flex');
        document.getElementById('input-machine-nom')?.focus();
    }
}

/**
 * Ferme la modal d'ajout d'équipement
 */
function fermerModalAjoutMachine() {
    const modal = document.getElementById('modal-ajouter-machine');
    if (modal) {
        modal.classList.add('hidden');
        modal.classList.remove('flex');
        document.getElementById('form-ajouter-machine')?.reset();
        // Restaurer le port 80 par défaut
        const portIn = document.getElementById('input-machine-port');
        if (portIn) portIn.value = '80';
    }
}

// ═══════════════════════════════════════════════════════════════════
// INITIALISATION DES ÉCOUTEURS D'ÉVÉNEMENTS
// ═══════════════════════════════════════════════════════════════════

document.addEventListener('DOMContentLoaded', () => {
    // 1. Bouton ouverture modal ajout
    document.getElementById('btn-ouvrir-modal-ajout')?.addEventListener('click', ouvrirModalAjoutMachine);

    // 2. Boutons fermeture modal ajout
    document.getElementById('btn-fermer-modal-ajout')?.addEventListener('click', fermerModalAjoutMachine);
    document.getElementById('btn-annuler-modal-ajout')?.addEventListener('click', fermerModalAjoutMachine);

    // 3. Fermeture clic hors de la modal
    const modalAjout = document.getElementById('modal-ajouter-machine');
    modalAjout?.addEventListener('click', (e) => {
        if (e.target === modalAjout) fermerModalAjoutMachine();
    });

    // 4. Presets rapides de ports L7
    document.querySelectorAll('.btn-preset-port').forEach(btn => {
        btn.addEventListener('click', () => {
            const port = btn.dataset.port;
            const proto = btn.dataset.proto;
            const portInput = document.getElementById('input-machine-port');
            const protoInput = document.getElementById('input-machine-proto');
            if (portInput && port) portInput.value = port;
            if (protoInput && proto) protoInput.value = proto;
        });
    });

    // 5. Soumission du formulaire d'ajout
    const formAjout = document.getElementById('form-ajouter-machine');
    formAjout?.addEventListener('submit', async (e) => {
        e.preventDefault();

        const ip = document.getElementById('input-machine-ip')?.value?.trim();
        const nom = document.getElementById('input-machine-nom')?.value?.trim() || null;
        const portL7 = document.getElementById('input-machine-port')?.value?.trim() || '80';
        const protoL7 = document.getElementById('input-machine-proto')?.value || 'HTTP';
        const estCritique = document.getElementById('input-machine-critique')?.checked || false;

        if (!ip) {
            alert('Veuillez spécifier une adresse IP.');
            return;
        }

        const btnSubmit = document.getElementById('btn-soumettre-machine');
        if (btnSubmit) {
            btnSubmit.disabled = true;
            btnSubmit.innerHTML = '<i class="fa-solid fa-spinner fa-spin mr-1.5"></i> Test L3/L7 en cours...';
        }

        try {
            const response = await fetch('http://localhost:8000/api/v1/supervision/machines', {
                method: 'POST',
                headers: getAuthHeaders(),
                body: JSON.stringify({
                    ip: ip,
                    nom: nom,
                    port_l7: portL7,
                    protocole_l7: protoL7,
                    est_critique: estCritique
                })
            });

            const data = await response.json();

            if (response.ok) {
                fermerModalAjoutMachine();
                await chargerSupervision();
            } else {
                alert(data.detail || 'Erreur lors de l\'enregistrement de la machine.');
            }
        } catch (err) {
            console.error('Erreur ajout machine:', err);
            alert('Impossible de joindre le serveur.');
        } finally {
            if (btnSubmit) {
                btnSubmit.disabled = false;
                btnSubmit.innerHTML = '<i class="fa-solid fa-plus text-xs"></i> <span>Ajouter &amp; Sonder</span>';
            }
        }
    });

    // 6. Bouton Re-sonder tout
    document.getElementById('btn-sonder-tout')?.addEventListener('click', declencherSondageManuel);

    // 7. Boutons de filtres (Toutes, Critiques, Alertes)
    const btnFiltreTous = document.getElementById('filtre-tous');
    const btnFiltreCritiques = document.getElementById('filtre-critiques');
    const btnFiltreAlertes = document.getElementById('filtre-alertes');

    function changerFiltre(nouveauFiltre) {
        filtreSupervisionActif = nouveauFiltre;

        const boutons = [
            { el: btnFiltreTous, id: 'tous' },
            { el: btnFiltreCritiques, id: 'critiques' },
            { el: btnFiltreAlertes, id: 'alertes' }
        ];

        boutons.forEach(b => {
            if (!b.el) return;
            if (b.id === nouveauFiltre) {
                b.el.className = 'px-2.5 py-1 text-xs rounded font-medium text-white bg-primary/20 border border-primary/30 transition-all';
            } else {
                b.el.className = 'px-2.5 py-1 text-xs rounded font-medium text-gray-400 hover:text-white transition-all';
            }
        });

        rendreTableauSupervision();
    }

    btnFiltreTous?.addEventListener('click', () => changerFiltre('tous'));
    btnFiltreCritiques?.addEventListener('click', () => changerFiltre('critiques'));
    btnFiltreAlertes?.addEventListener('click', () => changerFiltre('alertes'));

    // 8. Charger la supervision au démarrage
    chargerSupervision();

    // 9. Rafraîchissement périodique toutes les 30 secondes en arrière-plan
    if (!timerAutoRefresh) {
        timerAutoRefresh = setInterval(() => {
            const dash = document.getElementById('view-dashboard');
            if (dash && dash.style.display !== 'none' && !dash.classList.contains('hidden')) {
                chargerSupervision();
            }
        }, 30000);
    }
});