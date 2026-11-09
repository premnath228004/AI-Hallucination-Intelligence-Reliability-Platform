from sqlalchemy import func, select

from app.database import SessionLocal
from app.dataset_loader import BENCHMARK_DIR, load_dataset_file
from app.document_loader import DOCUMENTS_DIR, load_corpus_file
from app.evaluation_routes import evaluate_experiment
from app.experiment_runner import run_experiment
from app.models import Dataset, Experiment
from app.warehouse_etl import run_etl


def seed_demo_data() -> str:
    """Fill an EMPTY database with the sample dataset, corpus and one evaluated demo experiment.
    Never touches a database that already has experiments."""
    db = SessionLocal()
    try:
        if db.scalar(select(func.count()).select_from(Experiment)) > 0:
            return "skipped: database already contains experiments"
        load_dataset_file(db, BENCHMARK_DIR / "sample_v1.json")
        load_corpus_file(db, DOCUMENTS_DIR / "pilot_corpus_v1.json")
        dataset = db.scalar(select(Dataset).order_by(Dataset.id))
        experiment = run_experiment(db, dataset.id, "demo", "demo run (auto-seeded)")
        evaluate_experiment(experiment.id, db)
        etl = run_etl(db)
        return f"seeded: experiment {experiment.id}, warehouse run {etl['run_id']} ({etl['status']})"
    finally:
        db.close()
