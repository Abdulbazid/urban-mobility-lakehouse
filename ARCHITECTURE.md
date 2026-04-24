# Architecture — Urban Mobility Lakehouse

## 1. Context

- **Goal:** answer *"which NYC neighborhoods surge in bad weather?"*
- **Data:** simulated TLC taxi trips (~60k msg/min), Open-Meteo hourly weather, TLC zone lookup.
- **Freshness target:** hourly good enough for the question; minute-level for the demo.
- **Scale target:** laptop-runnable today; designed to scale 10× without rewrites.

## 2. Medallion on a Lakehouse

```
   Bronze                    Silver                     Gold
   (raw, immutable)          (cleaned, joined)          (business marts)
 ┌──────────────┐          ┌──────────────┐          ┌──────────────┐
 │ trips, dated │─Spark───▶│ trips joined │──dbt────▶│ fct_trips    │
 │ by ingest    │ batch    │ to weather   │          │ dim_zones    │
 │              │          │              │          │ surge_metrics│
 │ weather      │          │              │          │              │
 └──────────────┘          └──────────────┘          └──────────────┘
       ▲                          ▲                         ▲
       Kafka drain                Idempotent                 dbt tests
       on schedule                per-date overwrite         gate DAG
```

Why medallion (defend this in interviews):
- **Bronze** = audit/replay layer. Nothing gets lost; we can always rebuild from it.
- **Silver** = single source of truth. Cleaned, deduped, typed, joined.
- **Gold** = fast reads for BI. Aggregated, denormalized, optimized for dashboards.

## 3. Decision records

See [docs/decisions/](docs/decisions/) — one file per choice.

| ADR | Decision | Because |
|---|---|---|
| 001 | Medallion Bronze/Silver/Gold | Industry-standard; clear lineage; cheap to rebuild |
| 002 | Delta Lake over Iceberg / plain Parquet | ACID + time travel + tight Spark integration |
| 003 | Kafka KRaft (no ZooKeeper) | Simpler ops; Kafka 3.7+ default |
| 004 | dbt-duckdb for marts | Fast locally; uses DuckDB's native Delta reader |
| 005 | Airflow LocalExecutor | Adequate for this scale; documented upgrade path |

## 4. Data model (Gold)

```
                  dim_zones
                  (zone_id PK)
                       │
                       │ pickup_zone_id, dropoff_zone_id
                       ▼
         ┌──────────────────────────┐
         │       fct_trips          │
         │  (trip_id PK)            │
         │  grain: 1 row per trip   │
         │  measures: fare, tip,    │
         │    total, distance, ...  │
         │  degenerate dims: hour,  │
         │    date, daypart         │
         │  weather context:        │
         │    temp, precip, wind    │
         └──────────────────────────┘
                       │
                       ▼ aggregated
                 surge_metrics
          (borough, zone, hour grain)
```

See [docs/data_model.md](docs/data_model.md) for column-level detail.

## 5. Orchestration

Two DAGs:

- **`daily_mobility_etl`** — drains Kafka → Silver → Gold → tests. Runs at midnight UTC; catches up one day of data.
- **`hourly_weather`** — fetches Open-Meteo → Kafka. Keeps Bronze weather fresh for the daily job.

Idempotency is the key property:
- Silver uses `replaceWhere pickup_date = '{ds}'` — re-runs overwrite only that partition.
- Gold is a full rebuild per run (small enough to recompute).
- Bronze is append-only but keyed by Kafka offset — duplicate writes are harmless because Silver dedups on `trip_id`.

## 6. Failure modes & mitigations

| What fails | How we notice | How we recover |
|---|---|---|
| Kafka broker down | Spark job errors within 30s | Task retries 2×; alert to console |
| Weather API 5xx | Task fails mid-fetch | Retries 3× with backoff; gap filled next hour |
| Bad source row | Silver filter drops it | Row count delta logged; if > 1% → alert (future) |
| Late-arriving trip | Silver MERGE on subsequent run | `replaceWhere` rebuilds the partition; re-run the DAG |
| Delta table corruption | `dbt run` fails with schema error | Restore via `VERSION AS OF` time-travel |
| Schema drift from upstream | dbt test fails; DAG red | Fix contract; redeploy; rerun |

## 7. Security & cost

- Secrets via `.env` (gitignored). `.env.example` shows required vars only.
- MinIO uses demo creds — ADR notes this.
- Delta `VACUUM` set to 7-day retention to bound storage.
- Producer throttled to 500 msg/s per instance (tunable).

## 8. Scaling to 100×

Prepared interview answer:

- **Storage:** migrate Delta → Iceberg for multi-engine reads; add Glue Catalog or Unity Catalog.
- **Compute:** Spark on Kubernetes or EMR Serverless, auto-scaled.
- **Orchestration:** Airflow CeleryExecutor or Dagster for asset-based lineage.
- **Streaming:** replace batch Kafka drain with real Structured Streaming with state TTL + watermarks.
- **Quality:** Great Expectations + data contracts in Schema Registry, blocking in CI.
- **Observability:** OpenLineage, freshness/volume SLOs in Grafana.

## 9. Out of scope (and why)

- **Multi-region / DR** — not needed for a single-team analytical workload.
- **PII handling** — TLC data is already anonymized; simulated data has no PII.
- **ML** — this is a DE project; models live downstream.
- **Sub-second latency** — question doesn't require it.

---

When asked "why X?" in an interview, find the answer here or in an ADR. Answering from documented decisions is much stronger than improvising.
