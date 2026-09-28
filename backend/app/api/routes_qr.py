from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session as DBSession
from app.core.db import get_db
from app import models, schemas
from app.services.qr_service import create_qr_session, join_qr_session

router = APIRouter()


@router.post("/qr/create", response_model=schemas.QRCreateResponse)
def qr_create(payload: schemas.QRCreateRequest, request: Request, db: DBSession = Depends(get_db)):
    session = db.get(models.Session, payload.session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    qr = create_qr_session(db, payload.session_id)
    base = str(request.base_url).rstrip("/")
    join_url = f"{base}/mobile/?token={qr.token}"
    return schemas.QRCreateResponse(token=qr.token, join_url=join_url, expires_at=qr.expires_at)


@router.post("/qr/join", response_model=schemas.SessionContextOut)
def qr_join(payload: schemas.QRJoinRequest, db: DBSession = Depends(get_db)):
    qr = join_qr_session(db, payload.token)
    if not qr:
        raise HTTPException(410, "This QR code is invalid, expired, or already used.")
    session = db.get(models.Session, qr.session_id)
    messages = (
        db.query(models.Message)
        .filter(models.Message.session_id == session.id)
        .order_by(models.Message.created_at)
        .all()
    )
    plan = (
        db.query(models.ActionPlan)
        .filter(models.ActionPlan.session_id == session.id)
        .order_by(models.ActionPlan.created_at.desc())
        .first()
    )
    plan_out = None
    if plan:
        plan_out = schemas.ActionPlanOut(title=plan.title, steps=plan.steps,
                                          documents_required=plan.documents_required, warnings=plan.warnings)
    return schemas.SessionContextOut(
        session=session,
        messages=[schemas.MessageOut(role=m.role, text=m.text, intent=m.intent,
                                      response_mode=m.response_mode, created_at=m.created_at)
                  for m in messages],
        action_plan=plan_out,
    )
