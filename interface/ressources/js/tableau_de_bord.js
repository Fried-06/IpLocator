/**
 * tableau_de_bord.js — Gestion des graphiques NOC (Chart.js)
 */

let trafficChartInstance = null;
let portsChartInstance = null;

function initDashboardCharts() {
    // 1. Graphique du Trafic (Ligne / Courbe)
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
                plugins: {
                    legend: { display: false }
                },
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

    // 2. Graphique Donut (Répartition des Ports)
    const ctxPorts = document.getElementById('chart-ports');
    if (ctxPorts && !portsChartInstance) {
        portsChartInstance = new Chart(ctxPorts, {
            type: 'doughnut',
            data: {
                labels: ['Actifs', 'Erreurs', 'Inactifs'],
                datasets: [{
                    data: [47, 3, 2],
                    backgroundColor: ['#10B981', '#F59E0B', '#EF4444'],
                    borderColor: '#111827',
                    borderWidth: 3
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '75%',
                plugins: {
                    legend: { display: false }
                }
            }
        });
    }
}

// Initialisation automatique au chargement si l'élément est déjà visible
document.addEventListener('DOMContentLoaded', () => {
    const dash = document.getElementById('view-dashboard');
    if (dash && dash.style.display !== 'none' && !dash.classList.contains('hidden')) {
        initDashboardCharts();
    }
});