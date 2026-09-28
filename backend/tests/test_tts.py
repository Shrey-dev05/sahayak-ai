import pytest
from app.speech.tts import clean_for_speech


def test_clean_for_speech_hindi():
    raw = """• 72 घंटे के अंदर 14447 पर कॉल करें
• 7/12 और आधार कार्ड लेकर PACS/CSC जाएं
• ₹5000 का दावा करें"""
    cleaned = clean_for_speech(raw, "hi")
    assert "•" not in cleaned
    assert "*" not in cleaned
    assert "1 4 4 4 7" in cleaned
    assert "सात बारह" in cleaned
    assert "5000 रुपये" in cleaned
    assert "पैक्स या C S C" in cleaned or "या" in cleaned
    assert "।" in cleaned


def test_clean_for_speech_hinglish():
    raw = """• 72 ghante me 14447 par call karein
• 7/12 aur Aadhaar lekar PACS/CSC jayein
• Call 1800-180-1551 for help"""
    cleaned = clean_for_speech(raw, "hinglish")
    assert "•" not in cleaned
    assert "1 4 4 4 7" in cleaned
    assert "Saat Baarah" in cleaned
    assert "Paks ya C S C" in cleaned
    assert "1 8 0 0, 1 8 0, 1 5 5 1" in cleaned
    assert "." in cleaned


def test_clean_for_speech_english():
    raw = """• Report within 72 hours by calling 14447
• Take 7/12 and Aadhaar to PACS/CSC center
• 10% discount on ₹5000 fee"""
    cleaned = clean_for_speech(raw, "en")
    assert "•" not in cleaned
    assert "1 4 4 4 7" in cleaned
    assert "7 12 land records" in cleaned
    assert "Paks or C S C" in cleaned
    assert "10 percent" in cleaned
    assert "5000 rupees" in cleaned


def test_voice_tts_endpoint_returns_mp3(client):
    import urllib.parse
    text = "नमस्ते किसान भाई"
    url = f"/voice/tts?text={urllib.parse.quote(text)}&language=hi"
    res = client.get(url)
    assert res.status_code == 200
    assert res.headers.get("content-type") == "audio/mpeg"
    assert len(res.content) > 1000


def test_chat_response_contains_audio_url(client):
    s = client.post("/session", json={"language": "hi"}).json()
    r = client.post("/chat", json={"session_id": s["id"], "text": "फसल बीमा कैसे मिलेगा?", "language": "hi"})
    assert r.status_code == 200
    data = r.json()
    assert "audio_url" in data
    assert data["audio_url"].startswith("/voice/tts?text=")