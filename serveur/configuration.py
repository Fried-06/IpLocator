import os
SNMP_COMMUNITY = os.getenv("SNMP_COMMUNITY")
SNMP_VERSION = 2
SNMP_PORT = int(os.getenv("SNMP_PORT", 161))
SSH_USERNAME = os.getenv("SSH_USERNAME")
SSH_PASSWORD = os.getenv("SSH_PASSWORD")
SSH_PORT = int(os.getenv("SSH_PORT", 22))
JWT_SECRET = os.getenv("JWT_SECRET", "change-me-in-production")
