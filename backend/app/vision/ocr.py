"""
OCR provider adapter. MockOCR never invents document contents - it returns
an explicit placeholder rather than fabricated "extracted" text, because a
fake OCR result that looks real is more dangerous than an honest gap.

To go live: implement CloudOCR.extract() against a provider (Google Cloud
Vision, Azure Form Recognizer, or Tesseract for on-prem/offline), taking
image bytes and returning extracted text, and set OCR_PROVIDER=cloud.
"""
from app.core.config import OCR_PROVIDER


class OCRProvider:
    def extract(self, image_bytes: bytes) -> str:
        raise NotImplementedError


class MockOCR(OCRProvider):
    def extract(self, image_bytes: bytes) -> str:
        return (
            "[No real OCR provider is configured in this prototype. "
            "Connect OCR_PROVIDER=cloud with real credentials to extract "
            "text from this image.]"
        )


def get_ocr_provider() -> OCRProvider:
    return MockOCR()
