# Demo assets

Everything here is for the recruiter / interviewer. Keep it short, visual, and honest.

## Checklist

- [ ] `loom_link.txt` — 3-minute Loom walkthrough URL. Script in `STEP_BY_STEP.md` Phase 6.
- [ ] `screenshots/airflow_dag.png` — green DAG run on the `daily_mobility_etl` graph view.
- [ ] `screenshots/kafka_ui.png` — trips_raw topic with messages flowing.
- [ ] `screenshots/metabase_dashboard.png` — the surge-vs-weather dashboard.
- [ ] `screenshots/dbt_docs_lineage.png` — dbt docs lineage graph showing staging → intermediate → marts.
- [ ] `numbers.md` — one-line stats: N trips processed, P95 DAG runtime, data volume in MB.

## Script for the Loom (copy into the README of the repo)

> "Hi, I'm Abdul. This is Urban Mobility Lakehouse — a medallion pipeline that ingests simulated NYC taxi trips plus live weather, and answers 'does bad weather cause fare surges?'
>
> *(30s architecture diagram)* Kafka → Spark Bronze → Spark Silver → dbt Gold on DuckDB, orchestrated by Airflow, all in Docker.
>
> *(30s code tour)* Idempotent partition overwrite in Silver; dbt tests on uniqueness and surge plausibility; CI on every push.
>
> *(60s live run)* `make run`, trigger the DAG, watch tasks go green, open Metabase: fare uplift is ~18% in bad weather in Manhattan.
>
> *(60s wrap)* What I'd do differently at 100× scale: Iceberg + Snowflake + Kubernetes. Trade-offs in ADRs. Thanks!"

Total: ~3 minutes. Recruiters skim; keep it tight.
