import json

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.warehouse_etl import run_etl
from app.warehouse_models import (
    DimDataset,
    DimExperiment,
    DimQuestion,
    DimStrategy,
    DimVerdict,
    EtlRunLog,
    FactResponseEvaluation,
)

router = APIRouter(prefix="/api/warehouse", tags=["warehouse"])


@router.post("/refresh")
def refresh_warehouse(db: Session = Depends(get_db)):
    """Run the ETL: load operational data into the warehouse tables. Safe to repeat."""
    return run_etl(db)


@router.get("/runs")
def list_runs(db: Session = Depends(get_db)):
    runs = db.scalars(select(EtlRunLog).order_by(EtlRunLog.run_id.desc()).limit(20)).all()
    return [
        {
            "run_id": r.run_id,
            "status": r.status,
            "started_at": r.started_at.isoformat(),
            "finished_at": r.finished_at.isoformat() if r.finished_at else None,
            "counts": json.loads(r.counts_json) if r.counts_json else None,
            "reconciliation_passed": all(c["passed"] for c in json.loads(r.reconciliation_json))
            if r.reconciliation_json else None,
            "rejected_count": len(json.loads(r.rejected_json)) if r.rejected_json else None,
            "error_message": r.error_message,
        }
        for r in runs
    ]


@router.get("/summary")
def warehouse_summary(db: Session = Depends(get_db)):
    counts = {
        model.__tablename__: db.scalar(select(func.count()).select_from(model))
        for model in (DimDataset, DimQuestion, DimStrategy, DimExperiment, DimVerdict, FactResponseEvaluation)
    }
    rows = db.execute(
        select(
            DimExperiment.experiment_id,
            DimExperiment.execution_mode,
            DimStrategy.strategy_name,
            func.count(),
            func.sum(FactResponseEvaluation.is_correct),
        )
        .select_from(FactResponseEvaluation)
        .join(DimExperiment, DimExperiment.experiment_key == FactResponseEvaluation.experiment_key)
        .join(DimStrategy, DimStrategy.strategy_key == FactResponseEvaluation.strategy_key)
        .group_by(DimExperiment.experiment_id, DimExperiment.execution_mode, DimStrategy.strategy_name)
        .order_by(DimExperiment.experiment_id, DimStrategy.strategy_name)
    ).all()
    return {
        "table_row_counts": counts,
        "correct_by_experiment_and_strategy": [
            {"experiment_id": e, "execution_mode": mode, "strategy": s, "responses": n, "correct": int(c or 0)}
            for e, mode, s, n, c in rows
        ],
        "note": "Demo-mode experiments contain simulated fixture outputs, not real model results.",
    }