from typing import Optional

def resolve_ip_to_mac(ip_address: str) -> Optional[str]:
    # Simulation de résolution ARP
    if ip_address == "10.20.1.15":
        return "00:1A:2B:3C:4D:5E"
    elif ip_address == "10.20.1.20":
        return "AA:BB:CC:DD:EE:FF"
    return None

def resolve_name_to_ip(name: str) -> Optional[str]:
    # Simulation de résolution DNS locale
    name_lower = name.lower()
    if "amhs" in name_lower:
        return "10.20.1.15"
    elif "smt" in name_lower:
        return "10.20.1.20"
    return None
