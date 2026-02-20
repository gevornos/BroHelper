import logging
import threading
import sys

import keyboard

import config
from core.listener import Listener
from core.recognizer import Recognizer
from core.wake_word import detect_wake_word
from core.brain import Brain
from core.speaker import Speaker
from tools.base import register_tools_to_brain
from ui.tray import TrayIcon

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("jarvis")


class Jarvis:
    def __init__(self):
        log.info("Инициализация Jarvis...")

        self._recognizer = Recognizer()
        log.info("Whisper загружен")

        self._brain = Brain()
        register_tools_to_brain(self._brain)
        log.info("Claude API готов")

        self._speaker = Speaker()
        self._speaker.load()

        self._listener = Listener(on_speech_end=self._on_speech)

        self._tray = TrayIcon(
            on_toggle_listening=self._on_toggle_listening,
            on_quit=self._shutdown,
        )

        self._processing = False
        self._running = True

    def run(self):
        """Запускает Jarvis."""
        # Горячая клавиша как резерв
        keyboard.add_hotkey(config.HOTKEY, self._on_hotkey)
        log.info("Горячая клавиша: %s", config.HOTKEY)

        # Запуск прослушивания
        self._listener.start()
        log.info("Прослушивание запущено (wake-слова: %s)", ", ".join(config.WAKE_WORDS))

        log.info("Jarvis готов!")

        # Трей работает в главном потоке (требование pystray на Windows)
        self._tray.start()

    def _on_speech(self, audio):
        """Callback от listener — речь закончилась."""
        if self._processing:
            return

        self._processing = True
        thread = threading.Thread(target=self._process_audio, args=(audio,), daemon=True)
        thread.start()

    def _process_audio(self, audio):
        """Обрабатывает аудио: STT → wake-word → Claude → TTS."""
        try:
            text = self._recognizer.transcribe(audio)
            if not text:
                return

            log.info("Распознано: %s", text)

            command = detect_wake_word(text)
            if command is None:
                # Wake-слово не найдено — игнорируем
                return

            if not command:
                # Wake-слово без команды ("Братан!")
                command = "Привет, что умеешь?"

            log.info("Команда: %s", command)

            # Отключаем микрофон на время ответа, чтобы не слышать себя
            self._listener.set_listening(False)

            response = self._brain.think(command)
            log.info("Ответ: %s", response)

            self._speaker.speak(response)

        except Exception as e:
            log.error("Ошибка обработки: %s", e, exc_info=True)
        finally:
            self._listener.set_listening(True)
            self._processing = False

    def _on_hotkey(self):
        """Активация по горячей клавише Ctrl+Shift+J."""
        if self._processing:
            return
        log.info("Горячая клавиша нажата — слушаю...")
        # При нажатии горячей клавиши — просто ждём следующую фразу
        # Listener уже работает, wake-word не нужен
        # TODO: добавить режим "следующая фраза без wake-word"

    def _on_toggle_listening(self, enabled: bool):
        """Переключение прослушивания из трея."""
        self._listener.set_listening(enabled)
        state = "включено" if enabled else "выключено"
        log.info("Прослушивание %s", state)

    def _shutdown(self):
        """Корректное завершение."""
        log.info("Завершение Jarvis...")
        self._running = False
        self._listener.stop()
        keyboard.unhook_all()
        sys.exit(0)


if __name__ == "__main__":
    jarvis = Jarvis()
    jarvis.run()
