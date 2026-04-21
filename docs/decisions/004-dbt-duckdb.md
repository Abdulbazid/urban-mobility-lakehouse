# ADR 004 — dbt-duckdb for marts

**Date:** 2026-04-24
**Status:** accepted

## Context

We want SQL-level transforms with tests, docs, and lineage on top of our Silver Delta tables.

## Decision

Use **dbt-core 1.8 + dbt-duckdb 1.8** with DuckDB's native `delta` and `httpfs` extensions. DuckDB reads Silver Delta directly from MinIO via `delta_scan('s3://silver/trips/')`.

## Consequences

- Zero data copy — DuckDB pushes down predicates/column projections into Delta.
- Fast local runs (DuckDB is in-process).
- `dbt test`, `dbt docs generate`, lineage graph all free.
- Trade-off: single-node compute. At 100× scale we'd swap the adapter to `dbt-spark` or `dbt-snowflake`.

## Alternatives considered

- **dbt-spark** — same code, runs on our existing Spark cluster. Slower locally; more setup.
- **dbt-postgres** — would require loading Silver into Postgres. Extra step.
- **Raw Spark SQL** — works, but we'd re-implement tests/docs/lineage ourselves.
