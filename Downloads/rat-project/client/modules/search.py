"""Module de recherche de fichiers (optimisé pour Windows)."""

import logging
import os
import subprocess
from typing import List

logger = logging.getLogger(__name__)


def search_file(pattern: str, base_dir: str = None) -> List[str]:
    """Recherche un fichier sur la machine victime.
    
    Args:
        pattern: Motif de recherche (nom de fichier partiel)
        base_dir: Répertoire de base (par défaut : C:\)
    
    Returns:
        Liste des chemins trouvés
    """
    if base_dir is None:
        base_dir = "C:\\"
    
    max_results = 50
    results = []
    pattern_lower = pattern.lower()
    
    try:
        logger.info(f"Recherche de '{pattern}' dans {base_dir}...")
        
        # Utiliser la commande 'dir' pour une recherche rapide sous Windows
        # /s : recherche dans les sous-dossiers
        # /b : format simple (juste les chemins)
        # /a-d : seulement les fichiers (pas les dossiers)
        cmd = f'dir "{base_dir}" /s /b /a-d | findstr /i "{pattern}"'
        
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=15,  # Timeout de 15 secondes
        )
        
        if result.returncode == 0 and result.stdout:
            lines = result.stdout.strip().split('\n')
            for line in lines[:max_results]:
                if line.strip():
                    try:
                        size = os.path.getsize(line.strip())
                        results.append(f"{line.strip()} ({size} octets)")
                    except Exception:
                        results.append(line.strip())
        
        if not results:
            # Fallback : os.walk avec profondeur limitée
            results = _search_fallback(pattern, base_dir)
        
        logger.info(f"Recherche terminée : {len(results)} résultat(s)")
        return results if results else ["[!] Aucun fichier trouvé"]
        
    except subprocess.TimeoutExpired:
        logger.warning("Recherche trop longue, timeout")
        return ["[!] Recherche trop longue (timeout 15s)"]
    except Exception as e:
        logger.error(f"Erreur recherche : {e}")
        return _search_fallback(pattern, base_dir)


def _search_fallback(pattern: str, base_dir: str) -> List[str]:
    """Fallback avec os.walk (limité en profondeur)."""
    results = []
    pattern_lower = pattern.lower()
    max_results = 50
    max_depth = 3  # Limite la profondeur pour éviter les blocages
    
    try:
        for root, dirs, files in os.walk(base_dir):
            # Limiter la profondeur
            depth = root.replace(base_dir, '').count(os.sep)
            if depth > max_depth:
                dirs.clear()
                continue
            
            # Ignorer les dossiers système
            if any(part in ['Windows', 'System32', 'Program Files', 'Program Files (x86)'] 
                   for part in root.split(os.sep)):
                continue
            
            for filename in files:
                if pattern_lower in filename.lower():
                    full_path = os.path.join(root, filename)
                    try:
                        size = os.path.getsize(full_path)
                        results.append(f"{full_path} ({size} octets)")
                    except Exception:
                        results.append(full_path)
                    
                    if len(results) >= max_results:
                        break
            if len(results) >= max_results:
                break
        
        return results if results else ["[!] Aucun fichier trouvé"]
    except Exception as e:
        return [f"[!] Erreur fallback : {e}"]