document.addEventListener('DOMContentLoaded', () => {
    const navTopology = document.getElementById('nav-topology');
    let networkInstance = null;

    // 1. Initialiser ou rafraîchir à chaque clic sur l'onglet Topologie
    if (navTopology) {
        navTopology.addEventListener('click', () => {
            setTimeout(async () => {
                networkInstance = await initTopology();
            }, 100);
        });
    }

    // 2. Bouton "Ré-explorer" dans la barre d'outils
    const btnReExplore = document.getElementById('btn-re-explore');
    if (btnReExplore) {
        btnReExplore.addEventListener('click', async () => {
            const originalHtml = btnReExplore.innerHTML;
            btnReExplore.innerHTML = '<i class="fa-solid fa-arrows-rotate fa-spin"></i> Exploration...';
            btnReExplore.disabled = true;
            try {
                networkInstance = await initTopology();
            } finally {
                btnReExplore.innerHTML = originalHtml;
                btnReExplore.disabled = false;
            }
        });
    }

    // 3. Gestion du panneau latéral (Drawer)
    const btnCloseDrawer = document.getElementById('btn-close-drawer');
    const drawer = document.getElementById('topology-drawer');
    if (btnCloseDrawer && drawer) {
        btnCloseDrawer.addEventListener('click', () => {
            drawer.classList.add('translate-x-full');
        });
    }

    // 4. Action "Tracer cet équipement" depuis le drawer
    const drawerTraceBtn = drawer ? drawer.querySelector('button.btn-primary-glow') : null;
    if (drawerTraceBtn) {
        drawerTraceBtn.addEventListener('click', () => {
            const targetIp = document.getElementById('drawer-ip')?.textContent?.trim();
            if (targetIp && targetIp !== '--') {
                drawer.classList.add('translate-x-full');
                const navTracing = document.getElementById('nav-tracing');
                if (navTracing) navTracing.click();
                const inputTarget = document.getElementById('input-target');
                if (inputTarget) {
                    inputTarget.value = targetIp;
                    const formTracing = document.getElementById('form-tracing');
                    if (formTracing) {
                        formTracing.dispatchEvent(new Event('submit'));
                    }
                }
            }
        });
    }
});

async function initTopology() {
    const container = document.getElementById('conteneur-topologie');
    if (!container) return null;

    const drawer = document.getElementById('topology-drawer');
    if (drawer) drawer.classList.add('translate-x-full');

    try {
        const response = await fetch('http://localhost:8000/api/v1/decouverte/topologie');
        if (!response.ok) throw new Error('Erreur réseau');
        
        const data = await response.json();
        
        const options = {
            nodes: {
                borderWidth: 2,
                borderWidthSelected: 4,
                font: {
                    color: '#e5e7eb',
                    face: 'Inter',
                    size: 12,
                    bold: { color: '#ffffff' }
                },
                shadow: {
                    enabled: true,
                    color: 'rgba(0,0,0,0.5)',
                    size: 10,
                    x: 5,
                    y: 5
                }
            },
            edges: {
                width: 2,
                smooth: {
                    type: 'continuous'
                },
                font: {
                    color: '#9ca3af',
                    size: 10,
                    background: '#1E222D',
                    strokeWidth: 0
                }
            },
            groups: {
                CORE_SWITCH: {
                    color: {
                        background: 'rgba(16, 185, 129, 0.1)',
                        border: '#10B981',
                        highlight: {
                            background: 'rgba(16, 185, 129, 0.3)',
                            border: '#10B981'
                        }
                    },
                    shape: 'box',
                    margin: 10,
                    font: { size: 14, multi: true, bold: 'true' }
                },
                ACCESS_SWITCH: {
                    color: {
                        background: 'rgba(59, 130, 246, 0.1)',
                        border: '#3B82F6',
                        highlight: {
                            background: 'rgba(59, 130, 246, 0.3)',
                            border: '#3B82F6'
                        }
                    },
                    shape: 'box',
                    margin: 8
                },
                SERVER: {
                    color: {
                        background: 'rgba(6, 182, 212, 0.1)',
                        border: '#06B6D4',
                        highlight: {
                            background: 'rgba(6, 182, 212, 0.3)',
                            border: '#06B6D4'
                        }
                    },
                    shape: 'ellipse',
                    font: { size: 11 }
                }
            },
            physics: {
                enabled: true,
                barnesHut: {
                    gravitationalConstant: -2000,
                    centralGravity: 0.3,
                    springLength: 160,
                    springConstant: 0.04,
                    damping: 0.09
                }
            },
            interaction: {
                hover: true,
                tooltipDelay: 200,
                zoomView: true,
                dragView: true
            }
        };

        const nodes = new vis.DataSet(data.noeuds.map(n => {
            if (n.label) {
                n.label = n.label.replace(/\*/g, '');
            }
            return n;
        }));
        
        const edges = new vis.DataSet(data.liaisons);

        const networkData = {
            nodes: nodes,
            edges: edges
        };

        const network = new vis.Network(container, networkData, options);

        network.on("click", function (params) {
            if (params.nodes.length > 0) {
                const nodeId = params.nodes[0];
                const nodeData = nodes.get(nodeId);
                ouvrirDrawer(nodeData);
            } else {
                if (drawer) drawer.classList.add('translate-x-full');
            }
        });

        // Bouton Recentrer
        document.getElementById('btn-center-view')?.addEventListener('click', () => {
            network.fit({ animation: { duration: 800, easingFunction: 'easeInOutQuad' } });
        });

        // Filtre Équipements Critiques
        document.getElementById('toggle-critical')?.addEventListener('change', (e) => {
            const showCritical = e.target.checked;
            const serverNodes = data.noeuds.filter(n => n.group === 'SERVER');
            const serverIds = serverNodes.map(n => n.id);

            if (showCritical) {
                nodes.update(serverNodes);
            } else {
                nodes.remove(serverIds);
            }
        });

        return network;

    } catch (error) {
        console.error("Erreur lors du chargement de la topologie:", error);
        container.innerHTML = '<div class="text-danger p-8 font-bold text-center">Erreur : Impossible de charger la topologie réseau.</div>';
        return null;
    }
}

function ouvrirDrawer(nodeData) {
    const drawer = document.getElementById('topology-drawer');
    if (!drawer || !nodeData) return;

    const lines = (nodeData.label || '').replace(/\*/g, '').split('\n');
    const name = lines[0] || nodeData.id;
    const ip = nodeData.ip || lines[1] || '--';

    document.getElementById('drawer-name').textContent = name;
    document.getElementById('drawer-ip').textContent = ip;
    document.getElementById('drawer-mac').textContent = nodeData.mac || '--';

    const badge = document.getElementById('drawer-type-badge');
    const locationEl = document.getElementById('drawer-location');

    if (nodeData.group === 'CORE_SWITCH') {
        badge.textContent = 'SWITCH CŒUR';
        badge.className = 'inline-block mt-2 px-2 py-0.5 bg-primary/20 text-primary border border-primary/30 rounded text-[10px] uppercase font-bold';
        if (locationEl) locationEl.textContent = 'Salle Serveurs / Cœur de Réseau';
    } else if (nodeData.group === 'ACCESS_SWITCH') {
        badge.textContent = 'SWITCH ACCÈS';
        badge.className = 'inline-block mt-2 px-2 py-0.5 bg-blue-500/20 text-blue-400 border border-blue-500/30 rounded text-[10px] uppercase font-bold';
        if (locationEl) locationEl.textContent = 'Baie de Brassage - N/D';
    } else {
        badge.textContent = 'HÔTE CONNECTÉ';
        badge.className = 'inline-block mt-2 px-2 py-0.5 bg-cyan-500/20 text-cyan-400 border border-cyan-500/30 rounded text-[10px] uppercase font-bold';
        const portStr = nodeData.port ? `Port : ${nodeData.port}` : '';
        const vlanStr = nodeData.vlan ? ` (${nodeData.vlan})` : '';
        const switchStr = nodeData.switch ? ` | Switch : ${nodeData.switch}` : '';
        if (locationEl) locationEl.textContent = `${portStr}${vlanStr}${switchStr}` || 'Localisation dynamique';
    }

    drawer.classList.remove('translate-x-full');
}
