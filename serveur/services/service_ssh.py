def shutdown_port(switch_ip: str, port_interface: str) -> bool:
    """
    Simulation d'une connexion SSH via Netmiko pour désactiver (shutdown) un port.
    Retourne True si succès.
    """
    print(f"[MOCK SSH] Connexion à {switch_ip} via SSH...")
    print(f"[MOCK SSH] Passage en mode configuration terminal (conf t)...")
    print(f"[MOCK SSH] Exécution: interface {port_interface}")
    print(f"[MOCK SSH] Exécution: shutdown")
    print(f"[MOCK SSH] Le port {port_interface} sur {switch_ip} est maintenant ADMIN DOWN.")
    return True

def no_shutdown_port(switch_ip: str, port_interface: str) -> bool:
    """
    Simulation d'une connexion SSH via Netmiko pour réactiver (no shutdown) un port.
    Retourne True si succès.
    """
    print(f"[MOCK SSH] Connexion à {switch_ip} via SSH...")
    print(f"[MOCK SSH] Passage en mode configuration terminal (conf t)...")
    print(f"[MOCK SSH] Exécution: interface {port_interface}")
    print(f"[MOCK SSH] Exécution: no shutdown")
    print(f"[MOCK SSH] Le port {port_interface} sur {switch_ip} est maintenant UP.")
    return True
