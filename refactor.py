import os
import re

# Chemin de base
BASE_DIR = 'E:/projet mémoire/iplocator_light/IpLocator'

def refactor_file(filepath, replacements):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        new_content = content
        for pattern, repl in replacements:
            new_content = re.sub(pattern, repl, new_content, flags=re.MULTILINE|re.DOTALL)
            
        if content != new_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f'Modifié: {filepath}')
    except Exception as e:
        print(f'Erreur {filepath}: {e}')

def remove_file(filepath):
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
            print(f'Supprimé: {filepath}')
    except Exception as e:
        print(f'Erreur suppr {filepath}: {e}')

# Scripts frontend
refactor_file(os.path.join(BASE_DIR, 'frontend', 'js', 'tableau_de_bord.js'), [
    (r'const dataIn = \[.*?\];', 'const dataIn = [];'),
    (r'const dataOut = \[.*?\];', 'const dataOut = [];'),
    (r'data: \[47, 3, 2\]', 'data: []'),
])

# Paramètres backend
refactor_file(os.path.join(BASE_DIR, 'serveur', 'config', 'configuration.py'), [
    (r'MOCK_MODE\s*=\s*True', ''),
    (r'DEFAULT_GATEWAY\s*=\s*.*', ''),
])

remove_file(os.path.join(BASE_DIR, 'serveur', 'config', 'settings.json'))

print('Refactor partiel effectué (script simplifié pour l\'exemple).')
