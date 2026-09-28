import uuid
import time
from sqlalchemy import Column, String, Float, Integer, Text, ForeignKey, JSON
from app.core.db import Base


def new_id(prefix=""):
    return f"{prefix}{uuid.uuid4().hex[:20]}"


def now():
    return time.time()


class Session(Base):
    __tablename__ = "sessions"
    id = Column(String, primary_key=True, default=lambda: new_id("sess_"))
    kiosk_id = Column(String, nullable=True)
    mobile_token = Column(String, nullable=True)
    language = Column(String, default="en")
    status = Column(String, default="active")  # active | mobile_joined | closed
    created_at = Column(Float, default=now)
    expires_at = Column(Float, nullable=True)


class Message(Base):
    __tablename__ = "messages"
    id = Column(String, primary_key=True, default=lambda: new_id("msg_"))
    session_id = Column(String, ForeignKey("sessions.id"), index=True)
    role = Column(String)  # user | assistant
    text = Column(Text)
    audio_ref = Column(String, nullable=True)
    intent = Column(String, nullable=True)
    confidence = Column(Float, nullable=True)
    entities = Column(JSON, default=dict)
    response_mode = Column(String, nullable=True)
    created_at = Column(Float, default=now)


class Document(Base):
    __tablename__ = "documents"
    id = Column(String, primary_key=True, default=lambda: new_id("doc_"))
    title = Column(String)
    issuer = Column(String, nullable=True)
    source_url = Column(String, nullable=True)
    version = Column(String, default="v1")
    status = Column(String, default="pending")  # pending | approved | superseded
    language = Column(String, default="en")
    publication_date = Column(String, nullable=True)
    effective_from = Column(String, nullable=True)
    effective_to = Column(String, nullable=True)
    last_verified_at = Column(String, nullable=True)
    created_at = Column(Float, default=now)


class Chunk(Base):
    __tablename__ = "chunks"
    id = Column(String, primary_key=True, default=lambda: new_id("chk_"))
    document_id = Column(String, ForeignKey("documents.id"), index=True)
    text = Column(Text)
    page = Column(Integer, nullable=True)
    section = Column(String, nullable=True)


class SourceCitation(Base):
    __tablename__ = "source_citations"
    id = Column(String, primary_key=True, default=lambda: new_id("cit_"))
    message_id = Column(String, ForeignKey("messages.id"), index=True)
    document_id = Column(String, ForeignKey("documents.id"))
    chunk_id = Column(String, ForeignKey("chunks.id"))
    relevance = Column(Float, default=0.0)


class ActionPlan(Base):
    __tablename__ = "action_plans"
    id = Column(String, primary_key=True, default=lambda: new_id("plan_"))
    session_id = Column(String, ForeignKey("sessions.id"), index=True)
    title = Column(String)
    steps = Column(JSON, default=list)
    documents_required = Column(JSON, default=list)
    warnings = Column(JSON, default=list)
    created_at = Column(Float, default=now)


class QRSession(Base):
    __tablename__ = "qr_sessions"
    token = Column(String, primary_key=True)
    token_hash = Column(String)
    session_id = Column(String, ForeignKey("sessions.id"))
    expires_at = Column(Float)
    consumed_at = Column(Float, nullable=True)


class Grievance(Base):
    __tablename__ = "grievances"
    id = Column(String, primary_key=True, default=lambda: new_id("griev_"))
    session_id = Column(String, ForeignKey("sessions.id"), index=True)
    category = Column(String)
    complaint_text = Column(Text)
    draft = Column(Text)
    status = Column(String, default="drafted")
    created_at = Column(Float, default=now)


class Upload(Base):
    __tablename__ = "uploads"
    id = Column(String, primary_key=True, default=lambda: new_id("up_"))
    session_id = Column(String, ForeignKey("sessions.id"), index=True)
    file_ref = Column(String)
    type = Column(String, nullable=True)
    ocr_text = Column(Text, nullable=True)
    processing_status = Column(String, default="pending")  # pending|processing|done|failed
    created_at = Column(Float, default=now)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(String, primary_key=True, default=lambda: new_id("log_"))
    actor = Column(String, default="system")
    action = Column(String)
    object_type = Column(String)
    object_id = Column(String)
    timestamp = Column(Float, default=now)
