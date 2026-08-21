import os

# Paramètres SNMP (Version 2c définie par défaut selon la demande)
SNMP_COMMUNITY = os.getenv("SNMP_COMMUNITY", "public")
SNMP_VERSION = 2  # Correspond à v2c dans PySNMP (0=v1, 1=v2c, 3=v3)
SNMP_PORT = int(os.getenv("SNMP_PORT", 161))

# Paramètres Réseau par défaut (Passerelle pour point de départ de la découverte)
DEFAULT_GATEWAY = os.getenv("DEFAULT_GATEWAY", "192.168.1.254")

# Paramètres SSH (Netmiko) pour le mode Sécurité (Isolation de port)
SSH_USERNAME = os.getenv("SSH_USERNAME", "admin")
SSH_PASSWORD = os.getenv("SSH_PASSWORD", "asecna123")
SSH_PORT = int(os.getenv("SSH_PORT", 22))

# Mode de développement
MOCK_MODE = True  # Activé pour simuler les réponses matérielles
