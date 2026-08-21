// Initialisation des graphiques du Tableau de Bord (Dashboard NOC)
document.addEventListener('DOMContentLoaded', () => {
    initCharts();
});

function initCharts() {
    // Configuration globale Chart.js pour thème sombre
    Chart.defaults.color = '#9ca3af';
    Chart.defaults.borderColor = '#2A2F3D';
    Chart.defaults.font.family = "'Inter', sans-serif";

    // 1. Sparkline (Latence Moyenne) - Mini Chart Ligne
    const ctxSparkline = document.getElementById('sparkline-latency').getContext('2d');
    new Chart(ctxSparkline, {
        type: 'line',
        data: {
            labels: ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10'],
            datasets: [{
                data: [1.1, 1.2, 1.0, 1.5, 1.2, 1.1, 1.3, 1.2, 1.4, 1.2],
                borderColor: '#10B981', // emerald-500
                borderWidth: 2,
                pointRadius: 0,
                pointHoverRadius: 0,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false }, tooltip: { enabled: false } },
            scales: {
                x: { display: false },
                y: { display: false, min: 0, max: 2 }
            },
            interaction: { mode: null }
        }
    });

    // 2. Jauge Radiale (Capacité des Ports) - Doughnut
    const ctxPort = document.getElementById('chart-port-capacity').getContext('2d');
    new Chart(ctxPort, {
        type: 'doughnut',
        data: {
            labels: ['Actifs', 'Libres'],
            datasets: [{
                data: [164, 76],
                backgroundColor: ['#10B981', '#2A2F3D'],
                borderWidth: 0,
                borderRadius: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '80%',
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return ` ${context.label}: ${context.raw} ports`;
                        }
                    }
                }
            }
        }
    });

    // 3. Mini Area Chart (Bande Passante)
    const ctxBandwidth = document.getElementById('chart-bandwidth-mini').getContext('2d');
    
    // Création d'un dégradé pour la zone
    const gradientBand = ctxBandwidth.createLinearGradient(0, 0, 0, 100);
    gradientBand.addColorStop(0, 'rgba(16, 185, 129, 0.4)');
    gradientBand.addColorStop(1, 'rgba(16, 185, 129, 0)');

    new Chart(ctxBandwidth, {
        type: 'line',
        data: {
            labels: ['a', 'b', 'c', 'd', 'e', 'f', 'g'],
            datasets: [{
                data: [0.8, 1.2, 0.9, 1.5, 1.1, 1.6, 1.42],
                borderColor: '#10B981',
                backgroundColor: gradientBand,
                borderWidth: 2,
                fill: true,
                pointRadius: 0,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false }, tooltip: { enabled: false } },
            scales: {
                x: { display: false },
                y: { display: false, min: 0 }
            }
        }
    });

    // 4. Graphique Principal (Trafic Réseau ASECNA)
    const ctxMain = document.getElementById('chart-main-traffic').getContext('2d');
    
    const gradientIn = ctxMain.createLinearGradient(0, 0, 0, 400);
    gradientIn.addColorStop(0, 'rgba(16, 185, 129, 0.2)'); // emerald
    gradientIn.addColorStop(1, 'rgba(16, 185, 129, 0)');

    const gradientOut = ctxMain.createLinearGradient(0, 0, 0, 400);
    gradientOut.addColorStop(0, 'rgba(245, 158, 11, 0.2)'); // warning/orange
    gradientOut.addColorStop(1, 'rgba(245, 158, 11, 0)');

    new Chart(ctxMain, {
        type: 'line',
        data: {
            labels: ['00:00', '02:00', '04:00', '06:00', '08:00', '10:00', '12:00', '14:00', '16:00', '18:00', '20:00', '22:00'],
            datasets: [
                {
                    label: 'Trafic Entrant (IN) Gbps',
                    data: [1.2, 0.8, 0.5, 1.1, 2.5, 3.8, 4.2, 4.0, 3.5, 2.8, 1.9, 1.4],
                    borderColor: '#10B981',
                    backgroundColor: gradientIn,
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: '#1E222D',
                    pointBorderColor: '#10B981',
                    pointBorderWidth: 2,
                    pointRadius: 3,
                    pointHoverRadius: 5
                },
                {
                    label: 'Trafic Sortant (OUT) Gbps',
                    data: [0.9, 0.6, 0.4, 0.8, 1.8, 2.5, 3.1, 3.5, 2.9, 2.2, 1.5, 1.0],
                    borderColor: '#F59E0B',
                    backgroundColor: gradientOut,
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: '#1E222D',
                    pointBorderColor: '#F59E0B',
                    pointBorderWidth: 2,
                    pointRadius: 3,
                    pointHoverRadius: 5
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            plugins: {
                legend: {
                    position: 'top',
                    align: 'end',
                    labels: { boxWidth: 10, usePointStyle: true, pointStyle: 'circle' }
                },
                tooltip: {
                    backgroundColor: 'rgba(30, 34, 45, 0.9)',
                    titleColor: '#fff',
                    bodyColor: '#cbd5e1',
                    borderColor: '#2A2F3D',
                    borderWidth: 1,
                    padding: 10,
                    boxPadding: 4
                }
            },
            scales: {
                x: {
                    grid: { color: 'rgba(42, 47, 61, 0.5)', drawBorder: false }
                },
                y: {
                    grid: { color: 'rgba(42, 47, 61, 0.5)', drawBorder: false },
                    beginAtZero: true
                }
            }
        }
    });

    // 5. Bar Chart (Erreurs de Transmission)
    const ctxErrors = document.getElementById('chart-errors').getContext('2d');
    new Chart(ctxErrors, {
        type: 'bar',
        data: {
            labels: ['SW-CORE-1', 'SW-CORE-2', 'SW-ACC-TWR', 'SW-ACC-BGD', 'SW-ACC-ADM'],
            datasets: [{
                label: 'Erreurs CRC',
                data: [12, 5, 45, 8, 2],
                backgroundColor: '#EF4444', // danger
                borderRadius: 4,
                barThickness: 12
            }, {
                label: 'Paquets Perdus',
                data: [4, 2, 28, 3, 1],
                backgroundColor: '#F59E0B', // warning
                borderRadius: 4,
                barThickness: 12
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: true, position: 'top', labels: { boxWidth: 10, usePointStyle: true, pointStyle: 'circle'} }
            },
            scales: {
                x: {
                    grid: { display: false },
                    stacked: true
                },
                y: {
                    grid: { color: 'rgba(42, 47, 61, 0.5)' },
                    stacked: true,
                    beginAtZero: true
                }
            }
        }
    });
}
