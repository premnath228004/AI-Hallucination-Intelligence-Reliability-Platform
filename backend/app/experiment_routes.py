from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.experiment_runner import run_experiment
from app.models import Experiment, Question, Response
from app.providers import ProviderUnavailable

router = APIRouter(prefix="/api/experiments", tags=["experiments"])


class ExperimentCreate(BaseModel):
    dataset_id: int
    name: Optional[str] = None
    execution_mode: Literal["demo", "local_llm", "external_api"] = "demo"


def _summary(exp: Experiment, response_count: int) -> dict:
    return {
        "id": exp.id,
        "name": exp.name,
        "dataset_id": exp.dataset_id,
        "execution_mode": exp.execution_mode,
        "model_name": exp.model_name,
        "prompt_version": exp.prompt_version,
        "status": exp.status,
        "created_at": exp.created_at.isoformat(),
        "finished_at": exp.finished_at.isoformat() if exp.finished_at else None,
        "response_count": response_count,
    }


@router.post("", status_code=201)
def create_experiment(payload: ExperimentCreate, db: Session = Depends(get_db)):
    try:
        exp = run_experiment(db, payload.dataset_id, payload.execution_mode, payload.name)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ProviderUnavailable as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    count = db.scalar(select(func.count(Response.id)).where(Response.experiment_id == exp.id))
    return _summary(exp, count)


@router.get("")
def list_experiments(db: Session = Depends(get_db)):
    rows = db.execute(
        select(Experiment, func.count(Response.id))
        .outerjoin(Response, Response.experiment_id == Experiment.id)
        .group_by(Experiment.id)
        .order_by(Experiment.id.desc())
    ).all()
    return [_summary(exp, count) for exp, count in rows]


@router.get("/{experiment_id}/responses")
def list_responses(experiment_id: int, db: Session = Depends(get_db)):
    exp = db.get(Experiment, experiment_id)
    if exp is None:
        raise HTTPException(status_code=404, detail="Experiment not found")
    rows = db.execute(
        select(Response, Question.external_id)
        .join(Question, Question.id == Response.question_id)
        .where(Response.experiment_id == experiment_id)
        .order_by(Response.question_id, Response.strategy)
    ).all()
    return {
        "experiment": _summary(exp, len(rows)),
        "responses": [
            {
                "id": r.id,
                "question_external_id": external_id,
                "strategy": r.strategy,
                "answer_text": r.answer_text,
                "is_simulated": r.is_simulated,
                "latency_ms": r.latency_ms,
                "error_message": r.error_message,
            }
            for r, external_id in rows
        ],
    }