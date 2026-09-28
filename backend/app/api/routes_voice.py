from fastapi import APIRouter, UploadFile, File, Form, Response, Query
from pydantic import BaseModel
from app.speech.stt import get_stt_provider
from app.speech.tts import get_tts_provider, generate_speech_bytes

router = APIRouter()


class TranscribeResponse(BaseModel):
    text: str


@router.post("/voice/transcribe", response_model=TranscribeResponse)
async def transcribe(
    audio: UploadFile = File(None),
    language: str = Form("en"),
    hint_text: str = Form(None),
):
    audio_bytes = await audio.read() if audio else b""
    text = get_stt_provider().transcribe(audio_bytes, language, hint_text)
    return TranscribeResponse(text=text)


class SynthesizeRequest(BaseModel):
    text: str
    language: str = "en"


@router.post("/voice/synthesize")
def synthesize(payload: SynthesizeRequest):
    return get_tts_provider().synthesize(payload.text, payload.language)


@router.get("/voice/tts")
async def tts_stream(text: str = Query(...), language: str = Query("en")):
    """
    Streams studio-quality neural MP3 speech.
    Supports Hindi, Hinglish (hi-IN-SwaraNeural), and English (en-IN-NeerjaExpressiveNeural).
    """
    audio_bytes = await generate_speech_bytes(text, language)
    if not audio_bytes:
        return Response(status_code=204)
    return Response(
        content=audio_bytes,
        media_type="audio/mpeg",
        headers={
            "Cache-Control": "public, max-age=86400",
            "Content-Disposition": "inline; filename=speech.mp3",
        }
    )
