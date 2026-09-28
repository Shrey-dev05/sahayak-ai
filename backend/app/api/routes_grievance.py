from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession
from app.core.db import get_db
from app import models, schemas
from app.services.grievance import draft_grievance

router = APIRouter()


@router.post("/grievance/draft", response_model=schemas.GrievanceDraftResponse)
def grievance_draft(payload: schemas.GrievanceDraftRequest, db: DBSession = Depends(get_db)):
    session = db.get(models.Session, payload.session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    draft, checklist = draft_grievance(payload.category, payload.description, payload.language or "en")
    g = models.Grievance(session_id=payload.session_id, category=payload.category,
                          complaint_text=payload.description, draft=draft)
    db.add(g)
    db.commit()
    db.refresh(g)
    return schemas.GrievanceDraftResponse(id=g.id, draft=draft, checklist=checklist)
