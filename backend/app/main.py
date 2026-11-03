from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect

from app.database import DB_PATH, engine, init_db
from app.dataset_routes import router as dataset_router
from app.experiment_routes import router as experiment_router
from app.evaluation_routes import router as evaluation_router
from app.document_routes import router as document_router
from app.retrieval_routes import router as retrieval_router
from app.rag_routes import router as rag_router
from app.warehouse_routes import router as warehouse_router
from app.export_routes import router as export_router
from app.check_routes import router as check_router

APP_NAME = "AI Hallucination Intelligence & Reliability Platform"
APP_VERSION = "0.2.0"


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()  # creates missing tables only; existing data is untouched
    yield


app = FastAPI(title=APP_NAME, version=APP_VERSION, lifespan=lifespan)

# Allow the React dev server (added later) to call this API from the browser.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(dataset_router)
app.include_router(experiment_router)
app.include_router(evaluation_router)
app.include_router(document_router)
app.include_router(retrieval_router)
app.include_router(rag_router)
app.include_router(warehouse_router)
app.include_router(export_router)
app.include_router(check_router)



@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "app": APP_NAME,
        "version": APP_VERSION,
        "default_execution_mode": "demo",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/api/db-info")
def db_info():
    inspector = inspect(engine)
    return {
        "database_file": str(DB_PATH),
        "database_file_exists": DB_PATH.exists(),
        "tables": sorted(inspector.get_table_names()),
    }