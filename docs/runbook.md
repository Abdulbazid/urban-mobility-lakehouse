# Runbook — "something is broken, now what"

## First checks (always)

```bash
docker compose ps                       # is everything `healthy`?
docker compose logs <service> --tail 100
df -h                                   # disk full?
free -m                                 # memory?
```

---

## Top 10 issues you'll hit

### 1. Docker Desktop out of memory
**Symptom:** containers restart; Spark OOMs.
**Fix:** Docker Desktop → Settings → Resources → at least 6 GB RAM, 4 CPU.

### 2. Port already allocated
**Symptom:** `docker compose up` fails with "port is already allocated".
**Fix:** find what's using it — `lsof -i :9092` (or 5432/8088/etc.) — kill it, or remap the port in `docker-compose.yml`.

### 3. MinIO bucket doesn't exist
**Symptom:** Spark job fails with `NoSuchBucket`.
**Fix:** `make setup` again. The `createbuckets` service idempotently creates them.

### 4. Kafka not ready when producer starts
**Symptom:** `make seed` fails with "NoBrokersAvailable".
**Fix:** wait 15s after `make run`. Or check `docker compose logs kafka | grep "started"`.

### 5. Airflow DAG not appearing
**Symptom:** DAG missing from the UI.
**Fix:**
```bash
docker compose exec airflow-scheduler airflow dags list
docker compose exec airflow-scheduler airflow dags reserialize
```
Usually a Python syntax error in the DAG file — check scheduler logs.

### 6. Spark can't write to MinIO
**Symptom:** `s3a://... 403 AccessDenied`.
**Fix:** check `S3_ACCESS_KEY` / `S3_SECRET_KEY` env vars are passed to the Spark container. MinIO console → Users → verify creds match.

### 7. dbt fails with "table does not exist"
**Symptom:** `dbt run` fails reading `delta_scan('s3://silver/trips')`.
**Fix:** silver table not built yet. Run the Airflow DAG first, or run `transformation/batch/silver_clean.py` manually.

### 8. Delta "not a Delta table" error
**Symptom:** Reading a path that was written as plain Parquet.
**Fix:** check you wrote with `.format("delta")`. To convert existing Parquet → Delta, use `DeltaTable.convertToDelta(spark, 'parquet.`s3a://path`')`.

### 9. dbt_utils not found
**Symptom:** `dbt_utils.accepted_range` is undefined.
**Fix:** run `dbt deps` first. Should happen automatically in `make dbt`.

### 10. Metabase can't connect to DuckDB
**Symptom:** "Connection refused" in Metabase.
**Fix:** Metabase container has `./dbt:/data:ro` mount. The DuckDB file path inside Metabase is `/data/gold.duckdb`. Ensure `dbt run` created the file.

---

## Emergency reset (nuclear option)

```bash
make clean          # stops + wipes all volumes
make setup
make run
make seed
```

Takes ~5 minutes. You lose all local data but the pipeline rebuilds cleanly.

---

## Collecting logs for a bug report

```bash
docker compose logs > logs.txt
docker compose ps > state.txt
```

Attach these to any issue / Stack Overflow question.
