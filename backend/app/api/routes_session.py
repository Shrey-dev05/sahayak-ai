import time
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession
from app.core.db import get_db
from app.core.config import SESSION_TTL_SECONDS
from app import models, schemas

router = APIRouter()


@router.post("/session", response_model=schemas.SessionOut)
def create_session(payload: schemas.SessionCreate, db: DBSession = Depends(get_db)):
    s = models.Session(
        kiosk_id=payload.kiosk_id,
        language=payload.language or "en",
        expires_at=time.time() + SESSION_TTL_SECONDS,
    )
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


@router.get("/session/{session_id}", response_model=schemas.SessionContextOut)
def get_session(session_id: str, db: DBSession = Depends(get_db)):
    s = db.get(models.Session, session_id)
    if not s:
        raise HTTPException(404, "Session not found")
    messages = (
        db.query(models.Message)
        .filter(models.Message.session_id == session_id)
        .order_by(models.Message.created_at)
        .all()
    )
    plan = (
        db.query(models.ActionPlan)
        .filter(models.ActionPlan.session_id == session_id)
        .order_by(models.ActionPlan.created_at.desc())
        .first()
    )
    plan_out = None
    if plan:
        plan_out = schemas.ActionPlanOut(
            title=plan.title, steps=plan.steps,
            documents_required=plan.documents_required, warnings=plan.warnings,
        )
    return schemas.SessionContextOut(
        session=s,
        messages=[schemas.MessageOut(role=m.role, text=m.text, intent=m.intent,
                                      response_mode=m.response_mode, created_at=m.created_at)
                  for m in messages],
        action_plan=plan_out,
    )


@router.get("/session/{session_id}/action-plan", response_model=schemas.ActionPlanOut)
def get_action_plan(session_id: str, db: DBSession = Depends(get_db)):
    plan = (
        db.query(models.ActionPlan)
        .filter(models.ActionPlan.session_id == session_id)
        .order_by(models.ActionPlan.created_at.desc())
        .first()
    )
    if not plan:
        raise HTTPException(404, "No action plan for this session yet")
    return schemas.ActionPlanOut(
        title=plan.title, steps=plan.steps,
        documents_required=plan.documents_required, warnings=plan.warnings,
    )
