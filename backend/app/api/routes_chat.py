from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession
from app.core.db import get_db
from app import models, schemas
from app.ai.orchestrator import handle_message

router = APIRouter()


@router.post("/chat", response_model=schemas.ChatResponse)
def chat(payload: schemas.ChatRequest, db: DBSession = Depends(get_db)):
    session = db.get(models.Session, payload.session_id)
    if not session:
        # Seamlessly recreate session if client has a stale session ID or server restarted
        session = models.Session(id=payload.session_id, language=payload.language or "en")
        db.add(session)
        db.commit()
        db.refresh(session)
    return handle_message(db, session, payload.text, payload.language)
