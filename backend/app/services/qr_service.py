import hmac
import hashlib
import secrets
import time
from sqlalchemy.orm import Session as DBSession
from app import models
from app.core.config import QR_SECRET, QR_TOKEN_TTL_SECONDS


def _sign(token: str) -> str:
    return hmac.new(QR_SECRET.encode(), token.encode(), hashlib.sha256).hexdigest()


def create_qr_session(db: DBSession, session_id: str) -> models.QRSession:
    token = secrets.token_urlsafe(24)
    qr = models.QRSession(
        token=token,
        token_hash=_sign(token),
        session_id=session_id,
        expires_at=time.time() + QR_TOKEN_TTL_SECONDS,
    )
    db.add(qr)
    db.commit()
    db.refresh(qr)
    return qr


def join_qr_session(db: DBSession, token: str) -> models.QRSession | None:
    qr = db.query(models.QRSession).filter(models.QRSession.token == token).first()
    if not qr:
        return None
    if qr.token_hash != _sign(token):
        return None  # tampered token
    if qr.expires_at < time.time():
        return None  # expired
    if qr.consumed_at is not None:
        return None  # already used - request a fresh QR
    qr.consumed_at = time.time()
    session = db.get(models.Session, qr.session_id)
    if session:
        session.status = "mobile_joined"
    db.commit()
    return qr
