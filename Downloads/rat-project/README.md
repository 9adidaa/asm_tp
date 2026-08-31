# RAT - Remote Administration Tool

Projet final de développement d’un outil d’administration à distance (RAT) en Python, composé d’un **serveur** et d’un **client** communiquant via une socket TCP chiffrée avec **TLS 1.3**.

---

## 📋 Fonctionnalités

### Client – Commandes disponibles

| Commande | Description |
|----------|-------------|
| `help` | Affiche la liste des commandes disponibles |
| `download <path>` | Récupère un fichier de la machine victime et le sauvegarde sur le serveur |
| `upload <local> <dest>` | Envoie un fichier du serveur vers la machine victime |
| `shell` | Ouvre un shell interactif (bash/cmd) – utilise `shell_start`, `shell_exec`, `shell_stop` |
| `ipconfig` | Affiche la configuration réseau complète de la victime |
| `screenshot` | Capture d’écran de la victime (sauvegardée en PNG) |
| `search <pattern>` | Recherche un fichier (optimisée avec `find` sous Linux, `dir` sous Windows) |
| `hashdump` | Récupère la base SAM (Windows) ou `/etc/shadow` (Linux) – nécessite des privilèges élevés |
| `keylogger_start` | Démarre l’enregistrement des frappes clavier |
| `keylogger_stop` | Arrête le keylogger |
| `keylogger_get` | Récupère les touches enregistrées |
| `webcam_snapshot` | Prend une photo via la webcam (JPEG) |
| `webcam_stream_start` | Démarre le flux vidéo en direct et enregistre une vidéo MP4 sur le client |
| `webcam_stream_stop` | Arrête le streaming et finalise le fichier vidéo |
| `record_audio_start` | Enregistre le microphone (WAV) |
| `record_audio_stop` | Arrête l’enregistrement et sauvegarde le fichier audio |

### Serveur – Interface interactive

- **`rat >`** – invite de commande principale
- **`sessions`** – liste tous les agents connectés
- **`interact <id>`** – entre en mode interactif avec un agent spécifique
- **`help`** – affiche l’aide du serveur
- **`exit` / `quit`** – arrête le serveur

Le serveur gère plusieurs agents en parallèle (threads) et gère les déconnexions proprement.

---

## 🛠 Installation

### Prérequis
- Python 3.12 ou supérieur (recommandé)
- Poetry (gestionnaire de dépendances)
- Pour Linux : `portaudio19-dev`, `scrot`, `ffmpeg`, `v4l-utils`

### Cloner le projet
```bash
git clone <url-du-depot>
cd rat-project




Installer les dépendances Python:
poetry install

Dépendances système (Linux):
sudo apt-get update
sudo apt-get install -y portaudio19-dev scrot ffmpeg v4l-utils

Sous Windows, aucune dépendance système supplémentaire n’est requise (les roues pré-compilées sont utilisées).


🔐 Certificats TLS
Le projet génère automatiquement des certificats auto-signés au premier lancement (via cryptography ou openssl).
Aucune action manuelle n’est nécessaire, mais vous pouvez forcer la régénération en supprimant le dossier certs/.

Pour une utilisation en production, remplacez les certificats par des certificats signés par une autorité de confiance.


 *Utilisation
Lancer le serveur:
poetry run python -m server.server --host 0.0.0.0 --port 8888

Lancer le client:
poetry run python -m client.client --host <adresse_du_serveur> --port 8888


Structure du projet:
rat-project/
├── common/               # Modules partagés (crypto, protocole)
├── client/               # Client RAT
│   ├── client.py         # Logique principale
│   └── modules/          # Fonctionnalités
│       ├── audio.py
│       ├── filesystem.py
│       ├── hashdump.py
│       ├── keylogger.py
│       ├── screenshot.py
│       ├── search.py
│       ├── shell.py
│       ├── system_info.py
│       └── webcam.py
├── server/               # Serveur RAT
│   ├── server.py
│   └── handler.py        # Gestion d’un agent
├── tests/                # Tests unitaires (pytest)
├── certs/                # Certificats TLS (auto-générés)
├── downloads/            # Dossier de réception des fichiers
├── pyproject.toml        # Dépendances Poetry
└── README.md

Exemple d’interaction
Serveur :


[*] Listening on 8888...
rat > sessions
[*] Aucun agent connecté
rat > interact 1
[*] Mode interactif avec l'agent 1
rat agent 1 > help
...
rat agent 1 > screenshot
[+] Screenshot sauvegardé : downloads/screenshot_1234567890.png
rat agent 1 > webcam_stream_start
[+] Streaming webcam démarré (vidéo : downloads/stream_video_1234567890.mp4)
rat agent 1 > webcam_stream_stop
[+] Streaming arrêté (120 frames capturées)
[+] Vidéo sauvegardée : downloads/stream_video_1234567890.mp4



## 🐳 Docker (bonus)

Le projet peut être déployé facilement avec Docker.  
Un `Dockerfile` et un `docker-compose.yml` sont fournis à la racine du projet.

### Construire et lancer le conteneur

```bash
docker-compose up --build
```

### Lancer en arrière‑plan

```bash
docker-compose up -d
```

### Arrêter le conteneur

```bash
docker-compose down
```

### Détails techniques

- Le serveur écoute sur le port `8888`.
- Les fichiers récupérés (screenshots, audio, etc.) sont stockés dans le volume `./downloads:/app/downloads` (persistants sur l’hôte).
- Les certificats TLS sont générés automatiquement au premier lancement.

### Test du conteneur

Une fois le serveur lancé, connectez‑y un client depuis votre machine hôte :

```bash
python -m client.client --host localhost --port 8888
```

Les logs du conteneur afficheront `[+] Agent received !` pour confirmer la connexion.


👤 Auteurs
Mohamed Mokdad & Mohamed bekkali