"""
STT provider adapter. MockSTT lets the API contract (`POST /voice/transcribe`)
be tested end-to-end without a cloud account: if the caller passes a
`hint_text` (as the demo kiosk UI does, since it already has a browser-side
transcript from the Web Speech API), the mock echoes it back as if a server
had transcribed it. Otherwise it returns a clearly-labelled placeholder.

To go live: implement CloudSTT.transcribe() against your chosen provider
(e.g. Google Cloud Speech-to-Text, Azure Speech, or a hosted Whisper
endpoint), taking raw audio bytes and returning text, and set
STT_PROVIDER=cloud.
"""
from app.core.config import STT_PROVIDER


class STTProvider:
    def transcribe(self, audio_bytes: bytes, language: str, hint_text: str | None = None) -> str:
        raise NotImplementedError


class MockSTT(STTProvider):
    def transcribe(self, audio_bytes: bytes, language: str, hint_text: str | None = None) -> str:
        if hint_text:
            return hint_text
        return "[mock transcript - connect a real STT provider to transcribe uploaded audio]"


def get_stt_provider() -> STTProvider:
    return MockSTT()  # swap for a CloudSTT() implementation when STT_PROVIDER == "cloud"
