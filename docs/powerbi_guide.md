# Power BI Guide

This dashboard reads **CSV snapshots** exported from the warehouse. It is **not live or real-time**: new data appears only after you re-export and manually refresh in Power BI Desktop.

> Demo-mode experiments contain simulated fixture outputs, not real language-model results. Any chart built on them must be labelled as a pipeline demonstration.

## 1. Produce the CSV files
1. Start the backend (`uvicorn app.main:app --reload` in `backend`).
2. In `http://127.0.0.1:8000/docs` run `POST /api/warehouse/refresh`, then `POST /api/export/run`.
3. Check that `all_integrity_ok` is `true`. Files appear in `exports\`: `dim_dataset.csv`, `dim_question.csv`, `dim_strategy.csv`, `dim_experiment.csv`, `dim_verdict.csv`, `fact_response_evaluation.csv`, `etl_run_log.csv`, and `export_manifest.json`.

## 2. Import into Power BI Desktop
1. Home > Get data > Text/CSV. Pick one CSV, click Transform Data (or Load). Repeat for every CSV.
2. In Power Query check the data types:
   - every `*_key` and `*_id` column, `is_*`, `needs_review`, `human_reviewed`, `retrieved_count`, `latency_ms`, `answer_length_chars`, `retrieval_hit`: Whole Number
   - `retrieval_top_score`: Decimal Number
   - `created_at`, `started_at`, `finished_at`: Date/Time
   - everything else: Text
3. Close & Apply.

## 3. Create relationships (Model view)
Power BI may detect them automatically; check each one. All are Many-to-one (*:1), single direction (dimension filters fact).

| From (many) | To (one) |
|---|---|
| fact_response_evaluation[experiment_key] | dim_experiment[experiment_key] |
| fact_response_evaluation[question_key] | dim_question[question_key] |
| fact_response_evaluation[strategy_key] | dim_strategy[strategy_key] |
| fact_response_evaluation[verdict_key] | dim_verdict[verdict_key] |
| dim_question[dataset_key] | dim_dataset[dataset_key] |

Fact table grain: one row per response (one strategy's answer to one question in one experiment).

## 4. Add measures (Home > New measure, on fact_response_evaluation)
```DAX
Total Responses = COUNTROWS(fact_response_evaluation)
Correct Responses = SUM(fact_response_evaluation[is_correct])
Accuracy (provisional) = DIVIDE([Correct Responses], [Total Responses])
Needs Review = SUM(fact_response_evaluation[needs_review])
Human Reviewed = SUM(fact_response_evaluation[human_reviewed])
Failures to Abstain = CALCULATE([Total Responses], dim_verdict[verdict] = "failure_to_abstain")
Incorrect Abstentions = CALCULATE([Total Responses], dim_verdict[verdict] = "incorrect_abstention")
Retrieval Hit Rate = AVERAGE(fact_response_evaluation[retrieval_hit])
Simulated Share = AVERAGE(fact_response_evaluation[is_simulated])
```
`Retrieval Hit Rate` ignores blanks, so it covers only RAG rows with a measurable relevance label.

## 5. Report pages
**Page 1: Overview**
- Slicer: dim_experiment[experiment_name] (several experiments may hold identical demo runs, so always filter to one)
- Cards: Total Responses, Accuracy (provisional), Needs Review, Simulated Share
- Clustered column chart: axis dim_strategy[strategy_label], value Accuracy (provisional)
- Text box: "Demo mode: simulated fixture outputs, not real model results"

**Page 2: Failure analysis**
- Stacked bar: axis dim_strategy[strategy_label], legend dim_verdict[verdict_group], value Total Responses
- Table: dim_question[external_id], dim_question[question_text], dim_strategy[strategy_label], dim_verdict[verdict]; filter the visual to fact_response_evaluation[is_correct] = 0

**Page 3: RAG retrieval**
- Filter the page to dim_strategy[strategy_name] = rag
- Card: Retrieval Hit Rate
- Column chart: axis dim_question[external_id], value average of fact_response_evaluation[retrieval_top_score]

## 6. Refresh
Re-run `POST /api/warehouse/refresh` and `POST /api/export/run`, then in Power BI click Home > Refresh. If you moved the `exports` folder: Transform data > Data source settings > Change source.

## 6a. Share a filtered review in the web app
The app's **Analytics & Reports** page reads the warehouse directly and offers dataset, experiment, strategy, verdict, and execution-mode slicers. Filter selections are encoded in the page URL: use **Share review** or **Copy insight summary** to share the selected view and its generated interpretation. Add an analyst note before copying or downloading a review. Use **Print / Save PDF** for a static report.

This in-app report is separate from the PBIX file. For Power BI Desktop, share the `.pbix` file or publish it to Power BI Service (subject to your organization's licensing and sharing permissions). The CSV export itself does not publish or share the PBIX report.

## 7. Troubleshooting
| Problem | Fix |
|---|---|
| "We couldn't find the file" on refresh | The path changed. Data source settings > Change source |
| Numbers appear as text / sums show 0 | Set the column to Whole Number in Power Query |
| Relationship not detected | Create it manually in Model view with the columns listed above |
| Totals look doubled | Two experiments hold the same run. Use the experiment slicer |
| Weird characters at the start of the first column | Import with File Origin: UTF-8 |
| Export returns 409 | The last ETL run failed or never ran. Run `POST /api/warehouse/refresh` |

## 8. Limitations
- Snapshot data, manual refresh only.
- Accuracy is provisional: it contains unreviewed automatic verdicts (see Needs Review).
- Small sample (14 questions). No statistical significance is claimed.