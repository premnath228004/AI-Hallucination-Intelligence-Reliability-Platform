import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.document_loader import DOCUMENTS_DIR, load_corpus_file
from app.models import Chunk, Document

router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.post("/load-sample")
def load_sample(db: Session = Depends(get_db)):
    path = DOCUMENTS_DIR / "pilot_corpus_v1.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {path}")
    return load_corpus_file(db, path)


@router.get("")
def list_documents(db: Session = Depends(get_db)):
    rows = db.execute(
        select(Document, func.count(Chunk.id))
        .outerjoin(Chunk, Chunk.document_id == Document.id)
        .group_by(Document.id)
        .order_by(Document.id)
    ).all()
    return [
        {
            "id": d.id,
            "corpus": d.corpus,
            "doc_key": d.doc_key,
            "title": d.title,
            "relevant_to_questions": json.loads(d.relevant_question_ids or "[]"),
            "chunk_count": count,
        }
        for d, count in rows
    ]


@router.get("/{document_id}/chunks")
def list_chunks(document_id: int, db: Session = Depends(get_db)):
    doc = db.get(Document, document_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")
    chunks = db.scalars(
        select(Chunk).where(Chunk.document_id == document_id).order_by(Chunk.chunk_index)
    ).all()
    return {
        "document": {"id": doc.id, "doc_key": doc.doc_key, "title": doc.title, "content": doc.content},
        "chunks": [
            {"id": c.id, "chunk_index": c.chunk_index, "chunk_config": c.chunk_config,
             "char_start": c.char_start, "char_end": c.char_end, "text": c.text}
            for c in chunks
        ],
    }