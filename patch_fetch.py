import os

BASE_DIR = 'E:/projet mémoire/iplocator_light/IpLocator'
auth_js_path = os.path.join(BASE_DIR, 'interface', 'ressources', 'js', 'auth.js')

with open(auth_js_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Monkey patch fetch
monkey_patch = '''
// Monkey-patch global fetch to automatically inject the JWT token
const originalFetch = window.fetch;
window.fetch = async function() {
    let [resource, config] = arguments;
    if (typeof resource === 'string' && resource.startsWith('http://localhost:8000/api/v1/')) {
        const session = getSession();
        if (session && session.token) {
            config = config || {};
            config.headers = config.headers || {};
            config.headers['Authorization'] = 'Bearer ' + session.token;
        }
    }
    return originalFetch(resource, config);
};
'''

if 'const originalFetch = window.fetch;' not in content:
    content += "\n" + monkey_patch
    with open(auth_js_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Monkey-patched fetch in auth.js")
else:
    print("Already monkey-patched")

# Modif auth.js pour qu'il garde le token dans la session
# Session data is already saved whole which includes data.token, so this is fine.
