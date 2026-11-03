import csv
import hashlib
import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import PROJECT_ROOT, get_db
from app.warehouse_models import (
    DimDataset,
    DimExperiment,
    DimQuestion,
    DimStrategy,
    DimVerdict,
    EtlRunLog,
    FactResponseEvaluation,
)

EXPORT_DIR = PROJECT_ROOT / "exports"

TABLES = [
    ("dim_dataset.csv", DimDataset),
    ("dim_question.csv", DimQuestion),
    ("dim_strategy.csv", DimStrategy),
    ("dim_experiment.csv", DimExperiment),
    ("dim_verdict.csv", DimVerdict),
    ("fact_response_evaluation.csv", FactResponseEvaluation),
    ("etl_run_log.csv", EtlRunLog),
]
# Long JSON/text columns are left out of the CSV to keep it clean for Power BI.
EXCLUDED_COLUMNS = {"dw_etl_run_log": {"counts_json", "reconciliation_json", "rejected_json", "error_message"}}

router = APIRouter(prefix="/api/export", tags=["export"])


def _format(value):
    if value is None:
        return ""  # NULL becomes an empty cell (Power BI reads it as blank)
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")  # one timestamp format everywhere (UTC)
    return value


def _export_table(db: Session, filename: str, model) -> dict:
    skip = EXCLUDED_COLUMNS.get(model.__tablename__, set())
    columns = [c.name for c in model.__table__.columns if c.name not in skip]
    primary_key = list(model.__table__.primary_key.columns)[0]
    rows = db.execute(select(model).order_by(primary_key)).scalars().all()

    path = EXPORT_DIR / filename
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(columns)
        for row in rows:
            writer.writerow([_format(getattr(row, name)) for name in columns])

    # Integrity check: read the file back and compare with the database.
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        rows_in_csv = sum(1 for _ in csv.reader(f)) - 1  # minus header
    rows_in_db = db.scalar(select(func.count()).select_from(model))
    return {
        "file": filename,
        "table": model.__tablename__,
        "primary_key": primary_key.name,
        "rows_in_database": rows_in_db,
        "rows_in_csv": rows_in_csv,
        "integrity_ok": rows_in_db == rows_in_csv,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "columns": columns,
    }


@router.post("/run")
def run_export(db: Session = Depends(get_db)):
    last = db.scalar(select(EtlRunLog).order_by(EtlRunLog.run_id.desc()))
    if last is None or last.status != "success":
        raise HTTPException(
            status_code=409,
            detail="The latest ETL run is missing or not successful. Run POST /api/warehouse/refresh first.",
        )
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    files = [_export_table(db, filename, model) for filename, model in TABLES]
    manifest = {
        "exported_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
        "warehouse_run_id": last.run_id,
        "all_integrity_ok": all(f["integrity_ok"] for f in files),
        "note": "Snapshot of the warehouse at export time. Power BI shows this data only after a manual refresh; it is not live.",
        "files": files,
    }
    (EXPORT_DIR / "export_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


@router.get("/manifest")
def get_manifest():
    path = EXPORT_DIR / "export_manifest.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="No export yet. Run POST /api/export/run first.")
    return json.loads(path.read_text(encoding="utf-8"))