/**
 * auth.js — Module d'authentification RBAC ASECNA NET-TRACE
 * Gère la session, le login, la déconnexion et les droits d'accès.
 */

const AUTH_KEY = 'asecna_session';
const API_BASE = 'http://localhost:8000/api/v1';

// ──────────────────────────────────────────────
// Session Management
// ──────────────────────────────────────────────

function sauvegarderSession(data) {
    sessionStorage.setItem(AUTH_KEY, JSON.stringify(data));
}

function getSession() {
    const raw = sessionStorage.getItem(AUTH_KEY);
    return raw ? JSON.parse(raw) : null;
}

function getRole() {
    const session = getSession();
    return session ? session.role : null;
}

function getUser() {
    return getSession();
}

function isAdmin() {
    return getRole() === 'ADMIN';
}

function isOperateur() {
    return getRole() === 'OPERATEUR';
}

function deconnecter() {
    sessionStorage.removeItem(AUTH_KEY);
    window.location.href = 'login.html';
}

/**
 * À appeler au chargement de chaque page protégée (index.html).
 * Redirige vers login.html si aucune session active.
 */
function verifierSession() {
    const session = getSession();
    if (!session) {
        window.location.href = 'login.html';
        return null;
    }
    return session;
}

// ──────────────────────────────────────────────
// Login Function (appelée depuis login.html)
// ──────────────────────────────────────────────

async function login(identifiant, motDePasse, btnElement, msgElement) {
    const originalHTML = btnElement.innerHTML;
    btnElement.disabled = true;
    btnElement.innerHTML = `
        <svg class="animate-spin h-5 w-5 mx-auto" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
        </svg>`;
    if (msgElement) msgElement.textContent = '';

    try {
        const response = await fetch(`${API_BASE}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ identifiant, mot_de_passe: motDePasse })
        });

        const data = await response.json();

        if (response.ok) {
            sauvegarderSession(data);
            window.location.href = 'index.html';
        } else {
            if (msgElement) {
                msgElement.textContent = data.detail || 'Identifiants incorrects.';
                msgElement.classList.remove('hidden');
            }
            btnElement.disabled = false;
            btnElement.innerHTML = originalHTML;
        }
    } catch (err) {
        if (msgElement) {
            msgElement.textContent = 'Erreur de connexion au serveur API.';
            msgElement.classList.remove('hidden');
        }
        btnElement.disabled = false;
        btnElement.innerHTML = originalHTML;
    }
}

// ──────────────────────────────────────────────
// UI — Appliquer les restrictions RBAC
// ──────────────────────────────────────────────

function appliquerRestrictions() {
    const session = getSession();
    if (!session) return;

    // Mettre à jour le profil dans le sidebar
    const elNom = document.getElementById('profil-nom');
    const elRole = document.getElementById('profil-role');
    const elBadgeRole = document.getElementById('badge-role-header');

    if (elNom) elNom.textContent = session.nom;
    if (elRole) elRole.textContent = session.role;
    if (elBadgeRole) {
        elBadgeRole.textContent = session.role;
        elBadgeRole.className = session.role === 'ADMIN'
            ? 'text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 uppercase tracking-wider'
            : 'text-[10px] font-bold px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-400 border border-amber-500/30 uppercase tracking-wider';
    }

    // Si OPÉRATEUR : désactiver les boutons d'isolation
    if (session.role === 'OPERATEUR') {
        document.querySelectorAll('.btn-isolation').forEach(btn => {
            btn.disabled = true;
            btn.classList.add('opacity-50', 'cursor-not-allowed');
            btn.title = 'Action réservée aux Administrateurs NOC';
            // Remplacer le texte si le bouton a un label
            const label = btn.querySelector('.btn-label');
            if (label) label.textContent = 'Admin Requis';
        });
        // Cacher entièrement la section sécurité dans le nav
        const navSec = document.getElementById('nav-security');
        if (navSec) navSec.style.display = 'none';
    }
}
