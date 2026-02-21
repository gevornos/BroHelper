# Jarvis — Голосовой ИИ-ассистент

## Проект
Персональный голосовой ассистент на Windows 11 (Python).
Репо: gevornos/BroHelper

## Что делает
- Висит в трее, всегда слушает голос (русский язык)
- Активация: wake-word (брат/братан/братишка/бро/братанчик)
- Горячая клавиша Ctrl+Shift+J — открывает окно чата
- Двойной клик на трей — тоже открывает чат
- Ответы: голосом (Silero TTS) + текстом в чате
- Можно печатать команды в чате (без wake-word)
- Будет управлять Google Calendar, Gmail, Telegram

## Стек
- Python + faster-whisper (STT, medium, CPU, int8)
- Silero VAD (детекция речи)
- Claude API (claude-haiku-4-5) — мозг
- Silero TTS (голос baya)
- tkinter — окно чата
- pystray — иконка в трее
- Будущее: Google Calendar API, Gmail API, Telethon

## Архитектура
- Сейчас: всё локально, VPN для Claude API (регион заблокирован)
- Потом: VPS за рубежом (Claude напрямую, без VPN)
- Финал: Android-приложение как тонкий клиент → сервер

## Этапы
1. ~~Скелет — трей, голос→Whisper→Claude→ответ~~ DONE
2. ~~Окно чата, горячая клавиша, wake-word "братанчик"~~ DONE
3. Google Calendar — создать/посмотреть/удалить/напомнить
4. Gmail — читать письма по тегу, краткая сводка (отправка НЕ нужна)
5. Telegram — читать и отправлять сообщения в любые чаты (Telethon)
6. Полировка, Android-приложение

## Структура проекта
```
main.py              — точка входа, класс Jarvis
config.py            — конфигурация (.env, модели, промпт)
core/brain.py        — Claude API + tool-use loop
core/listener.py     — микрофон + Silero VAD
core/recognizer.py   — faster-whisper STT
core/speaker.py      — Silero TTS
core/wake_word.py    — детекция wake-word
tools/base.py        — реестр инструментов (@tool декоратор)
ui/tray.py           — системный трей (pystray)
ui/chat_window.py    — окно чата (tkinter)
services/            — пока пусто (будут интеграции)
```

## Заметки
- AMD процессор, нет мощной GPU — Whisper работает на CPU (medium/int8)
- Язык общения с пользователем: русский
- .env содержит ANTHROPIC_API_KEY (не коммитить!)
