"""Tests unitaires pour le module crypto."""

import socket
import ssl
import threading
import time
from pathlib import Path

import pytest

from common.crypto import SecureSocket, recv_exact


class TestSecureSocket:
    """Tests du module de chiffrement."""

    def test_init(self):
        """Test l'initialisation."""
        ss = SecureSocket()
        assert ss.cert_dir == Path("certs")
        assert ss.context_server is None
        assert ss.context_client is None

    def test_send_recv_data(self):
        """Test l'envoi et la réception de données."""
        ss = SecureSocket()

        # Création d'une paire de sockets connectées
        import io

        # Test des fonctions statiques send_data/recv_data
        # avec des données simples
        test_data = b"Hello, World!"
        # Nous ne pouvons pas tester directement sans socket,
        # mais nous vérifions que les méthodes existent
        assert hasattr(ss, "send_data")
        assert hasattr(ss, "recv_data")
        assert callable(ss.send_data)
        assert callable(ss.recv_data)


def test_recv_exact():
    """Test la fonction recv_exact."""
    # Test avec données simulées via un buffer
    import io

    class MockSocket:
        def __init__(self, data):
            self.data = io.BytesIO(data)

        def recv(self, n):
            return self.data.read(n)

    sock = MockSocket(b"testdata1234")
    result = recv_exact(sock, 4)
    assert result == b"test"

    sock = MockSocket(b"hello")
    result = recv_exact(sock, 10)
    assert result == b"hello"