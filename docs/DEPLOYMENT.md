# Deployment

The Docker image builds the React app and runs it with FastAPI as a single web service. FastAPI serves the API under `/api` and the built React app at `/`.

The container sets `AUTO_SEED_DEMO=1` to seed an empty database with demo content at startup. Set `HALLUCINATION_DB_PATH` to choose a SQLite database path; otherwise the app uses `data/hallucination.db`. Seeding is skipped when the database already contains experiments.

To test the production-style app locally from PowerShell:

```powershell
cd C:\Hallucination_Project\frontend
npm run build
cd C:\Hallucination_Project\backend
$env:HALLUCINATION_DB_PATH = "C:\Hallucination_Project\data\seedtest.db"
$env:AUTO_SEED_DEMO = "1"
.\venv\Scripts\python.exe -m uvicorn app.main:app --port 8001
```

In a second terminal, check `/api/health`, `/api/experiments`, `/api/warehouse/summary`, `/`, `/experiments`, and `/api/does-not-exist`. Stop the server, remove the two environment variables, and delete only the temporary `data\seedtest.db` file after the test.

Limitations: free-tier storage is ephemeral, so data resets on restart; the service sleeps after about 15 minutes idle; and there is no authentication.
