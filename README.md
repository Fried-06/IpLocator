# 🛰️ ASECNA NET-TRACE

**Application Web Intranet de Traçage Topologique, Découverte Dynamique et Réponse aux Incidents Réseau pour l'ASECNA (Togo).**

---

## 📌 1. Présentation du Projet

**ASECNA NET-TRACE** (IpLocator Light) est une solution de supervision et de sécurité conçue pour l'infrastructure réseau de la Navigation Aérienne (ASECNA). Elle permet de localiser physiquement des équipements critiques (AMHS, SMT, FREDA) par leur adresse IP/MAC, d'avoir une cartographie dynamique de la topologie réseau, et d'exécuter des actions de quarantaine (shutdown administratif de port via SSH).

### 🛠️ Stack Technique
- **Backend** : Python 3.10+, FastAPI, Uvicorn, Pydantic
- **Frontend** : HTML5 Vanilla, JavaScript (ES6+), Vanilla CSS avec Tailwind CSS CDN (adaptable pour hors-ligne Intranet), FontAwesome
- **Visualisation & Graphiques** : Chart.js (Dashboard NOC), Vis-network.js (Topologie Interactive 2D)

---

## 🚀 2. Guide de Démarrage Rapide (Installation & Lancement)

### Prérequis
- **Python 3.10 ou supérieur**
- Un navigateur web moderne (Chrome, Firefox, Edge)

### Étapes d'installation

1. **Cloner / Ouvrir le projet**
   ```bash
   cd c:\Users\MSI\Documents\iplocator_light
   ```

2. **Créer et activer un environnement virtuel Python**
   - **Sur Windows (PowerShell/CMD) :**
     ```powershell
     python -m venv venv
     .\venv\Scripts\activate
     ```
   - **Sur Linux / macOS :**
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```

3. **Installer les dépendances backend**
   ```bash
   pip install fastapi uvicorn pydantic
   ```
   *(Note : Si vous avez un fichier `serveur/requirements.txt`, lancez `pip install -r serveur/requirements.txt`)*

4. **Lancer le serveur backend FastAPI**
   ```bash
   uvicorn serveur.principal:app --reload --host 0.0.0.0 --port 8000
   ```

5. **Accéder à l'application**
   Ouvrez votre navigateur et accédez à :
   - Application Web : `http://localhost:8000` (ou directement en ouvrant `interface/index.html`)
   - Documentation interactive API (Swagger) : `http://localhost:8000/docs`

---

## 🧪 3. Inventaire des Données Mockées (Jeux de Tests)

En mode développement/démo, le backend utilise des services mockés (`service_snmp.py`, `service_arp.py`, `service_ssh.py`) renvoyant les équipements et topologies suivants :

### 🖥️ Équipements Critiques Pré-configurés
| Nom Équipement | Adresse IP | Adresse MAC | Switch d'Accès Rattaché | Port Switch | Emplacement Physique (sysLocation) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **AMHS** | `10.20.1.15` | `00:1A:2B:3C:4D:5E` | `SW-BLOC-TECH-01` (`10.20.0.12`) | `Gi1/0/14` | Bloc Technique - Salle BGD Baie 03 |
| **SMT** | `10.20.1.10` | `00:11:22:33:44:55` | `SW-BLOC-TECH-01` (`10.20.0.12`) | `Gi1/0/8` | Tour de Contrôle - Baie A |
| **FREDA** | `10.20.1.45` | `00:90:E8:11:22:33` | `SW-TOUR-01` (`10.20.0.15`) | `Gi1/0/4` | Centre Emetteur - Baie 01 |
| **SW-CORE** | `10.20.0.1` | `00:1A:2B:CORE` | *Switch Cœur Principal* | `--` | Salle Serveurs BGD (Cœur) |

### 🕸️ Structure de la Topologie Réseau
- **SW-CORE-ASECNA** (`10.20.0.1`) — Switch Cœur
  - 🔗 Relié à **SW-BLOC-TECH-01** (`10.20.0.12`)
    - 📌 Équipements rattachés : `AMHS` (`10.20.1.15`), `SMT` (`10.20.1.10`)
  - 🔗 Relié à **SW-TOUR-01** (`10.20.0.15`)
    - 📌 Équipements rattachés : `FREDA` (`10.20.1.45`)

### 🔑 Identifiants d'Isolation Sécurité
- **Mot de passe Administrateur NOC (Mock) :** `admin123`

---

## 📖 4. Guide de Démonstration / Scénario de Test Pas à Pas

Pour une démonstration complète durant la soutenance ou la revue de projet, suivez ces 4 étapes :

### 📊 Test 1 : Tableau de Bord (Dashboard NOC)
1. Cliquez sur **Tableau de bord** dans le menu latéral gauche.
2. Observez les métriques réseau (Santé globale à 98%, bande passante, taux d'erreurs).
3. Visualisez la répartition des ports actifs et le graphique en temps réel du débit réseau.

### 🔍 Test 2 : Traçage & Localisation Physiques
1. Cliquez sur **Traçage IP/MAC** dans le menu gauche.
2. Cliquez sur le raccourci rapide `🚀 Tester AMHS` (ou saisissez `10.20.1.15`).
3. Cliquez sur **Lancer le Traçage**.
4. **Résultat attendu :** 
   - La fiche d'identité s'affiche avec la localisation *Bloc Technique - Salle BGD Baie 03*.
   - Le schéma **Path Tracing (L2/L3)** trace graphiquement le chemin de l'équipement jusqu'au Switch Cœur via le switch `SW-BLOC-TECH-01` sur le port `Gi1/0/14`.

### 🌐 Test 3 : Cartographie & Topologie Réseau
1. Cliquez sur **Topologie Réseau** dans le menu.
2. Le graphe interactif Vis-network s'anime avec les nœuds vert néon (Cœur), bleu (Accès) et cyan (Serveurs).
3. Manipulez les nœuds par glisser-déposer, utilisez les molettes de zoom et testez le bouton **Recentrer la Vue**.
4. Cliquez sur un switch ou serveur pour ouvrir le **Panneau Latéral (Drawer)** affichant ses métriques détaillées.
5. Décochez la case **Équipements Critiques** pour afficher la vue filtrée "Switchs uniquement".

### 🚨 Test 4 : Centre de Sécurité & Isolation d'Urgence
1. Cliquez sur **Isolation & Sécurité** dans le menu.
2. Entrez `AMHS` ou `10.20.1.15` puis cliquez sur **Détecter le Port** (Détection du port `Gi1/0/14`).
3. Sélectionnez le motif *"Infection Malware / Ransomware suspecté"*.
4. Cliquez sur **ISOLER L'ÉQUIPEMENT MAINTENANT**.
5. Dans la modale de confirmation, saisissez le mot de passe administrateur : `admin123`.
6. Validez. La modale se ferme, le backend simule les commandes SSH Cisco `shutdown` et une nouvelle ligne avec le badge **ISOLÉ** apparaît dans le Registre d'Audit.
7. Testez la réactivation en cliquant sur **Restaurer**, ressaisissez `admin123` : le statut passe à **RESTAURÉ**.

---

## 🔌 5. Passer du Mode Mock au Réseau Réel ASECNA

Pour déployer l'application sur le réseau réel de l'ASECNA, vous devez remplacer les simulations mockées par les pilotes de communication réseau :

1. **Service SNMP (`serveur/services/service_snmp.py`)** :
   - Remplacer les réponses statiques par les requêtes réelles via `pysnmp` ou `easysnmp`.
   - Reconnecter les OIDs SNMP standard pour CDP/LLDP :
     - CAM Table (Mac Address Table) : `.1.3.6.1.2.1.17.4.3.1.2`
     - sysLocation : `.1.3.6.1.2.1.1.6.0`
     - CDP Neighbor Table : `.1.3.6.1.4.1.9.9.23.1.2.1.1`

2. **Service ARP / IP Resolution (`serveur/services/service_arp.py`)** :
   - Interroger les tables ARP des routeurs/switchs cœurs via SNMP (OID `ipNetToMediaPhysAddress` `.1.3.6.1.2.1.4.22.1.2`).

3. **Service SSH Isolation (`serveur/services/service_ssh.py`)** :
   - Décommenter/ajouter l'utilisation du package `netmiko` (`ConnectHandler`).
   - Établir la vraie connexion SSH vers le switch cible et envoyer la séquence de commandes :
     ```python
     cisco_device = {
         'device_type': 'cisco_ios',
         'host': switch_ip,
         'username': admin_user,
         'password': admin_password,
     }
     # netmiko_conn.send_config_set([f'interface {port_interface}', 'shutdown'])
     ```

4. **Bibliothèques Frontend Hors-Ligne (Intranet)** :
   - Télécharger les fichiers minifiés de Tailwind CSS, FontAwesome, Chart.js et Vis-network.js dans le dossier local `interface/ressources/lib/` et mettre à jour les chemins dans `index.html`.

---
*© ASECNA - Direction des Services de la Navigation Aérienne (DSNA) / Togo*
