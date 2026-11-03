from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.evaluation_routes import CORRECT_VERDICTS, _evaluations_by_response
from app.models import Chunk, Document, Experiment, Question, Response, Retrieval
from app.retriever import RETRIEVER_DESCRIPTION, RETRIEVER_NAME, load_relevance_map

router = APIRouter(prefix="/api/experiments", tags=["rag"])


def _hint(answerable: bool, retrieval_hit, verdict, n_retrieved: int):
    """Review hints only. These are candidates, never final failure labels."""
    if verdict is None:
        return "Not evaluated yet. Run POST /api/experiments/{id}/evaluate first."
    if answerable:
        if retrieval_hit is False and verdict not in CORRECT_VERDICTS:
            return "Candidate retrieval failure: the relevant document was not retrieved. Review."
        if retrieval_hit and verdict == "incorrect_abstention":
            return "Candidate evidence interpretation error: relevant evidence was retrieved but the answer abstained. Review."
        if retrieval_hit and verdict in ("reference_mismatch", "incorrect"):
            return "Candidate evidence interpretation error: relevant evidence was retrieved but the answer does not match the reference. Review."
    elif verdict == "failure_to_abstain":
        return (
            f"Candidate unsupported claim: an answer was given for an unanswerable question "
            f"({n_retrieved} chunks retrieved, none marked as evidence). Review."
        )
    return None


@router.get("/{experiment_id}/rag-inspection")
def rag_inspection(experiment_id: int, db: Session = Depends(get_db)):
    exp = db.get(Experiment, experiment_id)
    if exp is None:
        raise HTTPException(status_code=404, detail="Experiment not found")

    reference, human = _evaluations_by_response(db, experiment_id)
    relevance = load_relevance_map(db)

    rows = db.execute(
        select(Response, Question)
        .join(Question, Question.id == Response.question_id)
        .where(Response.experiment_id == experiment_id, Response.strategy == "rag")
        .order_by(Response.id)
    ).all()

    retrieved_by_response: dict[int, list] = {}
    for retrieval, chunk, doc in db.execute(
        select(Retrieval, Chunk, Document)
        .join(Chunk, Chunk.id == Retrieval.chunk_id)
        .join(Document, Document.id == Chunk.document_id)
        .join(Response, Response.id == Retrieval.response_id)
        .where(Response.experiment_id == experiment_id)
        .order_by(Retrieval.response_id, Retrieval.rank)
    ).all():
        retrieved_by_response.setdefault(retrieval.response_id, []).append(
            {
                "rank": retrieval.rank,
                "doc_key": doc.doc_key,
                "chunk_index": chunk.chunk_index,
                "score": retrieval.score,
                "text": chunk.text,
            }
        )

    items, labelled, hits = [], 0, 0
    for response, question in rows:
        effective = human.get(response.id) or reference.get(response.id)
        verdict = effective.verdict if effective else None
        keys = relevance.get(question.external_id, set())
        retrieved = retrieved_by_response.get(response.id, [])
        retrieval_hit = bool(keys & {r["doc_key"] for r in retrieved}) if keys else None
        if keys:
            labelled += 1
            hits += 1 if retrieval_hit else 0
        items.append(
            {
                "response_id": response.id,
                "question_external_id": question.external_id,
                "question_text": question.question_text,
                "answerable": question.answerable,
                "answer_text": response.answer_text,
                "verdict": verdict,
                "relevant_docs": sorted(keys),
                "retrieval_hit": retrieval_hit,
                "diagnostic_hint": _hint(question.answerable, retrieval_hit, verdict, len(retrieved)),
                "retrieved": retrieved,
            }
        )

    return {
        "experiment": {"id": exp.id, "name": exp.name, "execution_mode": exp.execution_mode, "model_name": exp.model_name},
        "retriever": RETRIEVER_NAME,
        "retriever_description": RETRIEVER_DESCRIPTION,
        "answer_note": (
            "Demo mode: RAG answers are simulated fixtures and were not generated from the retrieved chunks."
            if exp.execution_mode == "demo" else None
        ),
        "questions_with_relevant_docs": labelled,
        "retrieval_hit_rate": round(hits / labelled, 3) if labelled else None,
        "items": items,
        "limitations": [
            "Diagnostic hints are candidates for manual review, not final failure labels.",
            "A claim is not called unsupported just because it is absent from one retrieved passage.",
            "Relevance labels are author-assigned (one relevant document per question) on a tiny corpus.",
            "Contradicted and unverifiable claims need claim-level or LLM-judge evaluation, which is not implemented yet.",
        ],
    }