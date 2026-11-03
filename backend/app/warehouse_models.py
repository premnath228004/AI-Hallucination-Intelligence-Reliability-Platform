from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class EtlRunLog(Base):
    """Grain: one row per ETL execution."""

    __tablename__ = "dw_etl_run_log"

    run_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    status: Mapped[str] = mapped_column(String(30), nullable=False)  # running, success, reconciliation_failed, failed
    counts_json: Mapped[Optional[str]] = mapped_column(Text)  # inserted/updated/skipped/rejected per table
    reconciliation_json: Mapped[Optional[str]] = mapped_column(Text)
    rejected_json: Mapped[Optional[str]] = mapped_column(Text)
    error_message: Mapped[Optional[str]] = mapped_column(Text)


class DimDataset(Base):
    """Grain: one row per dataset version."""

    __tablename__ = "dw_dim_dataset"

    dataset_key: Mapped[int] = mapped_column(Integer, primary_key=True)
    dataset_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)  # source datasets.id
    dataset_name: Mapped[str] = mapped_column(String(200), nullable=False)
    dataset_version: Mapped[str] = mapped_column(String(50), nullable=False)


class DimQuestion(Base):
    """Grain: one row per benchmark question."""

    __tablename__ = "dw_dim_question"

    question_key: Mapped[int] = mapped_column(Integer, primary_key=True)
    question_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)  # source questions.id
    dataset_key: Mapped[int] = mapped_column(ForeignKey("dw_dim_dataset.dataset_key"), nullable=False)
    external_id: Mapped[str] = mapped_column(String(100), nullable=False)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[Optional[str]] = mapped_column(String(100))
    is_answerable: Mapped[int] = mapped_column(Integer, nullable=False)  # 1 = answerable, 0 = should abstain


class DimStrategy(Base):
    """Grain: one row per answering strategy."""

    __tablename__ = "dw_dim_strategy"

    strategy_key: Mapped[int] = mapped_column(Integer, primary_key=True)
    strategy_name: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    strategy_label: Mapped[str] = mapped_column(String(50), nullable=False)


class DimExperiment(Base):
    """Grain: one row per experiment run."""

    __tablename__ = "dw_dim_experiment"

    experiment_key: Mapped[int] = mapped_column(Integer, primary_key=True)
    experiment_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)  # source experiments.id
    experiment_name: Mapped[str] = mapped_column(String(200), nullable=False)
    execution_mode: Mapped[str] = mapped_column(String(20), nullable=False)
    model_name: Mapped[str] = mapped_column(String(200), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(50), nullable=False)
    is_simulated: Mapped[int] = mapped_column(Integer, nullable=False)  # 1 = demo/simulated outputs
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class DimVerdict(Base):
    """Grain: one row per verdict type."""

    __tablename__ = "dw_dim_verdict"

    verdict_key: Mapped[int] = mapped_column(Integer, primary_key=True)
    verdict: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    is_correct: Mapped[int] = mapped_column(Integer, nullable=False)
    verdict_group: Mapped[str] = mapped_column(String(60), nullable=False)


class FactResponseEvaluation(Base):
    """Grain: one row per response (one strategy's answer to one question in one experiment),
    carrying its final verdict (human review overrides the automatic reference verdict)."""

    __tablename__ = "dw_fact_response_evaluation"

    response_id: Mapped[int] = mapped_column(Integer, primary_key=True)  # source responses.id
    experiment_key: Mapped[int] = mapped_column(ForeignKey("dw_dim_experiment.experiment_key"), nullable=False)
    question_key: Mapped[int] = mapped_column(ForeignKey("dw_dim_question.question_key"), nullable=False)
    strategy_key: Mapped[int] = mapped_column(ForeignKey("dw_dim_strategy.strategy_key"), nullable=False)
    verdict_key: Mapped[int] = mapped_column(ForeignKey("dw_dim_verdict.verdict_key"), nullable=False)
    is_correct: Mapped[int] = mapped_column(Integer, nullable=False)
    needs_review: Mapped[int] = mapped_column(Integer, nullable=False)
    human_reviewed: Mapped[int] = mapped_column(Integer, nullable=False)
    evaluator_type: Mapped[str] = mapped_column(String(20), nullable=False)  # which evaluator gave the final verdict
    evaluator_version: Mapped[str] = mapped_column(String(50), nullable=False)
    answer_length_chars: Mapped[int] = mapped_column(Integer, nullable=False)
    latency_ms: Mapped[Optional[int]] = mapped_column(Integer)
    retrieved_count: Mapped[int] = mapped_column(Integer, nullable=False)  # 0 for non-RAG strategies
    retrieval_top_score: Mapped[Optional[float]] = mapped_column(Float)
    retrieval_hit: Mapped[Optional[int]] = mapped_column(Integer)  # 1/0, empty when not measurable
    is_simulated: Mapped[int] = mapped_column(Integer, nullable=False)
    loaded_run_id: Mapped[int] = mapped_column(ForeignKey("dw_etl_run_log.run_id"), nullable=False)  # provenance