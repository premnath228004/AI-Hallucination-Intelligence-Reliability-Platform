from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.checker import LIMITATIONS, analyze_answer, passages_from_text
from app.database import get_db
from app.evaluator import EVALUATOR_VERSION, evaluate_reference
from app.models import Question
from app.retriever import RETRIEVER_NAME, build_retriever

router = APIRouter(prefix="/api", tags=["checker"])

BENCHMARK_MATCH_AT = 0.7


class CheckIn(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    answer: str = Field(min_length=1, max_length=5000)
    evidence: Optional[str] = Field(default=None, max_length=10000)


def _reference_check(db: Session, question_text: str, answer: str) -> dict:
    questions = db.scalars(select(Question).order_by(Question.id)).all()
    if not questions:
        return {"matched": False, "note": "No benchmark questions are loaded."}
    vectorizer = TfidfVectorizer(lowercase=True, stop_words="english")
    matrix = vectorizer.fit_transform([q.question_text for q in questions] + [question_text])
    similarities = cosine_similarity(matrix[-1], matrix[:-1]).ravel()
    best = int(similarities.argmax())
    if similarities[best] < BENCHMARK_MATCH_AT:
        return {"matched": False, "note": "Your question does not match a benchmark question, so there is no reference answer to compare with."}
    q = questions[best]
    result = evaluate_reference(
        answerable=q.answerable, category=q.category,
        reference_answer=q.reference_answer, answer_text=answer,
    )
    return {
        "matched": True,
        "benchmark_question": {"external_id": q.external_id, "question_text": q.question_text, "answerable": q.answerable},
        "similarity": round(float(similarities[best]), 3),
        "evaluator": f"reference/{EVALUATOR_VERSION}",
        "verdict": result["verdict"],
        "needs_review": result["needs_review"],
        "explanation": result["explanation"],
    }


@router.post("/check")
def check_answer(payload: CheckIn, db: Session = Depends(get_db)):
    retrieved = []
    if payload.evidence and payload.evidence.strip():
        mode = "user_evidence"
        passages = passages_from_text(payload.evidence)
    else:
        try:
            retriever = build_retriever(db)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="No evidence available. Paste evidence text, or load the corpus with POST /api/documents/load-sample.",
            )
        mode = "corpus"
        passages = [
            {"source": f"{item['doc_key']} (chunk {item['chunk_index']})", "text": item["text"]}
            for item in retriever.items
        ]
        retrieved = [
            {"rank": r["rank"], "source": f"{r['doc_key']} (chunk {r['chunk_index']})", "score": r["score"], "text": r["text"]}
            for r in retriever.search(payload.question, 3)
        ]
    return {
        "mode": mode,
        "retriever": RETRIEVER_NAME if mode == "corpus" else None,
        "reference_check": _reference_check(db, payload.question, payload.answer),
        "evidence_check": analyze_answer(payload.answer, passages),
        "retrieved_for_question": retrieved,
        "limitations": LIMITATIONS,
    }