"""Tests unitaires pour le module serveur."""

import socket
import threading
import time

import pytest

from common.crypto import SecureSocket
from common.protocol import Message, MessageType


class TestServer:
    """Tests du fonctionnement du serveur (sans connexion réelle)."""

    def test_server_initialization(self):
        """Test que les imports du serveur fonctionnent."""
        from server.server import RATServer
        assert RATServer is not None

    def test_server_default_params(self):
        """Test les paramètres par défaut du serveur."""
        from server.server import RATServer
        server = RATServer()
        assert server.host == "0.0.0.0"
        assert server.port == 8888
        assert server.running is False
        assert server.agents == {}

    def test_server_custom_params(self):
        """Test les paramètres personnalisés."""
        from server.server import RATServer
        server = RATServer(host="127.0.0.1", port=9999)
        assert server.host == "127.0.0.1"
        assert server.port == 9999


class TestAgentHandler:
    """Tests du gestionnaire d'agents."""

    def test_handler_initialization(self):
        """Test l'initialisation d'un AgentHandler."""
        from server.handler import AgentHandler
        # On ne peut pas créer sans socket, on teste juste la classe
        assert AgentHandler is not None

    def test_send_receive(self):
        """Test la création de commandes pour handler."""
        from server.handler import AgentHandler
        handler_class = AgentHandler
        assert hasattr(handler_class, "send_command")
        assert hasattr(handler_class, "interact")