document.addEventListener('DOMContentLoaded', () => {
    // Navigation handling
    const navLinks = {
        'nav-dashboard': 'view-dashboard',
        'nav-tracing': 'view-tracing',
        'nav-topology': 'view-topology'
    };

    const views = Object.values(navLinks);
    
    // Titres de page correspondants
    const pageTitles = {
        'nav-dashboard': 'Vue Globale du Réseau',
        'nav-tracing': 'Recherche et Traçage',
        'nav-topology': 'Cartographie Active'
    };

    for (const [navId, viewId] of Object.entries(navLinks)) {
        const navEl = document.getElementById(navId);
        if (navEl) {
            navEl.addEventListener('click', (e) => {
                e.preventDefault();
                
                // Masquer toutes les vues
                views.forEach(v => {
                    const el = document.getElementById(v);
                    if (el) el.classList.add('hidden');
                });
                
                // Réinitialiser les styles de nav
                Object.keys(navLinks).forEach(nId => {
                    const el = document.getElementById(nId);
                    if (el) {
                        el.classList.remove('bg-primary/10', 'text-primary');
                        el.classList.add('text-gray-400', 'hover:bg-white/5', 'hover:text-white');
                        const icon = el.querySelector('i');
                        if (icon) {
                            icon.classList.add('group-hover:text-primary');
                        }
                    }
                });

                // Afficher la vue ciblée
                const targetView = document.getElementById(viewId);
                if (targetView) targetView.classList.remove('hidden');
                
                // Mettre à jour le style du lien actif
                navEl.classList.remove('text-gray-400', 'hover:bg-white/5', 'hover:text-white');
                navEl.classList.add('bg-primary/10', 'text-primary');
                const activeIcon = navEl.querySelector('i');
                if (activeIcon) {
                    activeIcon.classList.remove('group-hover:text-primary');
                }
                
                // Mettre à jour le titre
                document.getElementById('page-title').textContent = pageTitles[navId];

                // Actions spécifiques lors de l'activation d'une vue
                if (viewId === 'view-topology' && !network) {
                    // Initialiser la topologie seulement lors de la première ouverture de l'onglet
                    initTopology();
                }
            });
        }
    }

    // Initialisation au démarrage
    initDashboard();
});
