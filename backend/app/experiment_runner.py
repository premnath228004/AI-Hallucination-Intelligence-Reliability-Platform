import json
import time
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.document_loader import CHUNK_CONFIG
from app.models import Dataset, Experiment, Question, Response, Retrieval
from app.prompts import PROMPT_VERSION, STRATEGIES, build_prompt
from app.providers import get_provider
from app.retriever import DEFAULT_CORPUS, RETRIEVER_NAME, build_retriever

RETRIEVAL_K = 3


def run_experiment(db: Session, dataset_id: int, execution_mode: str, name: str | None = None) -> Experiment:
    dataset = db.get(Dataset, dataset_id)
    if dataset is None:
        raise LookupError("Dataset not found")

    # Both may raise (ProviderUnavailable / ValueError). Nothing is stored in that case.
    provider = get_provider(execution_mode, dataset.name, dataset.version)
    retriever = build_retriever(db)

    questions = db.scalars(
        select(Question).where(Question.dataset_id == dataset.id).order_by(Question.id)
    ).all()

    config = {
        "strategies": list(STRATEGIES),
        "dataset": f"{dataset.name} {dataset.version}",
        "provider_is_simulated": provider.is_simulated,
        "fixture_file": getattr(provider, "fixture_file", None),
        "retriever": RETRIEVER_NAME,
        "retrieval_k": RETRIEVAL_K,
        "retrieval_corpus": DEFAULT_CORPUS,
        "chunk_config": CHUNK_CONFIG,
    }
    if provider.is_simulated:
        config["rag_note"] = (
            "Retrieval is real and stored per response, but the RAG answer text is a simulated fixture "
            "and was NOT generated from the retrieved chunks."
        )
    experiment = Experiment(
        name=name or f"{execution_mode} run on {dataset.name} {dataset.version}",
        dataset_id=dataset.id,
        execution_mode=execution_mode,
        model_name=provider.model_name,
        prompt_version=PROMPT_VERSION,
        config_json=json.dumps(config),
        status="running",
    )
    db.add(experiment)
    db.flush()  # gets experiment.id

    error_count = 0
    for question in questions:
        for strategy in STRATEGIES:
            hits, context = [], None
            answer, error = None, None
            start = time.perf_counter()
            try:
                if strategy == "rag":
                    hits = retriever.search(question.question_text, RETRIEVAL_K)
                    context = "\n\n".join(f"[{h['doc_key']}] {h['text']}" for h in hits) or None
                prompt = build_prompt(strategy, question.question_text, context)
                answer = provider.generate(strategy, question.external_id, prompt)
            except Exception as exc:  # one failed answer must not stop the whole experiment
                error = str(exc)
                error_count += 1
            latency_ms = int((time.perf_counter() - start) * 1000)

            response = Response(
                experiment_id=experiment.id,
                question_id=question.id,
                strategy=strategy,
                answer_text=answer,
                is_simulated=provider.is_simulated,
                latency_ms=latency_ms,
                error_message=error,
            )
            db.add(response)
            db.flush()  # gets response.id
            for h in hits:
                db.add(
                    Retrieval(
                        response_id=response.id,
                        rank=h["rank"],
                        chunk_id=h["chunk_id"],
                        score=h["score"],
                        retriever_name=RETRIEVER_NAME,
                    )
                )

    experiment.status = "completed" if error_count == 0 else "completed_with_errors"
    experiment.finished_at = datetime.now(timezone.utc)
    db.commit()
    return experiment