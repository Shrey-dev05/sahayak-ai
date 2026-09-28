import uuid
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session as DBSession
from app.core.db import get_db
from app.core.config import UPLOADS_DIR
from app import models, schemas
from app.vision.ocr import get_ocr_provider
from app.ai.orchestrator import handle_message

router = APIRouter()

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "application/pdf"}
MAX_BYTES = 8 * 1024 * 1024  # 8 MB


@router.post("/upload", response_model=schemas.UploadOut)
async def upload_file(
    session_id: str = Form(...),
    file: UploadFile = File(...),
    db: DBSession = Depends(get_db),
):
    session = db.get(models.Session, session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(400, f"Unsupported file type: {file.content_type}")
    data = await file.read()
    if len(data) > MAX_BYTES:
        raise HTTPException(400, "File too large (max 8 MB in this prototype)")

    ref = f"{uuid.uuid4().hex}_{file.filename}"
    (UPLOADS_DIR / ref).write_bytes(data)

    up = models.Upload(session_id=session_id, file_ref=ref, type=file.content_type, processing_status="pending")
    db.add(up)
    db.commit()
    db.refresh(up)
    return schemas.UploadOut(id=up.id, session_id=session_id, processing_status=up.processing_status)


@router.post("/document/analyze", response_model=schemas.ChatResponse)
def analyze_document(payload: schemas.DocumentAnalyzeRequest, db: DBSession = Depends(get_db)):
    up = db.get(models.Upload, payload.upload_id)
    if not up:
        raise HTTPException(404, "Upload not found")
    session = db.get(models.Session, up.session_id)

    image_bytes = (UPLOADS_DIR / up.file_ref).read_bytes()
    extracted = get_ocr_provider().extract(image_bytes)
    up.ocr_text = extracted
    up.processing_status = "done"
    db.commit()

    # Feed the OCR text through the same orchestrator used by chat, so a
    # scanned document gets the identical evidence-first, cited response
    # a typed question would - one AI pipeline for kiosk, mobile and scans.
    return handle_message(db, session, extracted, session.language)
