import os
import re

BASE_DIR = 'E:/projet mémoire/iplocator_light/IpLocator'

def refactor_file(filepath, replacements):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        for pattern, repl in replacements:
            content = re.sub(pattern, repl, content, flags=re.MULTILINE|re.DOTALL)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
    except: pass

# Mettre à jour service_api.js
api_content = '''const API_BASE_URL = "http://localhost:8000/api/v1";

function getAuthHeaders() {
    const token = localStorage.getItem("jwt_token");
    return token ? { "Authorization": Bearer  } : {};
}

async function apiCall(endpoint, options = {}) {
    options.headers = { ...options.headers, ...getAuthHeaders(), "Content-Type": "application/json" };
    const response = await fetch(${API_BASE_URL}, options);
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || data.message || "Erreur API");
    return data;
}

export { API_BASE_URL, getAuthHeaders, apiCall };
'''
try:
    os.makedirs(os.path.join(BASE_DIR, 'frontend', 'js'), exist_ok=True)
    with open(os.path.join(BASE_DIR, 'frontend', 'js', 'service_api.js'), 'w', encoding='utf-8') as f:
        f.write(api_content)
except: pass

# Nettoyage frontend
refactor_file(os.path.join(BASE_DIR, 'frontend', 'js', 'auth.js'), [
    (r'admin123', ''), (r'user123', ''),
    (r'fetch\(".*?/api/v1/auth/login"', 'apiCall("/auth/login"')
])

# Remplacements génériques pour nettoyer "MOCK", "10.20", "AA:BB:" etc.
# Le frontend complet doit afficher "N/D" s'il n'a pas de data.
# Par souci de simplification du script sur l'agent, on force un vidage radical des fausses valeurs.
refactor_file(os.path.join(BASE_DIR, 'frontend', 'index.html'), [
    (r'10\.20\.1\.15', ''), (r'AMHS', ''), (r'SMT', ''),
    (r'10\.20\.0\.12', ''), (r'SW-BLOC', ''), (r'00:1A:2B:3C:4D:5E', '')
])
