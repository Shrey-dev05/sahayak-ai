"""
State-of-the-art Neural TTS provider for Sahayak AI.
Generates human-like, crystal-clear speech for:
  - Hindi (हिंदी): Microsoft hi-IN-SwaraNeural / hi-IN-MadhurNeural / gTTS
  - English: Microsoft en-IN-NeerjaExpressiveNeural / gTTS
  - Hinglish: Microsoft hi-IN-SwaraNeural (native bilingual Indian voice)
"""
import os
import re
import io
import hashlib
import asyncio
from pathlib import Path
from typing import Dict, Optional
from urllib.parse import quote
try:
    import edge_tts
except ImportError:
    edge_tts = None

try:
    from gtts import gTTS
except ImportError:
    gTTS = None

ABBREVIATIONS = {
    r"\bPMFBY\b": "P M F B Y",
    r"\bKCC\b": "K C C",
    r"\bPACS\b": "Paks",
    r"\bCSC\b": "C S C",
    r"\bCSCs\b": "C S C centers",
    r"\bDBT\b": "D B T",
    r"\bAGM\b": "A G M",
    r"\bKYC\b": "K Y C",
    r"\be-KYC\b": "E K Y C",
    r"\bEMI\b": "E M I",
    r"\bFPO\b": "F P O",
    r"\bFPOs\b": "F P Os",
    r"\bGovt\b": "Government",
    r"\bgovt\b": "government",
    r"\bAIF\b": "A I F",
    r"\bSMAM\b": "S M A M",
    r"\bRs\.?\s*(\d+)": r"\1 rupees",
    r"₹\s*(\d+)": r"\1 rupees",
    r"(\d+)\s*%": r"\1 percent",
}

CACHE_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "audio_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

VOICES = {
    "hi": "hi-IN-SwaraNeural",
    "en": "en-IN-NeerjaExpressiveNeural",
}

FALLBACK_VOICES = {
    "hi": "hi-IN-MadhurNeural",
    "en": "en-IN-PrabhatNeural",
}


def clean_for_speech(text: str, language: str = "en") -> str:
    """
    Cleans markdown formatting, symbols, hashtags, asterisks, brackets, and bullet
    characters so text-to-speech speaks natural human language without reading symbols.
    Ensures natural human breathing pauses between bullet points and clear helpline numbers.
    """
    if not text:
        return ""

    lang = (language or "en").lower()

    # 1. Strip markdown links [label](url) -> label
    clean = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)
    # 2. Strip URLs
    clean = re.sub(r"https?://\S+|www\.\S+", "", clean)
    # 3. Strip bold/italic/strikethrough markers (***, **, *, __, _, ~~)
    clean = re.sub(r"[*_~`]+", "", clean)
    # 4. Strip headings (#, ##, ###)
    clean = re.sub(r"^#{1,6}\s*", "", clean, flags=re.MULTILINE)

    # 5. Format helpline numbers for clear digit-by-digit spoken delivery
    clean = re.sub(r"\b1800[- ]?180[- ]?1551\b", "1 8 0 0, 1 8 0, 1 5 5 1", clean)
    clean = re.sub(r"\b1800[- ]?11[- ]?4000\b", "1 8 0 0, 1 1, 4 0 0 0", clean)
    clean = re.sub(r"\b14447\b", "1 4 4 4 7", clean)
    clean = re.sub(r"\b1915\b", "1 9 1 5", clean)

    # 6. Scheme acronyms and domain terms
    clean = re.sub(r"\bPM-?KISAN\b", "P M Kisan", clean, flags=re.IGNORECASE)
    clean = re.sub(r"\bPMFBY\b", "P M F B Y", clean)
    clean = re.sub(r"\bKCC\b", "K C C", clean)
    clean = re.sub(r"\bCSC\b", "C S C", clean)
    clean = re.sub(r"\bCSCs\b", "C S C centers", clean)
    clean = re.sub(r"\bDBT\b", "D B T", clean)
    clean = re.sub(r"\bKYC\b", "K Y C", clean)
    clean = re.sub(r"\be-?KYC\b", "E K Y C", clean, flags=re.IGNORECASE)
    clean = re.sub(r"\bFPO\b", "F P O", clean)
    clean = re.sub(r"\bFPOs\b", "F P Os", clean)
    clean = re.sub(r"\bAIF\b", "A I F", clean)

    # 7. Language-specific natural phrasing
    if "hi" in lang:
        clean = re.sub(r"\bPACS\b", "पैक्स", clean)
        clean = re.sub(r"\b7\s*/\s*12\b", "सात बारह", clean)
        clean = re.sub(r"₹\s*(\d+)", r"\1 रुपये", clean)
        clean = re.sub(r"Rs\.?\s*(\d+)", r"\1 रुपये", clean, flags=re.IGNORECASE)
        clean = re.sub(r"(\d+)\s*%", r"\1 प्रतिशत", clean)
        # Slashes between words -> या
        clean = re.sub(r"([A-Za-z0-9\u0900-\u097F]+)/([A-Za-z0-9\u0900-\u097F]+)", r"\1 या \2", clean)
        end_punc = "।"
    else:
        clean = re.sub(r"\bPACS\b", "Paks", clean)
        clean = re.sub(r"\b7\s*/\s*12\b", "7 12 land records", clean)
        clean = re.sub(r"₹\s*(\d+)", r"\1 rupees", clean)
        clean = re.sub(r"Rs\.?\s*(\d+)", r"\1 rupees", clean, flags=re.IGNORECASE)
        clean = re.sub(r"(\d+)\s*%", r"\1 percent", clean)
        # Slashes between words -> or
        clean = re.sub(r"([A-Za-z0-9]+)/([A-Za-z0-9]+)", r"\1 or \2", clean)
        end_punc = "."

    # 8. Natural cadence & sentence pauses between bullet points and lines
    lines = [l.strip() for l in clean.split("\n") if l.strip()]
    cleaned_lines = []
    for line in lines:
        # Strip bullets (- , + , * , • )
        line = re.sub(r"^\s*[-+*•]\s+", "", line)
        # Strip numbered prefixes (1. , 1) , Step 1: , कदम 1: )
        line = re.sub(r"^\s*(?:Step|कदम)?\s*\d+[\.\):\-]\s*", "", line, flags=re.IGNORECASE)
        # Strip non-speech brackets, slashes, braces, quotes, emojis
        line = re.sub(r"[\[\]{}<>|\\()\"'`~^@#*]", " ", line)
        line = re.sub(r"[\U00010000-\U0010ffff]", "", line)
        line = re.sub(r"\s+", " ", line).strip()
        if line:
            # Ensure sentence has a natural stopping pause
            if not re.search(r"[.!?,;:।]$", line):
                line += end_punc
            cleaned_lines.append(line)

    result = " ".join(cleaned_lines)
    result = re.sub(r"[-—_=+]+", " ", result)
    result = re.sub(r"\s+", " ", result).strip()
    return result


async def generate_speech_bytes(text: str, language: str = "en") -> bytes:
    clean_text = clean_for_speech(text, language)
    if not clean_text:
        return b""

    # Cache key based on language and text
    key = hashlib.md5(f"{language}_{clean_text}".encode("utf-8")).hexdigest()
    cached_file = CACHE_DIR / f"{key}.mp3"
    if cached_file.exists():
        try:
            return cached_file.read_bytes()
        except Exception:
            pass

    lang_key = "hi" if "hi" in language.lower() else "en"
    voice = VOICES.get(lang_key, "hi-IN-SwaraNeural")
    fallback_voice = FALLBACK_VOICES.get(lang_key, "hi-IN-MadhurNeural")

    # 1. Primary: Edge Neural TTS with calm, measured, articulate rate (-3%)
    if edge_tts is not None:
        try:
            communicate = edge_tts.Communicate(clean_text, voice, rate="-3%", pitch="+0Hz")
            audio_stream = io.BytesIO()
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_stream.write(chunk["data"])
            data = audio_stream.getvalue()
            if len(data) > 1000:
                cached_file.write_bytes(data)
                return data
        except Exception:
            pass

        # 1b. Secondary Edge Neural fallback voice
        try:
            communicate = edge_tts.Communicate(clean_text, fallback_voice, rate="-3%", pitch="+0Hz")
            audio_stream = io.BytesIO()
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_stream.write(chunk["data"])
            data = audio_stream.getvalue()
            if len(data) > 1000:
                cached_file.write_bytes(data)
                return data
        except Exception:
            pass

    # 2. Tertiary fallback: Google TTS (gTTS)
    if gTTS is not None:
        try:
            gtts_lang = "hi" if lang_key == "hi" else "en"
            tld = "co.in" if gtts_lang == "en" else "com"
            tts = gTTS(clean_text, lang=gtts_lang, tld=tld)
            buf = io.BytesIO()
            tts.write_to_fp(buf)
            data = buf.getvalue()
            if len(data) > 500:
                cached_file.write_bytes(data)
                return data
        except Exception:
            pass

    return b""


class TTSProvider:
    def synthesize(self, text: str, language: str) -> dict:
        raise NotImplementedError


class NeuralTTS(TTSProvider):
    def synthesize(self, text: str, language: str) -> dict:
        clean_text = clean_for_speech(text, language)
        audio_url = f"/voice/tts?text={quote(clean_text)}&language={language}"
        return {"audio_url": audio_url, "provider": "neural_edge", "spoken_text": clean_text}


def get_tts_provider() -> TTSProvider:
    return NeuralTTS()
