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
from ui.chat_window import ChatWindow

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

        # Окно чата
        self._chat = ChatWindow(on_user_message=self._on_chat_message)

        self._tray = TrayIcon(
            on_toggle_listening=self._on_toggle_listening,
            on_quit=self._shutdown,
            on_open_chat=self._on_open_chat,
        )

        self._processing = False
        self._running = True

    def run(self):
        """Запускает Jarvis."""
        # Запуск окна чата (скрыто)
        self._chat.start()
        self._chat.add_system_message("Jarvis запущен. Скажи wake-word или напиши сюда.")

        # Горячая клавиша — открывает/скрывает чат
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
                return

            if not command:
                command = "Привет, что умеешь?"

            log.info("Команда: %s", command)
            self._process_command(command)

        except Exception as e:
            log.error("Ошибка обработки: %s", e, exc_info=True)
        finally:
            self._processing = False

    def _on_chat_message(self, text: str):
        """Callback от окна чата — пользователь ввёл текст."""
        self._process_command(text)

    def _process_command(self, command: str):
        """Общая обработка команды (из голоса или чата)."""
        self._chat.add_user_message(command)

        self._listener.set_listening(False)
        try:
            response = self._brain.think(command)
            log.info("Ответ: %s", response)

            self._chat.add_assistant_message(response)
            self._speaker.speak(response)
        except Exception as e:
            log.error("Ошибка: %s", e, exc_info=True)
            self._chat.add_system_message(f"Ошибка: {e}")
        finally:
            self._listener.set_listening(True)

    def _on_hotkey(self):
        """Горячая клавиша — открывает/скрывает окно чата."""
        log.info("Горячая клавиша нажата")
        self._chat.toggle()

    def _on_open_chat(self):
        """Открытие чата из трея."""
        self._chat.show()

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
