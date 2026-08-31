"""Module d'enregistrement audio via sounddevice (streaming)."""

import logging
import threading
import io
import wave
import time
import sounddevice as sd
import numpy as np
from typing import Callable, Optional

logger = logging.getLogger(__name__)


class AudioRecorder:
    """Enregistrement audio en continu avec sounddevice."""

    RATE = 44100
    CHANNELS = 1
    CHUNK = 1024  # taille des blocs

    def __init__(self, on_chunk: Optional[Callable[[bytes], None]] = None):
        self._on_chunk = on_chunk
        self._running = False
        self._stream = None
        self._frames = []
        self._lock = threading.Lock()

    def start(self, stream_mode: bool = False) -> str:
        """Démarre l'enregistrement audio en continu."""
        if self._running:
            return "[!] Enregistrement déjà actif"

        self._running = True
        self._frames = []

        def callback(indata, frames, time, status):
            if status:
                logger.warning(f"Audio status: {status}")
            if self._running:
                audio_bytes = indata.tobytes()
                with self._lock:
                    self._frames.append(audio_bytes)
                if stream_mode and self._on_chunk:
                    self._on_chunk(audio_bytes)

        try:
            self._stream = sd.InputStream(
                samplerate=self.RATE,
                channels=self.CHANNELS,
                dtype='int16',
                blocksize=self.CHUNK,
                callback=callback
            )
            self._stream.start()
            logger.info("Enregistrement audio démarré (streaming)")
            return "[+] Enregistrement audio démarré"
        except Exception as e:
            self._running = False
            logger.error(f"Erreur démarrage audio : {e}")
            return f"[!] Erreur : {e}"

    def stop(self) -> bytes:
        """Arrête l'enregistrement et retourne les données WAV."""
        if not self._running:
            return b""

        self._running = False
        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None

        with self._lock:
            raw_frames = self._frames[:]
            self._frames = []

        if not raw_frames:
            logger.info("Aucune donnée audio enregistrée")
            return b""

        # Assembler les données
        audio_data = b"".join(raw_frames)

        # Créer un fichier WAV
        try:
            wav_buffer = io.BytesIO()
            with wave.open(wav_buffer, "wb") as wf:
                wf.setnchannels(self.CHANNELS)
                wf.setsampwidth(2)  # 16 bits
                wf.setframerate(self.RATE)
                wf.writeframes(audio_data)

            wav_data = wav_buffer.getvalue()
            logger.info(f"Audio enregistré : {len(wav_data)} octets")
            return wav_data
        except Exception as e:
            logger.error(f"Erreur création WAV : {e}")
            return audio_data