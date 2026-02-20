import numpy as np
from faster_whisper import WhisperModel

import config


class Recognizer:
    """Распознавание речи через faster-whisper."""

    def __init__(self):
        self._model = WhisperModel(
            config.WHISPER_MODEL,
            device=config.WHISPER_DEVICE,
            compute_type=config.WHISPER_COMPUTE_TYPE,
        )

    def transcribe(self, audio: np.ndarray) -> str:
        """Транскрибирует аудио (float32, 16kHz) в текст."""
        segments, info = self._model.transcribe(
            audio,
            language=config.WHISPER_LANGUAGE,
            beam_size=5,
            vad_filter=False,  # VAD уже отработал в listener
        )
        text = " ".join(seg.text.strip() for seg in segments)
        return text.strip()
