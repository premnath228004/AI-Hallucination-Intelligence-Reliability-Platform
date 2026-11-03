from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.evaluator import EVALUATOR_VERSION, evaluate_reference, wilson_interval
from app.models import Evaluation, Experiment, Question, Response

router = APIRouter(prefix="/api", tags=["evaluation"])

HUMAN_VERSION = "manual-v1"
CORRECT_VERDICTS = ("correct", "correct_abstention")


def _get_experiment(db: Session, experiment_id: int) -> Experiment:
    exp = db.get(Experiment, experiment_id)
    if exp is None:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return exp


def _rows(db: Session, experiment_id: int):
    return db.execute(
        select(Response, Question)
        .join(Question, Question.id == Response.question_id)
        .where(Response.experiment_id == experiment_id)
        .order_by(Response.id)
    ).all()


def _evaluations_by_response(db: Session, experiment_id: int):
    evals = db.scalars(
        select(Evaluation)
        .join(Response, Response.id == Evaluation.response_id)
        .where(
            Response.experiment_id == experiment_id,
            Evaluation.evaluator_type.in_(["reference", "human"]),
        )
    ).all()
    reference, human = {}, {}
    for e in evals:
        if e.evaluator_type == "reference" and e.evaluator_version == EVALUATOR_VERSION:
            reference[e.response_id] = e
        elif e.evaluator_type == "human" and e.evaluator_version == HUMAN_VERSION:
            human[e.response_id] = e
    return reference, human


@router.post("/experiments/{experiment_id}/evaluate")
def evaluate_experiment(experiment_id: int, db: Session = Depends(get_db)):
    _get_experiment(db, experiment_id)
    already = set(
        db.scalars(
            select(Evaluation.response_id)
            .join(Response, Response.id == Evaluation.response_id)
            .where(
                Response.experiment_id == experiment_id,
                Evaluation.evaluator_type == "reference",
                Evaluation.evaluator_version == EVALUATOR_VERSION,
            )
        ).all()
    )
    stats = {
        "evaluator": f"reference/{EVALUATOR_VERSION}",
        "inserted": 0,
        "skipped_existing": 0,
        "skipped_no_answer": 0,
    }
    for response, question in _rows(db, experiment_id):
        if response.id in already:
            stats["skipped_existing"] += 1
            continue
        if response.error_message or response.answer_text is None:
            stats["skipped_no_answer"] += 1
            continue
        result = evaluate_reference(
            answerable=question.answerable,
            category=question.category,
            reference_answer=question.reference_answer,
            answer_text=response.answer_text,
        )
        db.add(
            Evaluation(
                response_id=response.id,
                evaluator_type="reference",
                evaluator_version=EVALUATOR_VERSION,
                **result,
            )
        )
        stats["inserted"] += 1
    db.commit()
    return stats


@router.get("/experiments/{experiment_id}/evaluations")
def list_evaluations(experiment_id: int, needs_review_only: bool = False, db: Session = Depends(get_db)):
    _get_experiment(db, experiment_id)
    reference, human = _evaluations_by_response(db, experiment_id)
    items = []
    for response, question in _rows(db, experiment_id):
        r, h = reference.get(response.id), human.get(response.id)
        if needs_review_only and not (r is not None and r.needs_review and h is None):
            continue
        items.append(
            {
                "response_id": response.id,
                "question_external_id": question.external_id,
                "question_text": question.question_text,
                "reference_answer": question.reference_answer,
                "answerable": question.answerable,
                "strategy": response.strategy,
                "answer_text": response.answer_text,
                "reference_verdict": r.verdict if r else None,
                "needs_review": r.needs_review if r else None,
                "reference_explanation": r.explanation if r else None,
                "human_verdict": h.verdict if h else None,
                "human_note": h.explanation if h else None,
            }
        )
    return {"count": len(items), "items": items}


class ReviewIn(BaseModel):
    response_id: int
    verdict: Literal["correct", "correct_abstention", "incorrect", "incorrect_abstention", "failure_to_abstain"]
    failure_category: Optional[str] = None
    note: Optional[str] = None


@router.post("/evaluations/review")
def review_response(payload: ReviewIn, db: Session = Depends(get_db)):
    if db.get(Response, payload.response_id) is None:
        raise HTTPException(status_code=404, detail="Response not found")
    score = 1.0 if payload.verdict in CORRECT_VERDICTS else 0.0
    category = payload.failure_category or (None if score == 1.0 else payload.verdict)
    existing = db.scalar(
        select(Evaluation).where(
            Evaluation.response_id == payload.response_id,
            Evaluation.evaluator_type == "human",
            Evaluation.evaluator_version == HUMAN_VERSION,
        )
    )
    if existing:
        existing.verdict = payload.verdict
        existing.correctness_score = score
        existing.failure_category = category
        existing.explanation = payload.note
        action = "updated"
    else:
        db.add(
            Evaluation(
                response_id=payload.response_id,
                evaluator_type="human",
                evaluator_version=HUMAN_VERSION,
                verdict=payload.verdict,
                correctness_score=score,
                failure_category=category,
                needs_review=False,
                explanation=payload.note,
            )
        )
        action = "created"
    db.commit()
    return {"response_id": payload.response_id, "human_verdict": payload.verdict, "action": action}


@router.get("/experiments/{experiment_id}/summary")
def experiment_summary(experiment_id: int, db: Session = Depends(get_db)):
    exp = _get_experiment(db, experiment_id)
    reference, human = _evaluations_by_response(db, experiment_id)
    per: dict = {}
    for response, question in _rows(db, experiment_id):
        s = per.setdefault(
            response.strategy,
            {"responses": 0, "evaluated": 0, "correct": 0, "human_reviewed": 0, "pending_review": 0,
             "correct_abstentions": 0, "incorrect_abstentions": 0, "failures_to_abstain": 0,
             "verdicts": {}, "latencies": []},
        )
        s["responses"] += 1
        h, r = human.get(response.id), reference.get(response.id)
        effective = h or r  # a human verdict overrides the automatic one
        if effective is None:
            continue
        s["evaluated"] += 1
        s["verdicts"][effective.verdict] = s["verdicts"].get(effective.verdict, 0) + 1
        if effective.verdict in CORRECT_VERDICTS:
            s["correct"] += 1
        if effective.verdict == "correct_abstention":
            s["correct_abstentions"] += 1
        if effective.verdict == "incorrect_abstention":
            s["incorrect_abstentions"] += 1
        if effective.verdict == "failure_to_abstain":
            s["failures_to_abstain"] += 1
        if h is not None:
            s["human_reviewed"] += 1
        elif r.needs_review:
            s["pending_review"] += 1
        if response.latency_ms is not None:
            s["latencies"].append(response.latency_ms)

    is_demo = exp.execution_mode == "demo"
    strategies = {}
    for name in ("basic", "improved", "rag"):
        s = per.get(name)
        if s is None:
            continue
        n = s["evaluated"]
        ci = wilson_interval(s["correct"], n)
        strategies[name] = {
            "responses": s["responses"],
            "evaluated": n,
            "correct": s["correct"],
            "accuracy_provisional": round(s["correct"] / n, 3) if n else None,
            "accuracy_95ci_wilson": [round(ci[0], 3), round(ci[1], 3)] if ci else None,
            "verdict_counts": s["verdicts"],
            "correct_abstentions": s["correct_abstentions"],
            "incorrect_abstentions": s["incorrect_abstentions"],
            "failures_to_abstain": s["failures_to_abstain"],
            "human_reviewed": s["human_reviewed"],
            "pending_manual_review": s["pending_review"],
            "avg_latency_ms": None if is_demo or not s["latencies"] else round(sum(s["latencies"]) / len(s["latencies"]), 1),
        }
    return {
        "experiment": {"id": exp.id, "name": exp.name, "execution_mode": exp.execution_mode,
                       "model_name": exp.model_name, "prompt_version": exp.prompt_version},
        "evaluator": f"reference/{EVALUATOR_VERSION} + human overrides",
        "strategies": strategies,
        "latency_note": "Latency is not reported for demo mode: it measures a fixture lookup, not a model." if is_demo else None,
        "not_yet_measured": ["evidence grounding", "unsupported claims", "relevance", "completeness", "retrieval quality"],
        "limitations": [
            "Rule-based string matching cannot understand meaning; paraphrases can be marked wrong and hedged answers can be marked right.",
            "accuracy_provisional includes unreviewed automatic verdicts; see pending_manual_review.",
            "Small samples give very wide intervals; no statistical significance is claimed.",
            "Wilson intervals assume independent questions and do not cover errors in the reference answers.",
        ],
    }