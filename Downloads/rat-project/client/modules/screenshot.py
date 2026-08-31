"""Module de capture d'écran (fallback scrot via stdout)."""

import logging
import subprocess
import io
from PIL import ImageGrab

logger = logging.getLogger(__name__)


def take_screenshot() -> bytes:
    """Prend une capture d'écran (PIL, puis scrot en fallback)."""
    # 1. Essayer PIL (nécessite X11)
    try:
        screenshot = ImageGrab.grab()
        buffer = io.BytesIO()
        screenshot.save(buffer, format="PNG")
        buffer.seek(0)
        data = buffer.getvalue()
        if data and len(data) > 100:
            logger.info("Capture avec PIL réussie")
            return data
    except Exception as e:
        logger.warning(f"PIL échoué : {e}")

    # 2. Fallback : scrot en sortie stdout (pas de fichier temporaire)
    try:
        # -z : ignore les fenêtres vide
        # -o : écrit sur stdout
        result = subprocess.run(
            ['scrot', '-z', '-o', '-'],
            capture_output=True,
            check=True,
            timeout=5
        )
        if result.stdout and len(result.stdout) > 100:
            logger.info("Capture avec scrot (stdout) réussie")
            return result.stdout
        else:
            logger.warning("scrot a retourné un fichier vide ou trop petit")
    except FileNotFoundError:
        logger.warning("scrot n'est pas installé (sudo apt install scrot)")
    except subprocess.TimeoutExpired:
        logger.warning("scrot a expiré")
    except Exception as e:
        logger.warning(f"scrot a échoué : {e}")

    # 3. Fallback : import (ImageMagick) - si présent
    try:
        result = subprocess.run(
            ['import', '-window', 'root', 'png:-'],
            capture_output=True,
            check=True,
            timeout=5
        )
        if result.stdout and len(result.stdout) > 100:
            logger.info("Capture avec import (stdout) réussie")
            return result.stdout
    except Exception:
        pass

    raise RuntimeError("Impossible de capturer l'écran (aucun fallback n'a fonctionné)")
