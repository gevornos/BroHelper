import threading
import numpy as np
import torch
import sounddevice as sd
from silero_vad import load_silero_vad, VADIterator

import config

CHUNK_SIZE = 512  # 32ms при 16kHz — требование Silero VAD


class Listener:
    """Непрерывное прослушивание микрофона с Silero VAD.

    Определяет начало и конец речи, собирает аудио-фрагменты
    и передаёт их в callback при завершении фразы.
    """

    def __init__(self, on_speech_end):
        self.on_speech_end = on_speech_end
        self._active = False
        self._listening = True
        self._stream = None
        self._thread = None

        torch.set_num_threads(1)
        self._vad_model = load_silero_vad(onnx=False)
        self._vad_iterator = VADIterator(
            self._vad_model,
            threshold=config.VAD_THRESHOLD,
            sampling_rate=config.SAMPLE_RATE,
            min_silence_duration_ms=config.SILENCE_DURATION_MS,
            speech_pad_ms=30,
        )

        self._buffer = np.array([], dtype=np.float32)
        self._speech_chunks: list[np.ndarray] = []
        self._is_speaking = False

    def start(self):
        self._active = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._active = False
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()

    def set_listening(self, enabled: bool):
        self._listening = enabled
        if not enabled:
            self._reset_speech()

    def _run(self):
        self._stream = sd.InputStream(
            samplerate=config.SAMPLE_RATE,
            channels=config.CHANNELS,
            dtype="float32",
            blocksize=CHUNK_SIZE,
            callback=self._audio_callback,
        )
        self._stream.start()
        while self._active:
            sd.sleep(100)

    def _audio_callback(self, indata: np.ndarray, frames, time_info, status):
        if not self._listening:
            return

        audio = indata[:, 0].copy()
        self._buffer = np.concatenate([self._buffer, audio])

        while len(self._buffer) >= CHUNK_SIZE:
            chunk = self._buffer[:CHUNK_SIZE]
            self._buffer = self._buffer[CHUNK_SIZE:]

            chunk_tensor = torch.from_numpy(chunk)
            event = self._vad_iterator(chunk_tensor, return_seconds=False)

            if event is not None:
                if "start" in event:
                    self._is_speaking = True
                    self._speech_chunks = []
                elif "end" in event:
                    self._is_speaking = False
                    self._on_utterance_complete()

            if self._is_speaking:
                self._speech_chunks.append(chunk)

    def _on_utterance_complete(self):
        if not self._speech_chunks:
            return
        audio = np.concatenate(self._speech_chunks)
        self._speech_chunks = []
        self.on_speech_end(audio)

    def _reset_speech(self):
        self._is_speaking = False
        self._speech_chunks = []
        self._buffer = np.array([], dtype=np.float32)
        self._vad_iterator.reset_states()
