# ADR 005 — Airflow LocalExecutor

**Date:** 2026-04-24
**Status:** accepted

## Context

Need orchestration with retries, SLAs, backfills, idempotency.

## Decision

**Airflow 2.9 with LocalExecutor** + Postgres metastore.

## Consequences

- Handles our daily + hourly schedules comfortably.
- Standard tool — recruiters recognize it instantly.
- Not cluster-scale. At 100× we'd move to CeleryExecutor or KubernetesExecutor.

## Alternatives considered

- **Dagster** — nicer asset-based modeling, improving lineage story. Less hiring-market recognition.
- **Prefect** — Python-native, easier learning curve. Same market-recognition caveat.
- **Cron + bash** — rejected; no retries, no backfills, no UI.
