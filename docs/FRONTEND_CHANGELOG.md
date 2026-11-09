# Frontend Changelog and Data Map

**Scope:** frontend work from the backend baseline commit `d15a889` through the current local `HEAD`, plus the workspace Python interpreter setting. Paths and API details below were checked against the current source. This document does not describe the internal implementation of the binary Power BI report.

## 1. Files created and modified

### Created

| Path | Summary |
|---|---|
| `.vscode/settings.json` | Selects `backend/venv/Scripts/python.exe` as the workspace Python interpreter. |
| `README.md` | Describes the project, features, stack, local setup, first-use workflow, limitations, and documentation links. |
| `frontend/src/components/ErrorBoundary.jsx` | Displays a fallback if a React render throws an error. |
| `frontend/src/pages/AnalyticsReport.jsx` | Adds the filtered warehouse analytics report, charts, deterministic insight briefing, and browser-based sharing/printing actions. |
| `frontend/src/pages/Workspace.jsx` | Adds the experiment, evaluation, RAG, answer-checker, warehouse, and export pages. |

### Modified

| Path | Summary |
|---|---|
| `docs/FRONTEND_CHANGELOG.md` | This changelog and API/data mapping. |
| `docs/powerbi_guide.md` | Adds guidance for the in-app analytics report and distinguishes it from Power BI sharing. |
| `exports/export_manifest.json` | Updated generated export manifest; it is an export artifact, not frontend source. |
| `frontend/README.md` | Replaces template text with project setup, first-use workflow, and analytics-report guidance. |
| `frontend/index.html` | Sets the application title, theme color, and description. |
| `frontend/src/App.jsx` | Connects the app routes to their page components and fallback page. |
| `frontend/src/components/Layout.jsx` | Provides shared responsive navigation and health indicator; closes the mobile menu on navigation and removes an unused health-derived variable. |
| `frontend/src/index.css` | Sets global typography, page background, base controls, and scrollbar styling. |
| `frontend/src/main.jsx` | Mounts the router inside the React error boundary. |
| `frontend/src/nav.js` | Defines the sidebar pages, labels, icons, and descriptions. |
| `frontend/src/pages/NotBuilt.jsx` | Shows a not-found or planned-page fallback for routes without a page component. |
| `frontend/src/pages/Overview.jsx` | Displays backend/database health and database table information; hero status uses `/api/health`. |
| `frontend/src/pages/AnalyticsReport.jsx` | Displays frontend-computed Wilson 95% accuracy intervals, labels its deterministic summary, and states the sample-size caveat. |
| `frontend/vite.config.js` | Enables the Tailwind Vite plugin and proxies `/api` requests to the local backend. |
| `powerbi/hallucination_dashboard.pbix` | Binary PBIX changed in a later commit; its internal report edits were not inspected here. |

### Backend files changed

| Path | Summary |
|---|---|
| `backend/app/warehouse_routes.py` | Adds `GET /api/warehouse/report`, returning warehouse slicer options, filtered aggregates, strategy/verdict groupings, review questions, ETL metadata, and limitations. |

## 2. Pages, routes, and backend endpoints

All page routes are nested under the shared layout. The frontend Axios client uses relative `/api` URLs; Vite proxies them to `http://127.0.0.1:8000`.

| Page / route | Backend endpoints called |
|---|---|
| Overview — `/` | `GET /api/health`; `GET /api/db-info`. |
| Experiment Studio — `/experiments` | On load/refresh: `GET /api/datasets`, `GET /api/experiments`, `GET /api/documents`. Load sample actions: `POST /api/datasets/load-sample`, `POST /api/documents/load-sample`. Run action: `POST /api/experiments` with `dataset_id`, optional `name`, and `execution_mode`. |
| Evaluation Center — `/evaluation` | `GET /api/experiments`; for a selected experiment: `GET /api/experiments/{experiment_id}/summary`, `GET /api/experiments/{experiment_id}/evaluations?needs_review_only={boolean}`, and `POST /api/experiments/{experiment_id}/evaluate`. Saving a human verdict: `POST /api/evaluations/review`. |
| RAG Inspector — `/rag` | On load: `GET /api/experiments`, `GET /api/datasets`, `GET /api/documents`. Load corpus action: `POST /api/documents/load-sample`. Search: `GET /api/retrieval/search?q={query}&k=5`. Benchmark: `GET /api/retrieval/evaluate?dataset_id={id}&k=5`. Selected experiment trace: `GET /api/experiments/{experiment_id}/rag-inspection`. |
| Answer Checker — `/checker` | Submit action: `POST /api/check` with `question`, `answer`, and optional `evidence`. |
| Data Warehouse — `/warehouse` | On load/refresh: `GET /api/warehouse/summary`, `GET /api/warehouse/runs`. Refresh action: `POST /api/warehouse/refresh`. |
| Analytics & Reports — `/analytics` | `GET /api/warehouse/report`; optional query parameters: `dataset_id`, `experiment_id`, `strategy`, `verdict_group`, and `execution_mode`. The same endpoint is called when a slicer changes. |
| Export Center — `/export` | On load: `GET /api/export/manifest`; generate action: `POST /api/export/run`. A `404` for a missing manifest is rendered as the empty “no export yet” state. |
| Not-found/fallback — any unmatched URL | No API calls. |

The shared layout independently calls `GET /api/health` at startup and every 30 seconds for the header status. It is not limited to the Overview page.

## 3. Displayed numbers and charts: source fields

### Overview

| Display | Data source |
|---|---|
| Backend status, version, execution mode | `GET /api/health`: `status`, `version`, `default_execution_mode`. |
| Database table count | `GET /api/db-info`: length of `tables`. |
| Warehouse/application table counts | Derived from `tables`: names starting with `dw_` count as warehouse tables; all other returned names count as application tables. |
| Database path and file status | `GET /api/db-info`: `database_file`, `database_file_exists`. |
| Infrastructure status indicators | Derived from `health.status`, `db.database_file_exists`, and whether `health.default_execution_mode` is present. |
| Database explorer names | `GET /api/db-info`: `tables`, divided using the `dw_` prefix rule. |

### Experiment Studio

| Display | Data source |
|---|---|
| Dataset question count | `GET /api/datasets[]`: `question_count`; dataset name/version/id: `name`, `version`, `id`. |
| “Ready” dataset/document counts | Lengths of `GET /api/datasets` and `GET /api/documents` results. |
| Recent run id, name, mode, model, response count, status | `GET /api/experiments[]`: `id`, `name`, `execution_mode`, `model_name`, `response_count`, `status`. |
| Completed-run confirmation | `POST /api/experiments` response: `id`, `status`, `response_count`. |
| Execution-mode choices and strategy descriptions | Static UI choices/copy. Mode options are `demo`, `local_llm`, and `external_api`; the backend may reject a mode if its provider is unavailable. |

### Evaluation Center

| Display | Data source |
|---|---|
| Strategy accuracy cards and interval | `GET /api/experiments/{id}/summary`: `strategies[<strategy>].accuracy_provisional` and `accuracy_95ci_wilson`, plus `evaluated`, `responses`, `pending_manual_review`, and `human_reviewed`. |
| Accuracy bar width | `accuracy_provisional`. |
| Strategy sample-size caveat | Static note: “14 questions per strategy, no significance claimed.” |
| Review response/question/answer/reference/verdict/note | `GET /api/experiments/{id}/evaluations`: `items[]` fields including `response_id`, `question_external_id`, `question_text`, `reference_answer`, `strategy`, `answer_text`, `reference_verdict`, `needs_review`, `reference_explanation`, `human_verdict`, and `human_note`. |
| Evaluation completion message | `POST /api/experiments/{id}/evaluate`: `inserted` and `skipped_existing`. |
| Verdict selector | Static options matching the backend review schema: `correct`, `correct_abstention`, `incorrect`, `incorrect_abstention`, `failure_to_abstain`. |

### RAG Inspector

| Display | Data source |
|---|---|
| Search result rank, source key, chunk, score, text | `GET /api/retrieval/search`: `results[]` fields `rank`, `doc_key`, `chunk_index`, `score`, `text`. Search `k=5` is set by the frontend. |
| Retrieval hit-rate and MRR cards | `GET /api/retrieval/evaluate`: `k`, `hit_rate_at_k`, `mrr_at_k`, `questions_with_relevant_docs`, `retriever`. `k=5` is set by the frontend. |
| RAG answer, relevance hit, diagnostic hint, retrieved passages | `GET /api/experiments/{id}/rag-inspection`: `items[]` fields `response_id`, `question_external_id`, `question_text`, `answer_text`, `retrieval_hit`, `diagnostic_hint`, and `retrieved[]` (`rank`, `doc_key`, `chunk_index`, `score`, `text`). |
| Demo-mode caution and limitations | `answer_note` and `limitations[]` from the RAG-inspection response. |

### Answer Checker

| Display | Data source |
|---|---|
| Overall evidence signal and claim count | `POST /api/check` response: `evidence_check.signal` and length of `evidence_check.claims`. |
| Claim label, support score, claim sentence, explanation, best passage | `evidence_check.claims[]`: `label`, `support_score`, `sentence`, `explanation`, `best_passage.source`, and `best_passage.text`. |
| Benchmark reference explanation/verdict | `reference_check.note`, `reference_check.explanation`, `reference_check.verdict`, and `reference_check.needs_review`. |
| Evidence source/mode and retriever | Response fields `mode` and `retriever`. |
| Limitations | `limitations[]` from the backend response. The warning that this is a lexical heuristic is static UI copy consistent with those backend limitations. |

### Data Warehouse

| Display | Data source |
|---|---|
| Per-table row counts | `GET /api/warehouse/summary`: entries in `table_row_counts`. |
| Experiment/strategy fact table | `correct_by_experiment_and_strategy[]`: `experiment_id`, `execution_mode`, `strategy`, `responses`, `correct`. |
| Recent ETL run id, timestamp, status, rejected count, reconciliation | `GET /api/warehouse/runs[]`: `run_id`, `started_at`, `status`, `rejected_count`, `reconciliation_passed`. |
| Latest ETL result message | `POST /api/warehouse/refresh`: `run_id`, `status`, and `rejected_count` are returned by the backend; the UI also tolerates optional `message`/`error_message`, which are not part of the successful refresh response shown in the current backend route. |
| Demo-data note | Static `note` returned by `GET /api/warehouse/summary`. |

### Analytics & Reports

| Display | Data source |
|---|---|
| Slicer options | `GET /api/warehouse/report`: `filters.datasets[]` (`id`, `name`, `version`), `filters.experiments[]` (`id`, `name`, `execution_mode`), `filters.strategies[]` (`name`, `label`), `filters.verdict_groups[]`, and `filters.execution_modes[]`. |
| URL filter selections | Frontend query parameters `dataset`, `experiment`, `strategy`, `verdict`, `mode`; translated into API query parameters `dataset_id`, `experiment_id`, `strategy`, `verdict_group`, `execution_mode`. |
| Response count card | `metrics.total_responses`. |
| Provisional accuracy card and Wilson 95% interval | Accuracy is `metrics.accuracy_provisional`; interval is computed in the frontend from `metrics.correct_responses` and `metrics.total_responses`. |
| Needs-review and human-reviewed card | `metrics.needs_review` and `metrics.human_reviewed`. |
| Simulated share card | `metrics.simulated_share` and `metrics.simulated_responses`. |
| Retrieval hit-rate card | `metrics.retrieval_hit_rate`, with `metrics.retrieval_measured` shown as its labelled-retrieval denominator. |
| Strategy comparison bars and intervals | `by_strategy[]`: label from `label`, proportion from `accuracy`, interval computed from `correct` and `responses` using the Wilson 95% formula. |
| Verdict distribution bars | `by_verdict[]`: category from `verdict_group`, count from `responses`. |
| Questions-to-review list | `questions_to_review[]`: `external_id`, `category`, `question_text`, `incorrect_responses`, `needs_review`. Backend returns at most 10 rows. |
| Warehouse run/freshness line | `last_etl_run.run_id`, `last_etl_run.status`, `last_etl_run.started_at`; “loaded” time is generated by the browser when the response arrives. |
| Rule-based summary | Deterministic frontend text computed from `by_strategy`, `metrics`, and `by_verdict`; accuracy detail includes the strategy Wilson 95% interval. It is **not generated by an AI model** and has no separate insights API. |
| Strategy sample-size caveat | Static note: “14 questions per strategy, no significance claimed.” |
| Analyst note/share text/download | Note is entered in local page state; share text is assembled in the browser from the note, current filters, insight strings, and URL. No backend persistence is performed. |

### Export Center

| Display | Data source |
|---|---|
| Warehouse run id, export file count, overall integrity | Export manifest fields `warehouse_run_id`, length of `files`, and `all_integrity_ok`. |
| Per-file row counts, integrity, checksum | `files[]`: `file`, `rows_in_csv`, `rows_in_database`, `integrity_ok`, `sha256`. |
| Export timestamp and snapshot notice | `exported_at_utc` and `note`. |

### Static, hardcoded, or sample-derived values

- Product names, page titles/descriptions, colors, icons, table prefix `dw_`, explanatory text, strategy descriptions, review verdict choices, and chart colors are static UI/source values.
- The new RAG UI requests `k=5`; this is a frontend constant, not a user-controlled slicer.
- Experiment Studio defaults its execution-mode selector to `demo`; it does not mean the backend always executes in demo mode.
- Empty states/fallback strings such as `UNKNOWN`, “No answer”, and “Not available” are frontend fallbacks when data is absent.
- Sample dataset and corpus contents come from `data/benchmark/sample_v1.json` and `data/documents/pilot_corpus_v1.json` when the user explicitly selects the load-sample actions. Fixture answers come from `data/fixtures/demo_responses_v1.json` through the backend demo provider. These are sample/demo data, not live model outputs.
- The Overview hero status is bound to the `status` field from `GET /api/health`; explanatory copy and the successful-status label “System Operational” remain static UI text.

## 4. Backend features not implemented and UI behavior

- **Persisted dashboard sharing/access control:** there is no report-save, user, permission, or share-token endpoint. The app encodes slicer values in the URL and uses browser sharing/copy/download/print capabilities. The URL does not grant access; recipients must be able to reach the app and its backend. Analyst notes are included when copying/downloading/sharing text but are not saved to the backend or encoded in the URL.
- **AI-authored insight narratives:** there is no insights-generation endpoint. The report constructs fixed-format sentences from returned aggregates in frontend code; it is not an LLM-generated analysis.
- **Serve/download exported CSVs from the UI:** the existing export API writes CSV snapshots under the repository `exports/` directory and returns a manifest. Export Center displays the manifest; it does not offer a CSV file-download endpoint/button.
- **Semantic fact verification:** the Answer Checker calls the existing checker endpoint, which uses a lexical-overlap heuristic. The UI shows claim-level evidence and limitations; it does not present the heuristic as a semantic truth guarantee.
- **Provider configuration screen:** the page offers execution-mode choices but no UI for setting model credentials or provider configuration. If an unavailable provider is selected, the backend error is shown in the page.
- **Real-time Power BI synchronization:** exports are CSV snapshots. Export Center does not update a PBIX or Power BI Service report. Refreshing Power BI remains a separate manual action described in `docs/powerbi_guide.md`.
- The existing backend provides only aggregate warehouse report data for `/analytics`; it does not return row-level answer text on that page. The dashboard’s “questions to review” section is based on the endpoint’s top-ten question aggregates, not an interactive detail drill-through.

## 5. New npm packages

**None were added.** `recharts`, `lucide-react`, `axios`, React, Tailwind, and `@tailwindcss/vite` were already listed in `frontend/package.json`. This work enabled the existing Tailwind Vite plugin in `vite.config.js`; it did not change `package.json` or `package-lock.json`.

## 6. Start the backend and frontend

Open two PowerShell terminals from `C:\Hallucination_Project` and keep both running.

### Backend

The repository currently has `backend/venv`. Activate it and start FastAPI:

```powershell
cd C:\Hallucination_Project\backend
.\venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

For a fresh setup, create the environment and install dependencies before starting:

```powershell
cd C:\Hallucination_Project\backend
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### Frontend

```powershell
cd C:\Hallucination_Project\frontend
npm ci
npm run dev
```

Open the Vite URL printed in the terminal (normally `http://localhost:5173`). The Vite development server proxies `/api` to `http://127.0.0.1:8000`. Keep the backend running. API documentation is at `http://127.0.0.1:8000/docs`.

## 7. Known issues and testing limits

- Validation from `frontend/`: `npm run lint` passed with no warnings; `npm run build` passed (Vite 8.3.5, 2,123 modules transformed). No backend files or npm packages were changed for this update.
- The browser smoke check visited the Overview and six workspace routes and submitted an Answer Checker example against the local backend. Analytics API report calls were also made directly, including combined filters. This does **not** constitute a full automated end-to-end test of every page or action.
- After the analytics page was added, an attempt to start Vite for a further browser smoke test failed during dependency optimization with a Rust allocator memory-allocation error. Therefore browser rendering and clipboard/native-share/print actions for the final Analytics & Reports page were not verified in that attempt.
- No backend `pytest` suite was run; `backend/tests` contained no test files when inspected.
- Real external/local LLM provider runs, Power BI Desktop refresh, PBIX publishing, remote-device share-link access, and clipboard/native-share behavior were not tested.
- Accuracy is labelled provisional by the app/backend. Demo mode is simulated fixture output. Neither the demo results nor lexical checker labels should be interpreted as verified real-world factual accuracy.
- The PBIX file was changed in a later commit, but its internal visuals, model, and data source paths were not inspected or tested for this changelog.
- `docs/project_snapshot.txt` was present as an unrelated untracked file during inspection and is not included in the documented change set.

## Deployment changes

The project can be built as one Docker web service: FastAPI serves the built React app and API from the same public URL. See [DEPLOYMENT.md](./DEPLOYMENT.md) for environment variables, local production testing, and free-tier limitations.
