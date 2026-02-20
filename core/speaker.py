import logging
import threading
import torch
import sounddevice as sd
import numpy as np

import config

log = logging.getLogger(__name__)


class Speaker:
    """Silero TTS — синтез речи на русском языке."""

    def __init__(self):
        self._device = torch.device("cpu")
        self._model = None
        self._lock = threading.Lock()

    def load(self):
        """Загружает модель TTS (вызвать один раз при старте)."""
        log.info("Загрузка Silero TTS...")
        self._model, _ = torch.hub.load(
            repo_or_dir="snakers4/silero-models",
            model="silero_tts",
            language="ru",
            speaker="v3_1_ru",
        )
        self._model.to(self._device)
        log.info("Silero TTS загружен.")

    def speak(self, text: str):
        """Озвучивает текст через динамик."""
        if not text.strip():
            return
        if self._model is None:
            log.warning("TTS модель не загружена")
            return

        with self._lock:
            audio = self._model.apply_tts(
                text=text,
                speaker=config.TTS_SPEAKER,
                sample_rate=config.TTS_SAMPLE_RATE,
            )
            audio_np = audio.detach().cpu().numpy()
            sd.play(audio_np, samplerate=config.TTS_SAMPLE_RATE)
            sd.wait()

    def speak_async(self, text: str):
        """Озвучивает текст в отдельном потоке (не блокирует)."""
        thread = threading.Thread(target=self.speak, args=(text,), daemon=True)
        thread.start()
