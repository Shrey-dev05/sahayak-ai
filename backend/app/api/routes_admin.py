from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession
from app.core.db import get_db
from app import models, schemas
from app.rag.ingest import chunk_text

router = APIRouter()

# NOTE: no auth is implemented in this prototype - add real admin
# authentication (SSO / password + session) before deploying this router
# anywhere reachable by the public.


def _to_out(db: DBSession, doc: models.Document) -> schemas.DocumentOut:
    count = db.query(models.Chunk).filter(models.Chunk.document_id == doc.id).count()
    return schemas.DocumentOut(
        id=doc.id, title=doc.title, issuer=doc.issuer, source_url=doc.source_url,
        status=doc.status, version=doc.version, language=doc.language,
        last_verified_at=doc.last_verified_at, chunk_count=count,
    )


@router.get("/admin/documents", response_model=list[schemas.DocumentOut])
def list_documents(db: DBSession = Depends(get_db)):
    docs = db.query(models.Document).order_by(models.Document.created_at.desc()).all()
    return [_to_out(db, d) for d in docs]


@router.post("/admin/documents", response_model=schemas.DocumentOut)
def create_document(payload: schemas.DocumentIn, db: DBSession = Depends(get_db)):
    doc = models.Document(
        title=payload.title, issuer=payload.issuer, source_url=payload.source_url,
        language=payload.language or "en", status="pending",
        publication_date=payload.publication_date, effective_from=payload.effective_from,
        effective_to=payload.effective_to,
    )
    db.add(doc)
    db.flush()
    for piece in chunk_text(payload.text):
        db.add(models.Chunk(document_id=doc.id, text=piece))
    db.commit()
    db.refresh(doc)
    return _to_out(db, doc)


@router.post("/admin/documents/{doc_id}/approve", response_model=schemas.DocumentOut)
def approve_document(doc_id: str, db: DBSession = Depends(get_db)):
    doc = db.get(models.Document, doc_id)
    if not doc:
        raise HTTPException(404, "Document not found")
    import datetime
    doc.status = "approved"
    doc.last_verified_at = datetime.date.today().isoformat()
    db.commit()
    db.refresh(doc)
    return _to_out(db, doc)


@router.post("/admin/documents/{doc_id}/supersede", response_model=schemas.DocumentOut)
def supersede_document(doc_id: str, db: DBSession = Depends(get_db)):
    doc = db.get(models.Document, doc_id)
    if not doc:
        raise HTTPException(404, "Document not found")
    doc.status = "superseded"
    db.commit()
    db.refresh(doc)
    return _to_out(db, doc)


@router.post("/admin/documents/{doc_id}/restore", response_model=schemas.DocumentOut)
@router.post("/admin/documents/{doc_id}/undo-supersede", response_model=schemas.DocumentOut)
def restore_document(doc_id: str, db: DBSession = Depends(get_db)):
    doc = db.get(models.Document, doc_id)
    if not doc:
        raise HTTPException(404, "Document not found")
    import datetime
    doc.status = "approved"
    doc.last_verified_at = datetime.date.today().isoformat()
    db.commit()
    db.refresh(doc)
    return _to_out(db, doc)

