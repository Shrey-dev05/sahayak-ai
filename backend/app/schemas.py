from typing import Optional, List, Any, Dict
from pydantic import BaseModel, ConfigDict


class SessionCreate(BaseModel):
    kiosk_id: Optional[str] = None
    language: Optional[str] = "en"


class SessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    kiosk_id: Optional[str]
    language: str
    status: str
    created_at: float
    expires_at: Optional[float]


class ChatRequest(BaseModel):
    session_id: str
    text: str
    language: Optional[str] = None


class SourceOut(BaseModel):
    document_id: str
    title: str
    issuer: Optional[str] = None
    source_url: Optional[str] = None
    last_verified_at: Optional[str] = None
    relevance: float


class ActionPlanOut(BaseModel):
    title: str
    steps: List[str] = []
    documents_required: List[str] = []
    warnings: List[str] = []


class ChatResponse(BaseModel):
    answer_text: str
    spoken_text: str
    kiosk_summary: Optional[str] = None
    response_mode: str  # SPEECH_ONLY | SCREEN_SUMMARY | MOBILE_HANDOFF | HUMAN_ESCALATION
    intent: str
    action_plan: Optional[ActionPlanOut] = None
    sources: List[SourceOut] = []
    qr: Optional[Dict[str, Any]] = None
    language: str
    confidence: float
    trigger_pdf: Optional[bool] = False
    audio_url: Optional[str] = None


class QRCreateRequest(BaseModel):
    session_id: str


class QRCreateResponse(BaseModel):
    token: str
    join_url: str
    expires_at: float


class QRJoinRequest(BaseModel):
    token: str


class MessageOut(BaseModel):
    role: str
    text: str
    intent: Optional[str] = None
    response_mode: Optional[str] = None
    created_at: float


class SessionContextOut(BaseModel):
    session: SessionOut
    messages: List[MessageOut]
    action_plan: Optional[ActionPlanOut] = None


class GrievanceDraftRequest(BaseModel):
    session_id: str
    category: str
    description: str
    language: Optional[str] = "en"


class GrievanceDraftResponse(BaseModel):
    id: str
    draft: str
    checklist: List[str]


class DocumentIn(BaseModel):
    title: str
    text: str
    issuer: Optional[str] = None
    source_url: Optional[str] = None
    language: Optional[str] = "en"
    publication_date: Optional[str] = None
    effective_from: Optional[str] = None
    effective_to: Optional[str] = None


class DocumentOut(BaseModel):
    id: str
    title: str
    issuer: Optional[str]
    source_url: Optional[str]
    status: str
    version: str
    language: str
    last_verified_at: Optional[str]
    chunk_count: int


class UploadOut(BaseModel):
    id: str
    session_id: str
    processing_status: str


class DocumentAnalyzeRequest(BaseModel):
    upload_id: str
    language: Optional[str] = "en"
