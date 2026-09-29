import subprocess
import re
import socket
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
        "00:1A:2B": "Cisco Systems", "00:50:56": "VMware Virtual", "00:0C:29": "VMware Virtual",
        "00:15:5D": "Microsoft Hyper-V", "B8:27:EB": "Raspberry Pi", "F0:92:1C": "Apple, Inc.",
        "50:C7:BF": "TP-Link Technologies", "70:4D:7B": "Huawei Technologies", "F4:60:E2": "Dell Inc."
    }
    return known_ouis.get(prefix, "Inconnu")
