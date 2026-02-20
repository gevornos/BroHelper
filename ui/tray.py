import logging
import threading
from PIL import Image, ImageDraw
import pystray

log = logging.getLogger(__name__)


def _create_icon_image(color: str = "#4CAF50", size: int = 64) -> Image.Image:
    """Создаёт простую иконку — круг с буквой J."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([2, 2, size - 2, size - 2], fill=color)
    # Буква J в центре
    draw.text(
        (size // 2, size // 2),
        "J",
        fill="white",
        anchor="mm",
    )
    return img


class TrayIcon:
    """Иконка в системном трее с меню управления."""

    def __init__(self, on_toggle_listening=None, on_quit=None):
        self._on_toggle_listening = on_toggle_listening
        self._on_quit = on_quit
        self._listening = True
        self._icon = None

    def start(self):
        """Запускает иконку в трее (блокирует поток)."""
        menu = pystray.Menu(
            pystray.MenuItem(
                lambda item: "Выкл. прослушивание" if self._listening else "Вкл. прослушивание",
                self._toggle_listening,
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Выход", self._quit),
        )

        self._icon = pystray.Icon(
            name="Jarvis",
            icon=_create_icon_image(),
            title="Jarvis — слушаю..." if self._listening else "Jarvis — пауза",
            menu=menu,
        )
        self._icon.run()

    def start_in_thread(self):
        """Запускает иконку в отдельном потоке."""
        thread = threading.Thread(target=self.start, daemon=True)
        thread.start()
        return thread

    def update_status(self, listening: bool):
        self._listening = listening
        if self._icon:
            color = "#4CAF50" if listening else "#9E9E9E"
            self._icon.icon = _create_icon_image(color)
            self._icon.title = "Jarvis — слушаю..." if listening else "Jarvis — пауза"

    def _toggle_listening(self, icon, item):
        self._listening = not self._listening
        self.update_status(self._listening)
        if self._on_toggle_listening:
            self._on_toggle_listening(self._listening)

    def _quit(self, icon, item):
        log.info("Выход из Jarvis")
        if self._on_quit:
            self._on_quit()
        icon.stop()
