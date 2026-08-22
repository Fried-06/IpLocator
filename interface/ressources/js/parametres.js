/**
 * parametres.js — Gestion de la configuration réseau dynamique (Live & Mock)
 */

document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('form-settings');
    const selectVersion = document.getElementById('setting-snmp-version');
    const containerV2 = document.getElementById('snmp-v2c-fields');
    const containerV3 = document.getElementById('snmp-v3-fields');
    const btnTest = document.getElementById('btn-test-snmp');
    const testResult = document.getElementById('snmp-test-result');

    // 1. Bascule dynamique SNMP v2c / v3
    selectVersion?.addEventListener('change', () => {
        if (selectVersion.value === 'v2c') {
            containerV2?.classList.remove('hidden');
            containerV3?.classList.add('hidden');
        } else {
            containerV2?.classList.add('hidden');
            containerV3?.classList.remove('hidden');
        }
    });

    // 2. Charger les paramètres existants depuis l'API
    chargerParametres();

    // 3. Tester la connexion SNMP
    btnTest?.addEventListener('click', async () => {
        const ip = document.getElementById('setting-core-ip').value.trim();
        const version = selectVersion.value;
        const community = document.getElementById('setting-snmp-community').value.trim();

        if (!ip) {
            alert("Veuillez renseigner l'adresse IP du switch cœur.");
            return;
        }

        const originalText = btnTest.innerHTML;
        btnTest.disabled = true;
        btnTest.innerHTML = '<i class="fa-solid fa-spinner fa-spin mr-1"></i> Test en cours...';
        testResult?.classList.add('hidden');

        const payload = {
            ip: ip,
            version: version,
            community: community,
            v3_user: document.getElementById('setting-snmp-v3-user')?.value || "",
            v3_auth_key: document.getElementById('setting-snmp-v3-auth-key')?.value || "",
            v3_priv_key: document.getElementById('setting-snmp-v3-priv-key')?.value || "",
            v3_auth_proto: document.getElementById('setting-snmp-v3-auth-proto')?.value || "SHA",
            v3_priv_proto: document.getElementById('setting-snmp-v3-priv-proto')?.value || "AES"
        };

        try {
            const resp = await fetch('http://localhost:8000/api/v1/parametres/tester', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const data = await resp.json();

            testResult.classList.remove('hidden');
            if (resp.ok && data.succes) {
                testResult.className = "p-3 rounded-lg text-xs bg-emerald-500/10 border border-emerald-500/30 text-emerald-400";
                testResult.innerHTML = `
                    <div class="flex items-center gap-2 font-bold mb-1">
                        <i class="fa-solid fa-circle-check"></i> ${data.message}
                    </div>
                    <div class="font-mono text-[11px] text-gray-300">
                        Nœud: <strong>${data.sysName}</strong> | Latence: ${data.latence_ms}ms<br>
                        Descr: ${data.sysDescr}
                    </div>
                `;
            } else {
                testResult.className = "p-3 rounded-lg text-xs bg-danger/10 border border-danger/30 text-danger";
                testResult.innerHTML = `<i class="fa-solid fa-circle-xmark mr-1"></i> ${data.detail || data.message || "Échec de connexion SNMP"}`;
            }
        } catch (e) {
            testResult.classList.remove('hidden');
            testResult.className = "p-3 rounded-lg text-xs bg-danger/10 border border-danger/30 text-danger";
            testResult.innerHTML = `<i class="fa-solid fa-triangle-exclamation mr-1"></i> Erreur lors de l'appel au serveur API.`;
        } finally {
            btnTest.disabled = false;
            btnTest.innerHTML = originalText;
        }
    });

    // 4. Enregistrer les paramètres
    form?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const submitBtn = document.getElementById('btn-save-settings');
        const origBtnText = submitBtn.innerHTML;
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin mr-1"></i> Enregistrement...';

        const payload = {
            mode: document.getElementById('setting-mode').value,
            core_switch_ip: document.getElementById('setting-core-ip').value.trim(),
            core_switch_brand: document.getElementById('setting-core-brand').value,
            snmp_version: selectVersion.value,
            snmp_community: document.getElementById('setting-snmp-community').value.trim(),
            snmp_v3_user: document.getElementById('setting-snmp-v3-user').value.trim(),
            snmp_v3_auth_key: document.getElementById('setting-snmp-v3-auth-key').value,
            snmp_v3_priv_key: document.getElementById('setting-snmp-v3-priv-key').value,
            snmp_v3_auth_proto: document.getElementById('setting-snmp-v3-auth-proto').value,
            snmp_v3_priv_proto: document.getElementById('setting-snmp-v3-priv-proto').value,
            ssh_username: document.getElementById('setting-ssh-user').value.trim(),
            ssh_password: document.getElementById('setting-ssh-pwd').value,
            theme: document.getElementById('setting-theme').value,
            custom_logo_path: document.getElementById('setting-logo-path').value.trim()
        };

        try {
            const resp = await fetch('http://localhost:8000/api/v1/parametres', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            if (resp.ok) {
                afficherToastParam("Paramètres réseau et SNMP enregistrés avec succès !", "success");
            } else {
                afficherToastParam("Erreur lors de l'enregistrement.", "error");
            }
        } catch (e) {
            afficherToastParam("Impossible de joindre le serveur API.", "error");
        } finally {
            submitBtn.disabled = false;
            submitBtn.innerHTML = origBtnText;
        }
    });
});

async function chargerParametres() {
    try {
        const resp = await fetch('http://localhost:8000/api/v1/parametres');
        if (!resp.ok) return;
        const data = await resp.json();

        if (document.getElementById('setting-mode')) document.getElementById('setting-mode').value = data.mode || "MOCK";
        if (document.getElementById('setting-core-ip')) document.getElementById('setting-core-ip').value = data.core_switch_ip || "10.20.0.1";
        if (document.getElementById('setting-core-brand')) document.getElementById('setting-core-brand').value = data.core_switch_brand || "Cisco";
        
        const selVer = document.getElementById('setting-snmp-version');
        if (selVer) {
            selVer.value = data.snmp_version || "v2c";
            selVer.dispatchEvent(new Event('change'));
        }

        if (document.getElementById('setting-snmp-community')) document.getElementById('setting-snmp-community').value = data.snmp_community || "public";
        if (document.getElementById('setting-snmp-v3-user')) document.getElementById('setting-snmp-v3-user').value = data.snmp_v3_user || "";
        if (document.getElementById('setting-snmp-v3-auth-key')) document.getElementById('setting-snmp-v3-auth-key').value = data.snmp_v3_auth_key || "";
        if (document.getElementById('setting-snmp-v3-priv-key')) document.getElementById('setting-snmp-v3-priv-key').value = data.snmp_v3_priv_key || "";
        if (document.getElementById('setting-snmp-v3-auth-proto')) document.getElementById('setting-snmp-v3-auth-proto').value = data.snmp_v3_auth_proto || "SHA";
        if (document.getElementById('setting-snmp-v3-priv-proto')) document.getElementById('setting-snmp-v3-priv-proto').value = data.snmp_v3_priv_proto || "AES";
        if (document.getElementById('setting-ssh-user')) document.getElementById('setting-ssh-user').value = data.ssh_username || "";
        if (document.getElementById('setting-ssh-pwd')) document.getElementById('setting-ssh-pwd').value = data.ssh_password || "";
        if (document.getElementById('setting-theme')) document.getElementById('setting-theme').value = data.theme || "Dark NOC";
        if (document.getElementById('setting-logo-path')) document.getElementById('setting-logo-path').value = data.custom_logo_path || "../image/Logo_ASECNA.png";

    } catch (e) {
        console.warn("Impossible de charger les paramètres réseau depuis l'API.");
    }
}

function afficherToastParam(message, type = 'success') {
    const toast = document.createElement('div');
    const ok = type === 'success';
    toast.style.cssText = `
        position:fixed;bottom:24px;right:24px;z-index:9999;
        padding:12px 18px;border-radius:10px;font-size:13px;font-weight:500;
        display:flex;align-items:center;gap:10px;
        background:${ok ? 'rgba(16,185,129,0.15)' : 'rgba(239,68,68,0.15)'};
        border:1px solid ${ok ? 'rgba(16,185,129,0.4)' : 'rgba(239,68,68,0.4)'};
        color:${ok ? '#10b981' : '#f87171'};
        box-shadow:0 8px 24px rgba(0,0,0,0.5);
    `;
    toast.innerHTML = `<i class="fa-solid fa-${ok ? 'circle-check' : 'triangle-exclamation'}"></i> ${message}`;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 4000);
}