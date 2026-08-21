document.addEventListener('DOMContentLoaded', () => {
    const session  = typeof getSession === 'function' ? getSession() : null;
    const estAdmin = session && session.role === 'ADMIN';

    // RBAC : désactiver l'isolation pour les OPÉRATEURS
    if (!estAdmin) {
        document.querySelectorAll('.btn-isolation').forEach(btn => {
            btn.disabled = true;
            btn.classList.add('opacity-40', 'cursor-not-allowed');
            btn.title = 'Action réservée aux Administrateurs NOC';
            const label = btn.querySelector('.btn-label');
            if (label) label.textContent = 'Admin Requis';
        });
    }

    const btnDetect            = document.getElementById('sec-btn-detect');
    const detectResult         = document.getElementById('sec-detection-result');
    const formSecurity         = document.getElementById('form-security');
    const modal                = document.getElementById('modal-security');
    const modalContent         = document.getElementById('modal-security-content');
    const btnCancelModal       = document.getElementById('btn-cancel-isolation');
    const formConfirmIsolation = document.getElementById('form-confirm-isolation');
    const modalMessage         = document.getElementById('modal-sec-message');
    const inputTarget          = document.getElementById('sec-input-target');
    const inputReason          = document.getElementById('sec-input-reason');
    const inputPassword        = document.getElementById('sec-input-password');

    let targetInfo = { equipement: '', switchNom: 'SW-BLOC-TECH-01', port: 'Gi1/0/14' };

    btnDetect?.addEventListener('click', () => {
        const v = inputTarget?.value?.trim();
        if (!v) return;
        targetInfo.equipement = v;
        if (detectResult) {
            detectResult.innerHTML = `<i class="fa-solid fa-circle-check mr-1"></i>Détecté : <strong class="text-white">${targetInfo.switchNom}</strong> · Port <strong style="color:#fbbf24;">${targetInfo.port}</strong>`;
            detectResult.classList.remove('hidden');
        }
    });

    formSecurity?.addEventListener('submit', e => {
        e.preventDefault();
        if (!estAdmin) return;
        targetInfo.equipement = inputTarget?.value?.trim() || '';
        if (modalMessage) modalMessage.innerHTML = `Couper la liaison de <strong class="text-white">${targetInfo.equipement}</strong> sur <strong class="text-white">${targetInfo.switchNom}</strong> (Port <span style="color:#fbbf24;font-family:monospace">${targetInfo.port}</span>).`;
        modal?.classList.remove('hidden'); modal?.classList.add('flex');
        inputPassword && setTimeout(() => inputPassword.focus(), 300);
    });

    btnCancelModal?.addEventListener('click', () => { modal?.classList.add('hidden'); modal?.classList.remove('flex'); });
    modal?.addEventListener('click', e => { if (e.target === modal) { modal.classList.add('hidden'); modal.classList.remove('flex'); } });

    formConfirmIsolation?.addEventListener('submit', async e => {
        e.preventDefault();
        const btn = document.getElementById('btn-confirm-isolation');
        btn.disabled = true;
        try {
            const rep = await fetch('http://localhost:8000/api/v1/securite/isoler', {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ ip_equipement: targetInfo.equipement, raison: inputReason?.value, mot_de_passe_admin: inputPassword?.value })
            });
            const data = await rep.json();
            if (rep.ok) {
                ajouterLigneAudit(data.horodatage, targetInfo.equipement, `${targetInfo.switchNom} · ${targetInfo.port}`, inputReason?.value, targetInfo);
                modal?.classList.add('hidden'); modal?.classList.remove('flex');
                formSecurity?.reset(); detectResult?.classList.add('hidden');
            } else { alert(data.detail || 'Erreur.'); }
        } catch { alert('Erreur de connexion API.'); }
        finally { btn.disabled = false; }
    });

    function ajouterLigneAudit(ts, cible, acces, motif, info) {
        const tbody = document.getElementById('audit-log-body');
        document.getElementById('empty-log-row')?.remove();
        const id = Date.now(), tr = document.createElement('tr');
        tr.innerHTML = `<td class="py-3 px-4 font-mono text-[10px] text-gray-500">${ts}</td><td class="py-3 px-4 text-xs text-white">${cible}</td><td class="py-3 px-4 font-mono text-[10px] text-gray-400">${acces}</td><td class="py-3 px-4 text-[10px] text-gray-500">${motif}</td><td class="py-3 px-4 text-center" id="sc-${id}"><span style="background:rgba(239,68,68,0.1);color:#f87171;border:1px solid rgba(239,68,68,0.3)" class="px-2 py-0.5 rounded text-[9px] font-bold uppercase font-mono">ISOLÉ</span></td><td class="py-3 px-4 text-right" id="ac-${id}"><button class="btn-restaurer flex items-center gap-1 ml-auto px-3 py-1.5 rounded text-[10px] font-semibold" style="background:#0F172A;border:1px solid rgba(16,185,129,0.3);color:#10b981;"><i class="fa-solid fa-plug-circle-check text-[9px]"></i> Restaurer</button></td>`;
        tbody.insertBefore(tr, tbody.firstChild);
        tr.querySelector('.btn-restaurer').addEventListener('click', async () => {
            const pwd = prompt('Mot de passe Administrateur NOC :');
            if (!pwd) return;
            const rep = await fetch('http://localhost:8000/api/v1/securite/restaurer', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ip_equipement:info.equipement,raison:'Restauration',mot_de_passe_admin:pwd}) });
            const data = await rep.json();
            if (rep.ok) {
                document.getElementById(`sc-${id}`).innerHTML = `<span style="background:rgba(16,185,129,0.1);color:#10b981;border:1px solid rgba(16,185,129,0.3)" class="px-2 py-0.5 rounded text-[9px] font-bold uppercase font-mono">RESTAURÉ</span>`;
                document.getElementById(`ac-${id}`).innerHTML = `<span class="font-mono text-[9px] text-gray-600">${data.horodatage}</span>`;
            }
        });
    }
});