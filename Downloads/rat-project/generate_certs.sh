#!/bin/bash
# Script de génération des certificats TLS auto-signés
# À exécuter une seule fois avant le premier lancement

CERT_DIR="certs"
DAYS_VALID=3650
KEY_SIZE=2048

mkdir -p "$CERT_DIR"

echo "[*] Génération du certificat auto-signé pour TLS..."

# Génération de la clé privée et du certificat
openssl req -x509 -newkey rsa:$KEY_SIZE \
    -keyout "$CERT_DIR/server.key" \
    -out "$CERT_DIR/server.crt" \
    -days $DAYS_VALID \
    -nodes \
    -subj "/CN=RAT-Server/O=RAT-Project/C=FR"

# Copie du certificat pour le client
cp "$CERT_DIR/server.crt" "$CERT_DIR/client.crt"

echo "[+] Certificats générés avec succès dans $CERT_DIR/"
echo "    - server.key  (clé privée serveur)"
echo "    - server.crt  (certificat serveur)"
echo "    - client.crt  (certificat client)"