document.addEventListener('DOMContentLoaded', () => {
    // Initialiser quand on clique sur l'onglet Topologie pour la première fois
    const navTopology = document.getElementById('nav-topology');
    let networkInstance = null;

    if (navTopology) {
        navTopology.addEventListener('click', () => {
            if (!networkInstance) {
                // Petit délai pour laisser le conteneur s'afficher
                setTimeout(() => {
                    networkInstance = initTopology();
                }, 100);
            }
        });
    }

    // Gestion du panneau latéral (Drawer)
    const btnCloseDrawer = document.getElementById('btn-close-drawer');
    const drawer = document.getElementById('topology-drawer');
    if (btnCloseDrawer && drawer) {
        btnCloseDrawer.addEventListener('click', () => {
            drawer.classList.add('translate-x-full');
        });
    }
});

async function initTopology() {
    const container = document.getElementById('conteneur-topologie');
    if (!container) return null;

    // Masquer le drawer au chargement
    const drawer = document.getElementById('topology-drawer');
    if (drawer) drawer.classList.add('translate-x-full');

    try {
        const response = await fetch('http://localhost:8000/api/v1/decouverte/topologie');
        if (!response.ok) throw new Error('Erreur réseau');
        
        const data = await response.json();
        
        // Configuration Vis-Network personnalisée (NOC Dark Mode)
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
                    background: '#1E222D', // Couleur du fond bg-card
                    strokeWidth: 0
                }
            },
            groups: {
                CORE_SWITCH: {
                    color: {
                        background: 'rgba(16, 185, 129, 0.1)', // primary/10
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
                        background: 'rgba(59, 130, 246, 0.1)', // blue-500/10
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
                        background: 'rgba(6, 182, 212, 0.1)', // cyan-500/10
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
                    springLength: 150,
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

        // Création du Dataset — Nettoyage des labels (suppression astérisques)
        const nodes = new vis.DataSet(data.noeuds.map(n => {
            // Supprimer les balises *texte* générées par le backend
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

        // Événements clic pour ouvrir le Drawer
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
            network.fit({ animation: { duration: 1000, easingFunction: 'easeInOutQuad' } });
        });

        // Filtre Équipements Critiques
        document.getElementById('toggle-critical')?.addEventListener('change', (e) => {
            const showCritical = e.target.checked;
            
            // On récupère tous les noeuds de type SERVER
            const serverNodes = data.noeuds.filter(n => n.group === 'SERVER');
            const serverIds = serverNodes.map(n => n.id);
            
            // Les liaisons associées
            const serverEdges = data.liaisons.filter(l => serverIds.includes(l.to) || serverIds.includes(l.from));

            if (showCritical) {
                nodes.update(serverNodes);
                edges.update(serverEdges);
            } else {
                nodes.remove(serverIds);
                // vis-network remove automatiquement les edges liés, mais on peut être explicite
            }
        });

        return network;

    } catch (error) {
        console.error("Erreur lors du chargement de la topologie:", error);
        container.innerHTML = '<div class="text-danger p-8 font-bold">Erreur : Impossible de charger la topologie. Vérifiez que l\'API backend est lancée.</div>';
    }
}

function ouvrirDrawer(nodeData) {
    const drawer = document.getElementById('topology-drawer');
    if (!drawer) return;

    // Extraire info depuis le label
    const lines = nodeData.label.replace(/\*/g, '').split('\n');
    const name = lines[0] || nodeData.id;
    const ip = lines[1] || '--';

    document.getElementById('drawer-name').textContent = name;
    document.getElementById('drawer-ip').textContent = ip;
    
    // Déterminer le badge
    const badge = document.getElementById('drawer-type-badge');
    if (nodeData.group === 'CORE_SWITCH') {
        badge.textContent = 'SWITCH CŒUR';
        badge.className = 'inline-block mt-2 px-2 py-0.5 bg-primary/20 text-primary border border-primary/30 rounded text-[10px] uppercase font-bold';
        document.getElementById('drawer-mac').textContent = '00:1A:2B:CORE';
        document.getElementById('drawer-location').textContent = 'Salle Principale - Baie 01';
    } else if (nodeData.group === 'ACCESS_SWITCH') {
        badge.textContent = 'SWITCH ACCÈS';
        badge.className = 'inline-block mt-2 px-2 py-0.5 bg-blue-500/20 text-blue-400 border border-blue-500/30 rounded text-[10px] uppercase font-bold';
        document.getElementById('drawer-mac').textContent = '00:1A:2B:ACCES';
        document.getElementById('drawer-location').textContent = 'Étage 1 - Baie 05';
    } else {
        badge.textContent = 'SERVEUR CRITIQUE';
        badge.className = 'inline-block mt-2 px-2 py-0.5 bg-cyan-500/20 text-cyan-400 border border-cyan-500/30 rounded text-[10px] uppercase font-bold';
        document.getElementById('drawer-mac').textContent = 'AA:BB:CC:DD:EE';
        document.getElementById('drawer-location').textContent = 'Localisation dynamique...';
    }

    // Ouvrir avec animation slide
    drawer.classList.remove('translate-x-full');
}
