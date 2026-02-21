import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Пути
BASE_DIR = Path(__file__).parent
MODELS_DIR = BASE_DIR / "models"
MODELS_DIR.mkdir(exist_ok=True)

# Claude API
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = "claude-haiku-4-5-20251001"
HTTPS_PROXY = os.getenv("HTTPS_PROXY", "")

# Wake words
WAKE_WORDS = ["брат", "братан", "братишка", "бро", "братанчик"]

# Whisper
WHISPER_MODEL = "medium"
WHISPER_DEVICE = "cpu"
WHISPER_COMPUTE_TYPE = "int8"
WHISPER_LANGUAGE = "ru"

# Audio
SAMPLE_RATE = 16000
CHANNELS = 1

# VAD
VAD_THRESHOLD = 0.5
SILENCE_DURATION_MS = 700  # мс тишины для конца фразы

# Hotkey
HOTKEY = "ctrl+shift+j"

# TTS
TTS_SPEAKER = "baya"  # Silero TTS голос (baya — женский, aidar — мужской)
TTS_SAMPLE_RATE = 48000

# System prompt для Claude
SYSTEM_PROMPT = """Ты — Джарвис, персональный голосовой ассистент.
Отвечай кратко и по делу, на русском языке.
Ты дружелюбный, с лёгким чувством юмора.
Обращайся к пользователю на «ты».
Если тебя попросили сделать что-то, что ты не можешь — честно скажи об этом."""
