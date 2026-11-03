from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Dataset(Base):
    """A versioned benchmark dataset. Same name + new version = a new dataset."""

    __tablename__ = "datasets"
    __table_args__ = (UniqueConstraint("name", "version", name="uq_dataset_name_version"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    version: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    provenance: Mapped[Optional[str]] = mapped_column(Text)  # where the data came from
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)

    questions: Mapped[list["Question"]] = relationship(back_populates="dataset")


class Question(Base):
    """One benchmark question with its reference answer."""

    __tablename__ = "questions"
    __table_args__ = (UniqueConstraint("dataset_id", "external_id", name="uq_question_dataset_external"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    dataset_id: Mapped[int] = mapped_column(ForeignKey("datasets.id"), nullable=False)
    external_id: Mapped[str] = mapped_column(String(100), nullable=False)  # id used in the source file
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    reference_answer: Mapped[Optional[str]] = mapped_column(Text)
    category: Mapped[Optional[str]] = mapped_column(String(100))
    # False means the question cannot be answered from the evidence: the correct behaviour is to abstain.
    answerable: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    source_note: Mapped[Optional[str]] = mapped_column(Text)

    dataset: Mapped["Dataset"] = relationship(back_populates="questions")
    responses: Mapped[list["Response"]] = relationship(back_populates="question")


class Experiment(Base):
    """One experiment run. Stores everything needed to reproduce it."""

    __tablename__ = "experiments"
    __table_args__ = (
        CheckConstraint(
            "execution_mode IN ('demo', 'local_llm', 'external_api')",
            name="ck_experiment_execution_mode",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    dataset_id: Mapped[int] = mapped_column(ForeignKey("datasets.id"), nullable=False)
    execution_mode: Mapped[str] = mapped_column(String(20), nullable=False)
    model_name: Mapped[str] = mapped_column(String(200), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(50), nullable=False)
    config_json: Mapped[Optional[str]] = mapped_column(Text)  # settings used, stored as JSON text
    status: Mapped[str] = mapped_column(String(20), default="created", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    responses: Mapped[list["Response"]] = relationship(back_populates="experiment")


class Response(Base):
    """The answer one strategy gave to one question in one experiment."""

    __tablename__ = "responses"
    __table_args__ = (
        UniqueConstraint("experiment_id", "question_id", "strategy", name="uq_response_exp_question_strategy"),
        CheckConstraint("strategy IN ('basic', 'improved', 'rag')", name="ck_response_strategy"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    experiment_id: Mapped[int] = mapped_column(ForeignKey("experiments.id"), nullable=False)
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id"), nullable=False)
    strategy: Mapped[str] = mapped_column(String(20), nullable=False)
    answer_text: Mapped[Optional[str]] = mapped_column(Text)
    is_simulated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)  # True = demo output, not a real LLM
    latency_ms: Mapped[Optional[int]] = mapped_column(Integer)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)

    experiment: Mapped["Experiment"] = relationship(back_populates="responses")
    question: Mapped["Question"] = relationship(back_populates="responses")
class Evaluation(Base):
    """One evaluation of one response by one evaluator (reference rules, LLM judge, or human).

    Grain: one row per (response, evaluator_type, evaluator_version).
    """

    __tablename__ = "evaluations"
    __table_args__ = (
        UniqueConstraint("response_id", "evaluator_type", "evaluator_version", name="uq_eval_response_type_version"),
        CheckConstraint("evaluator_type IN ('reference', 'llm_judge', 'human')", name="ck_eval_type"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    response_id: Mapped[int] = mapped_column(ForeignKey("responses.id"), nullable=False)
    evaluator_type: Mapped[str] = mapped_column(String(20), nullable=False)
    evaluator_version: Mapped[str] = mapped_column(String(50), nullable=False)
    verdict: Mapped[str] = mapped_column(String(40), nullable=False)
    correctness_score: Mapped[Optional[float]] = mapped_column(Float)
    abstained: Mapped[Optional[bool]] = mapped_column(Boolean)
    failure_category: Mapped[Optional[str]] = mapped_column(String(60))
    needs_review: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    explanation: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)
class Document(Base):
    """A source document in the RAG corpus. Immutable once loaded: changed content needs a new corpus version."""

    __tablename__ = "documents"
    __table_args__ = (UniqueConstraint("corpus", "doc_key", name="uq_document_corpus_key"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    corpus: Mapped[str] = mapped_column(String(100), nullable=False)
    doc_key: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[Optional[str]] = mapped_column(String(300))
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)  # SHA-256, detects silent edits
    provenance: Mapped[Optional[str]] = mapped_column(Text)
    relevant_question_ids: Mapped[Optional[str]] = mapped_column(Text)  # JSON list of question external_ids
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)


class Chunk(Base):
    """A piece of a document. Grain: one row per (document, chunk_config, chunk_index)."""

    __tablename__ = "chunks"
    __table_args__ = (
        UniqueConstraint("document_id", "chunk_config", "chunk_index", name="uq_chunk_doc_config_index"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"), nullable=False)
    chunk_config: Mapped[str] = mapped_column(String(50), nullable=False)  # records how it was chunked
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    char_start: Mapped[int] = mapped_column(Integer, nullable=False)
    char_end: Mapped[int] = mapped_column(Integer, nullable=False)


class Retrieval(Base):
    """Chunks retrieved for one RAG response. Grain: one row per (response, rank)."""

    __tablename__ = "retrievals"
    __table_args__ = (UniqueConstraint("response_id", "rank", name="uq_retrieval_response_rank"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    response_id: Mapped[int] = mapped_column(ForeignKey("responses.id"), nullable=False)
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    chunk_id: Mapped[int] = mapped_column(ForeignKey("chunks.id"), nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    retriever_name: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)