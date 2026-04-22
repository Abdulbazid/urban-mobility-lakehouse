# Orchestration

Two Airflow DAGs:

| DAG | Schedule | What it does |
|---|---|---|
| `daily_mobility_etl` | `@daily` | Drains Kafka → Bronze, Bronze → Silver, dbt run+test for Gold |
| `hourly_weather` | `@hourly` | Calls Open-Meteo → Kafka `weather_raw` |

## Why two DAGs?

- Different SLAs (hourly vs daily).
- Independent retry domains — a weather API hiccup doesn't fail the main pipeline.
- Clear ownership if you later split teams.

## Idempotency patterns

- **Silver:** `replaceWhere pickup_date = '{ds}'` rewrites only the processed partition.
- **Gold:** `dbt run` on tables rebuilds them fully (cheap at this scale).
- **Bronze:** append-only, but deduped in Silver on `trip_id`, so duplicate writes don't propagate.

## Retry policy

- 2 retries with 5-min backoff for ETL tasks.
- 3 retries with 2-min backoff for the weather API (transient 5xx).

## Adding an SLA miss alert

Uncomment `sla=pendulum.duration(hours=2)` on any task. Alerts go to `default_args.sla_miss_callback` (not configured here — add Slack webhook when ready).
