from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dataset_loader import BENCHMARK_DIR, load_dataset_file
from app.models import Dataset, Question

router = APIRouter(prefix="/api/datasets", tags=["datasets"])


@router.post("/load-sample")
def load_sample(db: Session = Depends(get_db)):
    path = BENCHMARK_DIR / "sample_v1.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {path}")
    return load_dataset_file(db, path)


@router.get("")
def list_datasets(db: Session = Depends(get_db)):
    rows = db.execute(
        select(Dataset, func.count(Question.id))
        .outerjoin(Question, Question.dataset_id == Dataset.id)
        .group_by(Dataset.id)
        .order_by(Dataset.id)
    ).all()
    return [
        {
            "id": d.id,
            "name": d.name,
            "version": d.version,
            "description": d.description,
            "provenance": d.provenance,
            "question_count": count,
        }
        for d, count in rows
    ]


@router.get("/{dataset_id}/questions")
def list_questions(dataset_id: int, db: Session = Depends(get_db)):
    dataset = db.get(Dataset, dataset_id)
    if dataset is None:
        raise HTTPException(status_code=404, detail="Dataset not found")
    questions = db.scalars(
        select(Question).where(Question.dataset_id == dataset_id).order_by(Question.id)
    ).all()
    return {
        "dataset": {"id": dataset.id, "name": dataset.name, "version": dataset.version},
        "questions": [
            {
                "id": q.id,
                "external_id": q.external_id,
                "question_text": q.question_text,
                "reference_answer": q.reference_answer,
                "category": q.category,
                "answerable": q.answerable,
                "source_note": q.source_note,
            }
            for q in questions
        ],
    }