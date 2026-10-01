import os
import re

BASE_DIR = 'E:/projet mémoire/iplocator_light/IpLocator'

def replace_in_files(directory, replacements):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(('.js', '.html')):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    original = content
                    for pat, repl in replacements:
                        content = re.sub(pat, repl, content, flags=re.IGNORECASE)
                    if content != original:
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(content)
                        print(f"Modifié: {filepath}")
                except: pass

replacements = [
    (r'admin123', ''), (r'user123', ''), (r'Ousmane', 'N/D'), (r'Koffi', 'N/D'),
    (r'10\.20\.1\.15', ''), (r'10\.20\.0\.12', ''), (r'10\.20\.1\.10', ''), (r'10\.20\.0\.1', ''),
    (r'00:1A:2B:3C:4D:5E', ''), (r'AA:BB:CC:DD:EE:FF', ''),
    (r'AMHS', ''), (r'SMT', ''), (r'SW-BLOC', 'N/D'), (r'SW-TOUR', 'N/D'), (r'SW-CORE-ASECNA', 'N/D'),
    (r'Gi1/0/14', 'N/D'), (r'Baie \d+', 'N/D'), (r'Hôte-', ''),
    (r'Wi-Fi ou Hub', 'N/D'), (r'MOCK_MODE', 'REAL'), (r'MOCK', ''), (r'simul\w*', ''), (r'demo\w*', ''), (r'fictif', '')
]

replace_in_files(os.path.join(BASE_DIR, 'frontend'), replacements)
replace_in_files(os.path.join(BASE_DIR, 'interface'), replacements)
