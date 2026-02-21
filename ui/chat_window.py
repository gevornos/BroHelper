import tkinter as tk
from tkinter import scrolledtext
import threading
import logging

log = logging.getLogger(__name__)


class ChatWindow:
    """Окно чата Jarvis — показывает диалог и принимает текстовый ввод."""

    def __init__(self, on_user_message=None):
        """
        Args:
            on_user_message: callback(text: str) — вызывается при отправке текста.
        """
        self._on_user_message = on_user_message
        self._root = None
        self._chat_display = None
        self._input_field = None
        self._visible = False
        self._ready = threading.Event()

    def start(self):
        """Запускает Tk mainloop в отдельном потоке."""
        thread = threading.Thread(target=self._run, daemon=True)
        thread.start()
        self._ready.wait(timeout=5)

    def _run(self):
        self._root = tk.Tk()
        self._root.title("Jarvis")
        self._root.geometry("500x600")
        self._root.configure(bg="#1e1e1e")

        # Не уничтожаем окно при закрытии — просто прячем
        self._root.protocol("WM_DELETE_WINDOW", self.hide)

        self._build_ui()

        # Начинаем скрытым
        self._root.withdraw()
        self._visible = False

        self._ready.set()
        self._root.mainloop()

    def _build_ui(self):
        # Область чата
        chat_frame = tk.Frame(self._root, bg="#1e1e1e")
        chat_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(10, 5))

        self._chat_display = scrolledtext.ScrolledText(
            chat_frame,
            wrap=tk.WORD,
            state=tk.DISABLED,
            bg="#2d2d2d",
            fg="#ffffff",
            font=("Consolas", 11),
            relief=tk.FLAT,
            padx=10,
            pady=10,
            insertbackground="#ffffff",
            selectbackground="#4a6fa5",
        )
        self._chat_display.pack(fill=tk.BOTH, expand=True)

        # Теги для стилей сообщений
        self._chat_display.tag_configure("user", foreground="#6cb6ff")
        self._chat_display.tag_configure("assistant", foreground="#d4d4d4")
        self._chat_display.tag_configure("label_user", foreground="#4a9eff", font=("Consolas", 10, "bold"))
        self._chat_display.tag_configure("label_assistant", foreground="#8b8b8b", font=("Consolas", 10, "bold"))
        self._chat_display.tag_configure("system", foreground="#6a9955", font=("Consolas", 10, "italic"))

        # Поле ввода
        input_frame = tk.Frame(self._root, bg="#1e1e1e")
        input_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        self._input_field = tk.Entry(
            input_frame,
            bg="#3c3c3c",
            fg="#ffffff",
            font=("Consolas", 11),
            relief=tk.FLAT,
            insertbackground="#ffffff",
        )
        self._input_field.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=8)
        self._input_field.bind("<Return>", self._on_submit)

        send_btn = tk.Button(
            input_frame,
            text="➤",
            command=lambda: self._on_submit(None),
            bg="#4a9eff",
            fg="#ffffff",
            font=("Consolas", 14),
            relief=tk.FLAT,
            padx=12,
            cursor="hand2",
        )
        send_btn.pack(side=tk.RIGHT, padx=(8, 0), ipady=2)

    def _on_submit(self, event):
        text = self._input_field.get().strip()
        if not text:
            return
        self._input_field.delete(0, tk.END)
        if self._on_user_message:
            threading.Thread(
                target=self._on_user_message, args=(text,), daemon=True
            ).start()

    def show(self):
        """Показывает окно чата."""
        if self._root:
            self._root.after(0, self._do_show)

    def _do_show(self):
        self._root.deiconify()
        self._root.lift()
        self._root.focus_force()
        self._input_field.focus_set()
        self._visible = True

    def hide(self):
        """Скрывает окно чата."""
        if self._root:
            self._root.after(0, self._do_hide)

    def _do_hide(self):
        self._root.withdraw()
        self._visible = False

    def toggle(self):
        """Переключает видимость окна."""
        if self._visible:
            self.hide()
        else:
            self.show()

    def add_user_message(self, text: str):
        """Добавляет сообщение пользователя в чат."""
        if self._root:
            self._root.after(0, self._append_message, "Ты", text, "label_user", "user")

    def add_assistant_message(self, text: str):
        """Добавляет ответ ассистента в чат."""
        if self._root:
            self._root.after(0, self._append_message, "Jarvis", text, "label_assistant", "assistant")

    def add_system_message(self, text: str):
        """Добавляет системное сообщение."""
        if self._root:
            self._root.after(0, self._append_system, text)

    def _append_message(self, label: str, text: str, label_tag: str, text_tag: str):
        self._chat_display.configure(state=tk.NORMAL)
        self._chat_display.insert(tk.END, f"{label}:\n", label_tag)
        self._chat_display.insert(tk.END, f"{text}\n\n", text_tag)
        self._chat_display.configure(state=tk.DISABLED)
        self._chat_display.see(tk.END)

    def _append_system(self, text: str):
        self._chat_display.configure(state=tk.NORMAL)
        self._chat_display.insert(tk.END, f"{text}\n\n", "system")
        self._chat_display.configure(state=tk.DISABLED)
        self._chat_display.see(tk.END)

    @property
    def visible(self) -> bool:
        return self._visible
