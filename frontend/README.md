# AI Reliability Platform

The frontend is a React application built with Vite. Its pages use the FastAPI
service in `../backend` through the `/api` development proxy.

## Run locally

Open two terminals from the project root.

### Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### Frontend

```powershell
cd frontend
npm ci
npm run dev
```

Open the Vite URL printed in the frontend terminal (normally
`http://localhost:5173`). Keep both processes running. The backend creates any
missing database tables on startup and uses the existing SQLite database
without deleting its data.

## First use

1. Confirm the header reports **Backend Online**.
2. In **Experiment Studio**, load the sample benchmark and pilot evidence corpus
   if they are not already present.
3. Run an experiment in **Demo fixtures** mode to try the workflow without
   configuring a model provider.
4. Evaluate the experiment, review flagged responses, and inspect stored RAG
   retrievals in **Evaluation Center** and **RAG Inspector**.
5. Refresh the **Data Warehouse** before generating Power BI CSV exports in
   **Export Center**.
6. Use **Analytics & Reports** to slice the current warehouse snapshot by
   dataset, experiment, strategy, verdict, or execution mode. The URL preserves
   those filters; share the filtered link or copy/download the generated
   insight review. Use Print / Save PDF for a static copy.

Demo answers are simulated fixtures, not real model output. The Answer Checker
and evaluation pages describe their heuristic limitations in the UI.

## Verify the frontend

```powershell
npm run lint
npm run build
```
