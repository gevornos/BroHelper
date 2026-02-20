import re
import config


def detect_wake_word(text: str) -> str | None:
    """Проверяет текст на наличие wake-слова в начале.

    Возвращает команду (текст после wake-слова) или None.
    """
    text_lower = text.lower().strip()
    if not text_lower:
        return None

    # Убираем знаки пунктуации для сравнения
    cleaned = re.sub(r"[^\w\s]", "", text_lower)
    words = cleaned.split()
    if not words:
        return None

    for wake in config.WAKE_WORDS:
        if words[0] == wake:
            # Всё после wake-слова — команда
            command = " ".join(words[1:]).strip()
            return command if command else ""

    return None
