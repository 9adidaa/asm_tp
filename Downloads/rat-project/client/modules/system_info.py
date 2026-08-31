"""Module d'information système : ipconfig, informations réseau."""

import logging
import platform
import socket
import subprocess
from typing import Dict, List

import psutil

logger = logging.getLogger(__name__)


def get_ipconfig() -> str:
    """Récupère la configuration réseau de la machine.

    Similaire à 'ipconfig' sur Windows ou 'ifconfig' sur Linux.

    Returns:
        Configuration réseau formatée
    """
    system = platform.system().lower()
    output_parts = []

    # En-tête
    hostname = socket.gethostname()
    output_parts.append(f"Hôte : {hostname}")
    output_parts.append(f"Système : {platform.system()} {platform.release()}")
    output_parts.append("=" * 50)

    # Toutes les interfaces réseau
    addrs = psutil.net_if_addrs()
    stats = psutil.net_if_stats()

    for interface, addr_list in addrs.items():
        output_parts.append(f"\nInterface : {interface}")

        # Statut de l'interface
        if interface in stats:
            nic_stat = stats[interface]
            status = "UP" if nic_stat.isup else "DOWN"
            speed = nic_stat.speed if nic_stat.speed > 0 else "?"
            output_parts.append(f"  Statut : {status}")
            output_parts.append(f"  Vitesse : {speed} Mbps")

        for addr in addr_list:
            if addr.family.name == "AF_INET":
                output_parts.append(f"  IPv4 : {addr.address}")
                if addr.netmask:
                    output_parts.append(f"  Masque : {addr.netmask}")
                if addr.broadcast:
                    output_parts.append(f"  Broadcast : {addr.broadcast}")
            elif addr.family.name == "AF_INET6":
                output_parts.append(f"  IPv6 : {addr.address}")
            elif addr.family.name == "AF_LINK" or "AF_PACKET" in str(addr.family):
                output_parts.append(f"  MAC : {addr.address}")

    # Tenter d'obtenir la gateway par défaut
    try:
        gateways = psutil.net_if_stats()
        output_parts.append("\n" + "=" * 50)
        output_parts.append("Routes (information partielle)")
    except Exception:
        pass

    return "\n".join(output_parts)


def get_system_info() -> Dict:
    """Retourne un dictionnaire d'informations système."""
    return {
        "hostname": socket.gethostname(),
        "os": platform.system(),
        "os_version": platform.version(),
        "os_release": platform.release(),
        "architecture": platform.machine(),
        "processor": platform.processor(),
        "cpu_count": psutil.cpu_count(),
        "ram_total": psutil.virtual_memory().total,
        "ram_available": psutil.virtual_memory().available,
        "python_version": platform.python_version(),
    }