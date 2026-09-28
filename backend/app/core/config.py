import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
UPLOADS_DIR = BASE_DIR / "uploads"
UPLOADS_DIR.mkdir(exist_ok=True)

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DATA_DIR / 'sahayak.db'}")
# Swap the line above for a real Postgres URL in production, e.g.:
# DATABASE_URL = "postgresql+psycopg2://user:pass@host:5432/sahayak"

QR_SECRET = os.getenv("QR_SECRET", "dev-secret-change-me")
QR_TOKEN_TTL_SECONDS = int(os.getenv("QR_TOKEN_TTL_SECONDS", "900"))  # 15 min
SESSION_TTL_SECONDS = int(os.getenv("SESSION_TTL_SECONDS", "3600"))  # 1 hour

# Provider selection: gemini | mock | anthropic | groq
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")

STT_PROVIDER = os.getenv("STT_PROVIDER", "mock")       # mock | cloud
TTS_PROVIDER = os.getenv("TTS_PROVIDER", "mock")       # mock | cloud
OCR_PROVIDER = os.getenv("OCR_PROVIDER", "mock")       # mock | cloud

SUPPORTED_LANGUAGES = ["en", "hi", "hinglish"]
DEFAULT_LANGUAGE = "en"
