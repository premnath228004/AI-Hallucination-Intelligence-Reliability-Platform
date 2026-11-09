import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import inspect

from app.check_routes import router as check_router
from app.database import DB_PATH, PROJECT_ROOT, engine, init_db
from app.dataset_routes import router as dataset_router
from app.document_routes import router as document_router
from app.evaluation_routes import router as evaluation_router
from app.experiment_routes import router as experiment_router
from app.export_routes import router as export_router
from app.rag_routes import router as rag_router
from app.retrieval_routes import router as retrieval_router
from app.warehouse_routes import router as warehouse_router

APP_NAME = "AI Hallucination Intelligence & Reliability Platform"
APP_VERSION = "0.3.0"
FRONTEND_DIST = PROJECT_ROOT / "frontend" / "dist"
logger = logging.getLogger("uvicorn.error")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()  # creates missing tables only; existing data is untouched
    if os.getenv("AUTO_SEED_DEMO") == "1":
        from app.bootstrap import seed_demo_data

        try:
            logger.info("Demo seed: %s", seed_demo_data())
        except Exception:
            logger.exception("Demo seed failed; the app still starts.")
    yield


app = FastAPI(title=APP_NAME, version=APP_VERSION, lifespan=lifespan)

# Only needed when the React dev server (port 5173) calls the API directly.
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


# Serve the built React app (only if frontend/dist exists). Must stay LAST so it never hides an API route.
if FRONTEND_DIST.is_dir():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    def serve_frontend(full_path: str):
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not Found")
        candidate = (FRONTEND_DIST / full_path).resolve()
        if full_path and candidate.is_file() and FRONTEND_DIST.resolve() in candidate.parents:
            return FileResponse(candidate)
        return FileResponse(FRONTEND_DIST / "index.html")  # React Router handles the page
