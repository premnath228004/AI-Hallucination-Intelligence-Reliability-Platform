import json
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import PROJECT_ROOT
from app.models import Dataset, Question

BENCHMARK_DIR = PROJECT_ROOT / "data" / "benchmark"


def load_dataset_file(db: Session, file_path: Path) -> dict:
    """Load a benchmark JSON file. Safe to run repeatedly: no duplicates, no silent edits."""
    data = json.loads(file_path.read_text(encoding="utf-8"))
    stats = {
        "dataset": f'{data["name"]} {data["version"]}',
        "dataset_created": False,
        "inserted": 0,
        "skipped": 0,
        "rejected": 0,
        "messages": [],
    }

    dataset = db.scalar(
        select(Dataset).where(Dataset.name == data["name"], Dataset.version == data["version"])
    )
    if dataset is None:
        dataset = Dataset(
            name=data["name"],
            version=data["version"],
            description=data.get("description"),
            provenance=data.get("provenance"),
        )
        db.add(dataset)
        db.flush()  # gets dataset.id
        stats["dataset_created"] = True

    for item in data.get("questions", []):
        external_id = item.get("external_id")
        text = item.get("question_text")
        if not external_id or not text:
            stats["rejected"] += 1
            stats["messages"].append(f"Rejected item without external_id or question_text: {item}")
            continue

        fields = {
            "question_text": text,
            "reference_answer": item.get("reference_answer"),
            "category": item.get("category"),
            "answerable": item.get("answerable", True),
            "source_note": item.get("source_note"),
        }
        existing = db.scalar(
            select(Question).where(
                Question.dataset_id == dataset.id, Question.external_id == external_id
            )
        )
        if existing is None:
            db.add(Question(dataset_id=dataset.id, external_id=external_id, **fields))
            stats["inserted"] += 1
        elif all(getattr(existing, key) == value for key, value in fields.items()):
            stats["skipped"] += 1
        else:
            # A versioned dataset must not change silently.
            stats["rejected"] += 1
            stats["messages"].append(
                f"{external_id}: content differs from the stored version. Create a new dataset version instead of editing."
            )

    db.commit()
    return stats