# AI Hallucination Intelligence & Reliability Platform

A platform that compares basic prompting, improved prompting and retrieval-augmented generation (RAG) on factual questions, including questions that should not be answered. It stores every answer with its provenance, evaluates answers with rules and human review, loads a star-schema data warehouse through an idempotent ETL, exports CSV files for Power BI, and presents everything in a React web application.

**Live demo:** https://hallucination-intelligence-platform.onrender.com

> **Demo mode.** All answers are simulated fixtures, not outputs of a language model, so the accuracy values demonstrate the pipeline and are not findings about real models.
> The free hosting sleeps after about 15 minutes of inactivity (the first load can take about a minute), its storage is ephemeral so data is re-seeded on restart, and there is no authentication. It is a demonstration deployment, not a production system.

## Stack
FastAPI, SQLAlchemy, SQLite, scikit-learn (TF-IDF), React, Vite, Tailwind CSS, Recharts, Power BI Desktop.

## Run locally (Windows, PowerShell)

Backend:
    cd backend
    .\venv\Scripts\Activate.ps1
    python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

Frontend (second terminal):
    cd frontend
    npm install
    npm run dev

Open http://localhost:5173. API documentation: http://127.0.0.1:8000/docs

## Documentation
See the docs folder: DEPLOYMENT.md, FRONTEND_CHANGELOG.md and powerbi_guide.md.