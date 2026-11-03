import json

from fastapi import APIRouter, Depends, Query
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


@router.get("/report")
def warehouse_report(
    dataset_id: int | None = Query(default=None, ge=1),
    experiment_id: int | None = Query(default=None, ge=1),
    strategy: str | None = None,
    verdict_group: str | None = None,
    execution_mode: str | None = None,
    db: Session = Depends(get_db),
):
    """Return slicer options and warehouse aggregates for the interactive report."""
    fact = FactResponseEvaluation
    joined = (
        select(fact, DimExperiment, DimQuestion, DimStrategy, DimVerdict, DimDataset)
        .select_from(fact)
        .join(DimExperiment, DimExperiment.experiment_key == fact.experiment_key)
        .join(DimQuestion, DimQuestion.question_key == fact.question_key)
        .join(DimStrategy, DimStrategy.strategy_key == fact.strategy_key)
        .join(DimVerdict, DimVerdict.verdict_key == fact.verdict_key)
        .join(DimDataset, DimDataset.dataset_key == DimQuestion.dataset_key)
    )
    filters = []
    if dataset_id is not None:
        filters.append(DimDataset.dataset_id == dataset_id)
    if experiment_id is not None:
        filters.append(DimExperiment.experiment_id == experiment_id)
    if strategy:
        filters.append(DimStrategy.strategy_name == strategy)
    if verdict_group:
        filters.append(DimVerdict.verdict_group == verdict_group)
    if execution_mode:
        filters.append(DimExperiment.execution_mode == execution_mode)
    if filters:
        joined = joined.where(*filters)

    summary = db.execute(
        joined.with_only_columns(
            func.count(fact.response_id),
            func.coalesce(func.sum(fact.is_correct), 0),
            func.coalesce(func.sum(fact.needs_review), 0),
            func.coalesce(func.sum(fact.human_reviewed), 0),
            func.coalesce(func.sum(fact.is_simulated), 0),
            func.count(fact.retrieval_hit),
            func.coalesce(func.sum(fact.retrieval_hit), 0),
            func.avg(fact.retrieval_top_score),
            func.avg(fact.latency_ms),
        )
    ).one()
    total, correct, needs_review, human_reviewed, simulated, retrieval_measured, retrieval_hits, retrieval_score, latency = summary

    strategy_rows = db.execute(
        joined.with_only_columns(
            DimStrategy.strategy_name,
            DimStrategy.strategy_label,
            func.count(fact.response_id),
            func.coalesce(func.sum(fact.is_correct), 0),
            func.coalesce(func.sum(fact.needs_review), 0),
            func.coalesce(func.sum(fact.human_reviewed), 0),
            func.count(fact.retrieval_hit),
            func.coalesce(func.sum(fact.retrieval_hit), 0),
        )
        .group_by(DimStrategy.strategy_name, DimStrategy.strategy_label)
        .order_by(DimStrategy.strategy_name)
    ).all()
    verdict_rows = db.execute(
        joined.with_only_columns(
            DimVerdict.verdict_group,
            func.count(fact.response_id),
        )
        .group_by(DimVerdict.verdict_group)
        .order_by(func.count(fact.response_id).desc(), DimVerdict.verdict_group)
    ).all()
    question_rows = db.execute(
        joined.with_only_columns(
            DimQuestion.external_id,
            DimQuestion.question_text,
            DimQuestion.category,
            func.count(fact.response_id),
            func.coalesce(func.sum(1 - fact.is_correct), 0),
            func.coalesce(func.sum(fact.needs_review), 0),
        )
        .group_by(DimQuestion.external_id, DimQuestion.question_text, DimQuestion.category)
        .order_by(func.sum(1 - fact.is_correct).desc(), DimQuestion.external_id)
        .limit(10)
    ).all()
    last_run = db.scalar(select(EtlRunLog).order_by(EtlRunLog.run_id.desc()).limit(1))

    return {
        "filters": {
            "datasets": [
                {"id": item.dataset_id, "name": item.dataset_name, "version": item.dataset_version}
                for item in db.scalars(select(DimDataset).order_by(DimDataset.dataset_name, DimDataset.dataset_version)).all()
            ],
            "experiments": [
                {"id": item.experiment_id, "name": item.experiment_name, "execution_mode": item.execution_mode}
                for item in db.scalars(select(DimExperiment).order_by(DimExperiment.experiment_id.desc())).all()
            ],
            "strategies": [
                {"name": name, "label": label}
                for name, label in db.execute(
                    select(DimStrategy.strategy_name, DimStrategy.strategy_label).order_by(DimStrategy.strategy_name)
                ).all()
            ],
            "verdict_groups": list(
                db.scalars(select(DimVerdict.verdict_group).distinct().order_by(DimVerdict.verdict_group)).all()
            ),
            "execution_modes": list(
                db.scalars(select(DimExperiment.execution_mode).distinct().order_by(DimExperiment.execution_mode)).all()
            ),
        },
        "selection": {
            "dataset_id": dataset_id,
            "experiment_id": experiment_id,
            "strategy": strategy,
            "verdict_group": verdict_group,
            "execution_mode": execution_mode,
        },
        "metrics": {
            "total_responses": total,
            "correct_responses": correct,
            "accuracy_provisional": correct / total if total else None,
            "needs_review": needs_review,
            "human_reviewed": human_reviewed,
            "simulated_responses": simulated,
            "simulated_share": simulated / total if total else None,
            "retrieval_measured": retrieval_measured,
            "retrieval_hits": retrieval_hits,
            "retrieval_hit_rate": retrieval_hits / retrieval_measured if retrieval_measured else None,
            "average_retrieval_score": retrieval_score,
            "average_latency_ms": latency,
        },
        "by_strategy": [
            {
                "strategy": name,
                "label": label,
                "responses": count,
                "correct": correct_count,
                "accuracy": correct_count / count if count else None,
                "needs_review": pending,
                "human_reviewed": reviewed,
                "retrieval_measured": measured,
                "retrieval_hits": hits,
                "retrieval_hit_rate": hits / measured if measured else None,
            }
            for name, label, count, correct_count, pending, reviewed, measured, hits in strategy_rows
        ],
        "by_verdict": [{"verdict_group": group, "responses": count} for group, count in verdict_rows],
        "questions_to_review": [
            {
                "external_id": external_id,
                "question_text": question_text,
                "category": category,
                "responses": count,
                "incorrect_responses": incorrect,
                "needs_review": pending,
            }
            for external_id, question_text, category, count, incorrect, pending in question_rows
        ],
        "last_etl_run": (
            {"run_id": last_run.run_id, "status": last_run.status, "started_at": last_run.started_at.isoformat()}
            if last_run else None
        ),
        "limitations": [
            "Accuracy is provisional and may include automatic verdicts that have not been human-reviewed.",
            "Demo-mode responses are simulated fixtures, not real model outputs.",
            "Retrieval hit rate is calculated only where a relevance label exists.",
            "This dashboard summarizes the latest warehouse snapshot; refresh ETL to include recent evaluations.",
        ],
    }