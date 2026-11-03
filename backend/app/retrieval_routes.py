import json

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Dataset, Document, Question
from app.retriever import DEFAULT_CORPUS, RETRIEVER_DESCRIPTION, RETRIEVER_NAME, build_retriever

router = APIRouter(prefix="/api/retrieval", tags=["retrieval"])


def _get_retriever(db: Session):
    try:
        return build_retriever(db)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/search")
def search(q: str = Query(..., min_length=1), k: int = Query(3, ge=1, le=10), db: Session = Depends(get_db)):
    retriever = _get_retriever(db)
    return {
        "retriever": RETRIEVER_NAME,
        "description": RETRIEVER_DESCRIPTION,
        "query": q,
        "results": retriever.search(q, k),
    }


@router.get("/evaluate")
def evaluate_retrieval(dataset_id: int, k: int = Query(3, ge=1, le=10), db: Session = Depends(get_db)):
    dataset = db.get(Dataset, dataset_id)
    if dataset is None:
        raise HTTPException(status_code=404, detail="Dataset not found")
    retriever = _get_retriever(db)

    # question external_id -> set of document keys marked as relevant by the corpus author
    relevant: dict[str, set] = {}
    for doc in db.scalars(select(Document).where(Document.corpus == DEFAULT_CORPUS)).all():
        for qid in json.loads(doc.relevant_question_ids or "[]"):
            relevant.setdefault(qid, set()).add(doc.doc_key)

    questions = db.scalars(
        select(Question).where(Question.dataset_id == dataset_id).order_by(Question.id)
    ).all()

    per_question, hits, rr_sum, labelled = [], 0, 0.0, 0
    for q in questions:
        results = retriever.search(q.question_text, k)
        keys = relevant.get(q.external_id, set())
        first_rank = next((r["rank"] for r in results if r["doc_key"] in keys), None)
        if keys:
            labelled += 1
            if first_rank is not None:
                hits += 1
                rr_sum += 1 / first_rank
        per_question.append(
            {
                "external_id": q.external_id,
                "answerable": q.answerable,
                "relevant_docs": sorted(keys),
                "top_score": results[0]["score"] if results else 0.0,
                "first_relevant_rank": first_rank if keys else None,
                "hit": (first_rank is not None) if keys else None,
                "retrieved": [
                    {"rank": r["rank"], "doc_key": r["doc_key"], "chunk_index": r["chunk_index"], "score": r["score"]}
                    for r in results
                ],
            }
        )
    return {
        "retriever": RETRIEVER_NAME,
        "description": RETRIEVER_DESCRIPTION,
        "k": k,
        "questions_with_relevant_docs": labelled,
        "hit_rate_at_k": round(hits / labelled, 3) if labelled else None,
        "mrr_at_k": round(rr_sum / labelled, 3) if labelled else None,
        "per_question": per_question,
        "limitations": [
            "Tiny corpus (a few documents): high hit rates are expected and say little about real-world retrieval.",
            "Relevance labels were written by the corpus author, one relevant document per question.",
            "Lexical matching only: paraphrased questions can miss the right chunk.",
            "A high retrieval score does not mean the question is answerable from the retrieved text.",
        ],
    }