# AI Hallucination Intelligence Reliability Platform

A web application for exploring and evaluating the reliability of AI-generated
responses. It brings experiment runs, reference-based evaluation, retrieval
inspection, warehouse analytics, and CSV export into one interface.

> **Interpret results carefully:** Demo mode uses simulated fixture responses.
> The Answer Checker uses a lexical-overlap heuristic, not a guarantee of
> factual correctness. Accuracy is provisional, and the project makes no
> statistical significance claim.

## What the project does

- **Overview** — view backend health and database information.
- **Experiment Studio** — load the sample benchmark and evidence corpus, then
  run experiments using an available execution mode.
- **Evaluation Center** — compare strategies against reference answers, inspect
  Wilson 95% accuracy intervals, and record human reviews.
- **RAG Inspector** — search retrieved evidence, run retrieval benchmarks, and
  inspect experiment retrieval traces.
- **Answer Checker** — check an answer against supplied evidence using the
  backend's lexical-overlap heuristic.
- **Data Warehouse** — refresh and inspect analytical warehouse data.
- **Analytics & Reports** — filter warehouse results by dataset, experiment,
  strategy, verdict, and execution mode; share a filtered report view.
- **Export Center** — generate warehouse CSV snapshots for external analysis.

The frontend is a React application served by Vite. Its API requests are handled
by a FastAPI backend. The in-app analytics report is separate from the Power BI
Desktop report: CSV exports are snapshots and do not automatically refresh or
publish a Power BI report. See the [Power BI guide](docs/powerbi_guide.md).

## Technology

- **Frontend:** React, Vite, Tailwind CSS
- **Backend:** Python, FastAPI, SQLAlchemy
- **Analytics:** SQLite-backed warehouse and CSV exports; Power BI can consume
  the exported CSV files

## Requirements

- Python 3.10 or later
- Node.js and npm
- Windows PowerShell commands below; adapt activation commands for other shells

## Run locally

Open two terminals in the repository root.

### 1. Start the backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

The API is available at `http://127.0.0.1:8000`; interactive API documentation
is at `http://127.0.0.1:8000/docs`.

### 2. Start the frontend

In the second terminal:

```powershell
cd frontend
npm ci
npm run dev
```

Open the local URL printed by Vite (normally `http://localhost:5173`). Keep both
the frontend and backend terminals running. During development, Vite proxies
the frontend's `/api` requests to the local backend.

## First-use workflow

1. Check that the application reports the backend as online.
2. In **Experiment Studio**, load the sample benchmark and pilot corpus if they
   are not already available.
3. Run an experiment in **Demo fixtures** mode to try the workflow without
   configuring a model provider. These responses are simulated.
4. Open **Evaluation Center** to evaluate responses and, where appropriate,
   record human verdicts.
5. Use **RAG Inspector** to explore retrieval results and experiment traces.
6. Refresh the **Data Warehouse**, then generate exports in **Export Center**.
7. Use **Analytics & Reports** to filter results and share the selected view.
   For Power BI, import the exported CSV snapshots and refresh them separately.

## Validate the frontend

From `frontend`:

```powershell
npm run lint
npm run build
```

## Repository layout

```text
backend/   FastAPI application and Python dependencies
data/      Sample benchmark, corpus, and demo fixtures
docs/      Project guides and frontend/API data map
exports/   Generated warehouse CSV snapshots and manifest
frontend/  React/Vite web application
powerbi/   Power BI report file
```

For detailed frontend routes, API endpoints, displayed metric sources, and
known limitations, see [docs/FRONTEND_CHANGELOG.md](docs/FRONTEND_CHANGELOG.md).
