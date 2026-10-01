import subprocess
import re
import socket
import os
import asyncio
from typing import Optional, Tuple

def ping_host(ip: str, timeout_ms: int = 1500) -> Tuple[bool, float]:
    try:
        # Compatible Windows / Linux basique (on privilégie Windows comme demandé initialement)
        cmd = ["ping", "-n", "1", "-w", str(timeout_ms), ip] if os.name == 'nt' else ["ping", "-c", "1", "-W", str(timeout_ms//1000 or 1), ip]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=3)
        if res.returncode == 0:
            match = re.search(r"(?:temps|time)[=<](\d+(?:\.\d+)?)ms", res.stdout, re.IGNORECASE)
            if match: return True, float(match.group(1))
            return True, 1.0
        return False, 0.0
    except: return False, 0.0

def resolve_ip_to_mac(ip_address: str) -> Optional[str]:
    ping_host(ip_address, timeout_ms=500)
    try:
        res = subprocess.run(["arp", "-a"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=2)
        if res.returncode == 0:
            for line in res.stdout.splitlines():
                if ip_address in line:
                    for p in line.split():
                        if re.match(r"^([0-9a-fA-F]{2}[:-]){5}([0-9a-fA-F]{2})$", p):
                            return p.replace("-", ":").upper()
    except: pass
    return None

def resolve_name_to_ip(name: str) -> Optional[str]:
    try: return socket.gethostbyname(name.strip())
    except: return None

def resolve_ip_to_hostname(ip_address: str) -> Optional[str]:
    try:
        host, _, _ = socket.gethostbyaddr(ip_address)
        return host
    except: return None

def get_mac_vendor(mac: str) -> str:
    if not mac or mac == "N/A" or len(mac) < 8: return "Inconnu"
    prefix = mac[:8].upper().replace("-", ":")
    known_ouis = {
        "00:1A:2B": "Cisco Systems", "00:64:40": "Cisco Systems", "A4:4C:C8": "Cisco Systems",
        "64:4E:D7": "Cisco Systems", "00:50:56": "VMware Virtual", "00:0C:29": "VMware Virtual",
        "00:15:5D": "Microsoft Hyper-V", "B8:27:EB": "Raspberry Pi", "DC:A6:32": "Raspberry Pi",
        "F0:92:1C": "Apple, Inc.", "10:FE:ED": "Apple, Inc.", "AC:BC:32": "Apple, Inc.",
        "50:C7:BF": "TP-Link", "70:4D:7B": "Huawei", "F4:60:E2": "Dell Inc.",
        "78:0C:B8": "Samsung / Dell", "5C:F9:DD": "Dell Inc.", "8C:DC:D4": "Dell Inc.",
        "74:78:A6": "Dell Inc.", "18:03:73": "Dell Inc.", "B0:22:7A": "Lenovo",
        "80:E8:2C": "Intel Corporation", "70:A7:41": "HP Inc.", "6C:3B:E5": "HP Inc.",
        "B4:B5:2F": "Hewlett Packard", "10:E7:C6": "ASUSTeK", "04:D4:C4": "ASUSTeK",
        "48:0F:CF": "Hon Hai (Foxconn)", "DA:0D:17": "Samsung Electronics"
    }
    return known_ouis.get(prefix, "Inconnu")
