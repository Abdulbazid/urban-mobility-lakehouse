# Transformation Layer

Spark jobs that move data through the medallion: **Bronze → Silver → Gold**.

| Job | Input | Output | Trigger |
|---|---|---|---|
| `streaming/bronze_writer.py` | Kafka `trips_raw`, `weather_raw` | `s3a://bronze/trips/`, `s3a://bronze/weather/` | streaming (or triggered batch from Airflow) |
| `batch/silver_clean.py` | `s3a://bronze/trips/`, `s3a://bronze/weather/` | `s3a://silver/trips/` | daily Airflow task |
| `batch/gold_aggregates.py` | `s3a://silver/trips/` | `s3a://gold/surge_metrics/` | daily Airflow task (or dbt) |

All outputs are **Delta** tables — ACID, time-travel, schema-evolution enabled.

## Why Spark (and not plain Python/Pandas)

At 60k trips/minute × 24h we're at ~80M rows/day. Pandas would swap; Spark scales horizontally and Delta gives us idempotent writes. See [ADR 001](../docs/decisions/001-why-medallion.md).

## Partitioning strategy

- **Bronze:** `ingestion_date` (when we received it). We never mutate; we append.
- **Silver:** `pickup_date` (when the trip actually happened). Queries filter by this.
- **Gold:** `pickup_date`. Small and dense.

## Run a Spark job locally

```bash
docker compose run --rm dbt bash          # re-use the container shell
# or spin up a Spark-ready container
docker run --rm -it -v $(pwd):/app bitnami/spark:3.5 \
  spark-submit --packages io.delta:delta-spark_2.12:3.2.0,org.apache.hadoop:hadoop-aws:3.3.4 \
               /app/transformation/batch/silver_clean.py
```

In practice, these are run **from the Airflow DAG** — you shouldn't need to invoke them manually.
