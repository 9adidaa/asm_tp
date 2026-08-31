"""Module de shell interactif simplifié (basé sur subprocess.run)."""

import logging
import platform
import subprocess
import threading

logger = logging.getLogger(__name__)

IS_WINDOWS = platform.system().lower() == "windows"
SHELL_CMD = "cmd.exe" if IS_WINDOWS else "/bin/bash"


class InteractiveShell:
    """Shell interactif simplifié (exécution unique par commande)."""

    def __init__(self):
        self.running = False
        self._lock = threading.Lock()

    def start(self) -> str:
        """Démarre le shell (état uniquement, pas de processus)."""
        with self._lock:
            if self.running:
                return "[!] Shell déjà actif"
            self.running = True
            logger.info("Shell interactif démarré")
            return "[+] Shell interactif démarré"

    def execute(self, command: str) -> str:
        """Exécute une commande shell et retourne la sortie."""
        if not self.running:
            return "[!] Shell non actif. Utilisez 'shell_start' d'abord."

        with self._lock:
            try:
                # Utiliser subprocess.run pour une exécution unique et fiable
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                output = result.stdout
                if result.stderr:
                    output += f"\n[STDERR]\n{result.stderr}"
                if result.returncode != 0:
                    output += f"\n[EXIT CODE] {result.returncode}"
                return output.strip() if output.strip() else "(aucune sortie)"
            except subprocess.TimeoutExpired:
                return "[!] Commande expirée (30s)"
            except Exception as e:
                return f"[!] Erreur shell : {e}"

    def stop(self) -> str:
        """Arrête le shell."""
        with self._lock:
            if not self.running:
                return "[!] Aucun shell actif"
            self.running = False
            logger.info("Shell interactif arrêté")
            return "[+] Shell arrêté"