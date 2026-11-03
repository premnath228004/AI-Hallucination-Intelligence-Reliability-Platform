import json
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.evaluation_routes import CORRECT_VERDICTS, HUMAN_VERSION
from app.evaluator import EVALUATOR_VERSION
from app.models import Chunk, Dataset, Document, Evaluation, Experiment, Question, Response, Retrieval
from app.retriever import load_relevance_map
from app.warehouse_models import (
    DimDataset,
    DimExperiment,
    DimQuestion,
    DimStrategy,
    DimVerdict,
    EtlRunLog,
    FactResponseEvaluation,
)

STRATEGY_LABELS = {"basic": "Basic prompting", "improved": "Improved prompting", "rag": "RAG"}

VERDICT_GROUPS = {
    "correct": "Correct answer",
    "correct_abstention": "Correct abstention",
    "incorrect": "Incorrect answer",
    "reference_mismatch": "Incorrect answer (unreviewed mismatch)",
    "incorrect_abstention": "Incorrect abstention",
    "failure_to_abstain": "Failure to abstain",
}


def _new_stats() -> dict:
    return {"inserted": 0, "updated": 0, "skipped": 0, "rejected": 0}


def _upsert(db: Session, model, natural: dict, values: dict, stats: dict, stamp: dict | None = None):
    """Insert if missing, update if changed, otherwise skip. This is what makes repeat runs safe."""
    stamp = stamp or {}
    obj = db.scalar(select(model).filter_by(**natural))
    if obj is None:
        obj = model(**natural, **values, **stamp)
        db.add(obj)
        db.flush()
        stats["inserted"] += 1
    else:
        changed = {k: v for k, v in values.items() if getattr(obj, k) != v}
        if changed:
            for key, value in {**changed, **stamp}.items():
                setattr(obj, key, value)
            stats["updated"] += 1
        else:
            stats["skipped"] += 1
    return obj


def _count(db: Session, model) -> int:
    return db.scalar(select(func.count()).select_from(model))


def run_etl(db: Session) -> dict:
    run = EtlRunLog(status="running")
    db.add(run)
    db.flush()
    tables = {
        name: _new_stats()
        for name in ("dim_dataset", "dim_question", "dim_strategy", "dim_experiment", "dim_verdict", "fact_response_evaluation")
    }
    rejected: list[dict] = []
    expected_correct = {name: 0 for name in STRATEGY_LABELS}
    accepted_rows = 0
    total_responses = 0

    try:
        # ---- dimensions ----
        strategy_keys = {
            name: _upsert(db, DimStrategy, {"strategy_name": name}, {"strategy_label": label}, tables["dim_strategy"]).strategy_key
            for name, label in STRATEGY_LABELS.items()
        }
        verdict_keys = {
            verdict: _upsert(
                db, DimVerdict, {"verdict": verdict},
                {"is_correct": int(verdict in CORRECT_VERDICTS), "verdict_group": group},
                tables["dim_verdict"],
            ).verdict_key
            for verdict, group in VERDICT_GROUPS.items()
        }
        dataset_keys = {}
        for d in db.scalars(select(Dataset).order_by(Dataset.id)).all():
            obj = _upsert(db, DimDataset, {"dataset_id": d.id},
                          {"dataset_name": d.name, "dataset_version": d.version}, tables["dim_dataset"])
            dataset_keys[d.id] = obj.dataset_key

        questions = db.scalars(select(Question).order_by(Question.id)).all()
        question_keys = {}
        for q in questions:
            obj = _upsert(
                db, DimQuestion, {"question_id": q.id},
                {"dataset_key": dataset_keys[q.dataset_id], "external_id": q.external_id,
                 "question_text": q.question_text, "category": q.category, "is_answerable": int(q.answerable)},
                tables["dim_question"],
            )
            question_keys[q.id] = obj.question_key
        question_by_id = {q.id: q for q in questions}

        experiment_keys = {}
        for e in db.scalars(select(Experiment).order_by(Experiment.id)).all():
            obj = _upsert(
                db, DimExperiment, {"experiment_id": e.id},
                {"experiment_name": e.name, "execution_mode": e.execution_mode, "model_name": e.model_name,
                 "prompt_version": e.prompt_version, "is_simulated": int(e.execution_mode == "demo"),
                 "created_at": e.created_at},
                tables["dim_experiment"],
            )
            experiment_keys[e.id] = obj.experiment_key

        # ---- lookups for the fact table ----
        reference, human = {}, {}
        for ev in db.scalars(select(Evaluation).where(Evaluation.evaluator_type.in_(["reference", "human"]))).all():
            if ev.evaluator_type == "reference" and ev.evaluator_version == EVALUATOR_VERSION:
                reference[ev.response_id] = ev
            elif ev.evaluator_type == "human" and ev.evaluator_version == HUMAN_VERSION:
                human[ev.response_id] = ev

        relevance = load_relevance_map(db)
        retrieval_info: dict[int, dict] = {}
        for retrieval, doc_key in db.execute(
            select(Retrieval, Document.doc_key)
            .join(Chunk, Chunk.id == Retrieval.chunk_id)
            .join(Document, Document.id == Chunk.document_id)
        ).all():
            info = retrieval_info.setdefault(retrieval.response_id, {"count": 0, "top": None, "docs": set()})
            info["count"] += 1
            info["top"] = retrieval.score if info["top"] is None else max(info["top"], retrieval.score)
            info["docs"].add(doc_key)

        # ---- fact ----
        fact_stats = tables["fact_response_evaluation"]
        for resp in db.scalars(select(Response).order_by(Response.id)).all():
            total_responses += 1
            question = question_by_id.get(resp.question_id)
            effective = human.get(resp.id) or reference.get(resp.id)
            reason = None
            if question is None:
                reason = "question not found"
            elif resp.error_message or resp.answer_text is None:
                reason = "response has no answer (provider error)"
            elif effective is None:
                reason = "response not evaluated yet"
            elif effective.verdict not in VERDICT_GROUPS:
                reason = f"unknown verdict: {effective.verdict}"
            if reason:
                fact_stats["rejected"] += 1
                rejected.append({"response_id": resp.id, "experiment_id": resp.experiment_id, "reason": reason})
                continue

            info = retrieval_info.get(resp.id)
            keys = relevance.get(question.external_id, set())
            hit = None
            if resp.strategy == "rag" and info is not None and keys:
                hit = int(bool(keys & info["docs"]))
            is_correct = int(effective.verdict in CORRECT_VERDICTS)
            _upsert(
                db, FactResponseEvaluation, {"response_id": resp.id},
                {
                    "experiment_key": experiment_keys[resp.experiment_id],
                    "question_key": question_keys[resp.question_id],
                    "strategy_key": strategy_keys[resp.strategy],
                    "verdict_key": verdict_keys[effective.verdict],
                    "is_correct": is_correct,
                    "needs_review": int(effective.needs_review and effective.evaluator_type != "human"),
                    "human_reviewed": int(effective.evaluator_type == "human"),
                    "evaluator_type": effective.evaluator_type,
                    "evaluator_version": effective.evaluator_version,
                    "answer_length_chars": len(resp.answer_text),
                    "latency_ms": resp.latency_ms,
                    "retrieved_count": info["count"] if info else 0,
                    "retrieval_top_score": info["top"] if info else None,
                    "retrieval_hit": hit,
                    "is_simulated": int(resp.is_simulated),
                },
                fact_stats,
                stamp={"loaded_run_id": run.run_id},
            )
            accepted_rows += 1
            expected_correct[resp.strategy] += is_correct

        # ---- reconciliation: does the warehouse agree with the source? ----
        checks = []

        def add(name, source, warehouse):
            checks.append({"check": name, "source": source, "warehouse": warehouse, "passed": source == warehouse})

        fact_count = _count(db, FactResponseEvaluation)
        add("datasets", _count(db, Dataset), _count(db, DimDataset))
        add("questions", _count(db, Question), _count(db, DimQuestion))
        add("experiments", _count(db, Experiment), _count(db, DimExperiment))
        add("fact rows = responses accepted by validation", accepted_rows, fact_count)
        add("responses = fact rows + rejected", total_responses, fact_count + fact_stats["rejected"])
        warehouse_correct = dict(
            db.execute(
                select(DimStrategy.strategy_name, func.coalesce(func.sum(FactResponseEvaluation.is_correct), 0))
                .select_from(FactResponseEvaluation)
                .join(DimStrategy, DimStrategy.strategy_key == FactResponseEvaluation.strategy_key)
                .group_by(DimStrategy.strategy_name)
            ).all()
        )
        for name in STRATEGY_LABELS:
            add(f"correct answers [{name}]", expected_correct[name], int(warehouse_correct.get(name, 0)))

        run.status = "success" if all(c["passed"] for c in checks) else "reconciliation_failed"
        run.finished_at = datetime.now(timezone.utc)
        run.counts_json = json.dumps(tables)
        run.reconciliation_json = json.dumps(checks)
        run.rejected_json = json.dumps(rejected)
        db.commit()
        return {
            "run_id": run.run_id,
            "status": run.status,
            "tables": tables,
            "rejected_count": len(rejected),
            "rejected_sample": rejected[:10],
            "reconciliation": checks,
        }
    except Exception as exc:
        db.rollback()
        failed = EtlRunLog(status="failed", finished_at=datetime.now(timezone.utc), error_message=str(exc))
        db.add(failed)
        db.commit()
        raise