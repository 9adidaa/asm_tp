"""Module de chiffrement et déchiffrement TLS pour la communication sécurisée.

Utilise TLS 1.3 via la bibliothèque cryptography pour assurer
la confidentialité et l'intégrité des échanges.
"""

import logging
import socket
import ssl
from pathlib import Path
import subprocess
import shutil
import sys

logger = logging.getLogger(__name__)


class SecureSocket:
    """Wrapper autour d'une socket TCP avec chiffrement TLS.

    Fournit une interface simplifiée pour envoyer et recevoir
    des données de manière sécurisée.
    """

    def __init__(self, cert_dir: str = "certs"):
        self.cert_dir = Path(cert_dir)
        self.context_server = None
        self.context_client = None
        self._ensure_certificates()

    def _ensure_certificates(self):
        """Génère des certificats auto-signés s'ils n'existent pas."""
        cert_path = self.cert_dir / "server.crt"
        key_path = self.cert_dir / "server.key"
        client_cert = self.cert_dir / "client.crt"

        if cert_path.exists() and key_path.exists():
            logger.info("Certificats existants, pas de génération.")
            return

        self.cert_dir.mkdir(exist_ok=True)
        logger.info("Génération automatique des certificats SSL...")

        # Essayer avec openssl (disponible sur Linux et parfois Windows)
        try:
            subprocess.run(
                [
                    "openssl", "req", "-x509", "-newkey", "rsa:2048",
                    "-keyout", str(key_path), "-out", str(cert_path),
                    "-days", "365", "-nodes",
                    "-subj", "/CN=RAT-Server"
                ],
                check=True,
                capture_output=True,
            )
            shutil.copy(cert_path, client_cert)
            logger.info("Certificats générés avec openssl.")
            return
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.warning("openssl non trouvé, génération via cryptography...")

        # Fallback : utiliser cryptography
        try:
            from cryptography import x509
            from cryptography.x509.oid import NameOID
            from cryptography.hazmat.primitives import hashes, serialization
            from cryptography.hazmat.primitives.asymmetric import rsa
            import datetime

            # Clé privée
            key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
            # Certificat auto-signé
            subject = issuer = x509.Name([
                x509.NameAttribute(NameOID.COUNTRY_NAME, "FR"),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, "RAT-Project"),
                x509.NameAttribute(NameOID.COMMON_NAME, "RAT-Server"),
            ])
            cert = (
                x509.CertificateBuilder()
                .subject_name(subject)
                .issuer_name(issuer)
                .public_key(key.public_key())
                .serial_number(x509.random_serial_number())
                .not_valid_before(datetime.datetime.now(datetime.UTC))
                .not_valid_after(datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=365))
                .sign(key, hashes.SHA256())
            )

            with open(key_path, "wb") as f:
                f.write(key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()
                ))
            with open(cert_path, "wb") as f:
                f.write(cert.public_bytes(serialization.Encoding.PEM))
            shutil.copy(cert_path, client_cert)
            logger.info("Certificats générés via cryptography.")
        except ImportError:
            logger.error("Impossible de générer les certificats. Installez cryptography ou openssl.")
            raise

    def _load_server_context(self) -> ssl.SSLContext:
        """Charge le contexte SSL côté serveur."""
        if self.context_server is None:
            cert_path = self.cert_dir / "server.crt"
            key_path = self.cert_dir / "server.key"

            if not cert_path.exists() or not key_path.exists():
                raise FileNotFoundError(
                    f"Certificats SSL introuvables dans {self.cert_dir}. "
                    "Génération automatique échouée."
                )

            self.context_server = ssl.create_default_context(
                ssl.Purpose.CLIENT_AUTH
            )
            self.context_server.load_cert_chain(
                certfile=str(cert_path),
                keyfile=str(key_path),
            )
            self.context_server.verify_mode = ssl.CERT_NONE
            self.context_server.check_hostname = False
            logger.info("Contexte serveur TLS chargé")

        return self.context_server

    def _load_client_context(self) -> ssl.SSLContext:
        """Charge le contexte SSL côté client."""
        if self.context_client is None:
            cert_path = self.cert_dir / "client.crt"

            if not cert_path.exists():
                raise FileNotFoundError(
                    f"Certificat client introuvable dans {self.cert_dir}. "
                    "Génération automatique échouée."
                )

            self.context_client = ssl.create_default_context(
                ssl.Purpose.SERVER_AUTH,
            )
            self.context_client.load_verify_locations(cafile=str(cert_path))
            # Désactiver complètement la vérification pour les certificats auto-signés
            self.context_client.verify_mode = ssl.CERT_NONE
            self.context_client.check_hostname = False
            logger.info("Contexte client TLS chargé")

        return self.context_client

    def wrap_server_socket(self, sock: socket.socket) -> ssl.SSLSocket:
        """Encapsule une socket serveur avec TLS."""
        context = self._load_server_context()
        return context.wrap_socket(sock, server_side=True)

    def wrap_client_socket(
        self, sock: socket.socket, hostname: str = "localhost"
    ) -> ssl.SSLSocket:
        """Encapsule une socket client avec TLS (mode développement)."""
        # Créer un contexte SSL sans vérification
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        return context.wrap_socket(sock, server_hostname=hostname)

    @staticmethod
    def send_data(sock: ssl.SSLSocket, data: bytes) -> None:
        """Envoie des données de manière fiable."""
        size = len(data).to_bytes(4, byteorder="big")
        sock.sendall(size + data)

    @staticmethod
    def recv_data(sock: ssl.SSLSocket) -> bytes:
        """Reçoit des données de manière fiable."""
        size_bytes = recv_exact(sock, 4)
        if not size_bytes:
            return b""
        size = int.from_bytes(size_bytes, byteorder="big")
        return recv_exact(sock, size)


def recv_exact(sock: ssl.SSLSocket, n: int) -> bytes:
    """Reçoit exactement n octets de la socket."""
    data = bytearray()
    while len(data) < n:
        packet = sock.recv(n - len(data))
        if not packet:
            break
        data.extend(packet)
    return bytes(data)