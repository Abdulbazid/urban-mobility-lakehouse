# ADR 002 — Delta Lake over Iceberg / plain Parquet

**Date:** 2026-04-24
**Status:** accepted

## Context

We need ACID writes, concurrent streaming + batch writers, and time travel for reproducibility.

## Decision

Use **Delta Lake 3.2** on MinIO (S3).

## Consequences

- Gain: atomic commits, `MERGE INTO`, `VACUUM`, versioning, `replaceWhere` partition overwrite, schema evolution.
- Tight Spark integration via `io.delta:delta-spark_2.12:3.2.0`.
- DuckDB reads Delta natively with the `delta` extension — no intermediate copy for dbt.
- Lock-in risk: less portable than plain Parquet. We mitigate by keeping Bronze simple and rebuild-able.

## Alternatives considered

- **Apache Iceberg** — strong multi-engine story (Trino, Snowflake, BigQuery externals). But setup friction is higher on a single-node dev box; catalog integration (REST / Nessie / Glue) is an extra service. Revisit when we're multi-engine.
- **Plain Parquet** — no ACID, no time travel. Re-runs are tricky to make idempotent.
- **Apache Hudi** — similar capabilities; ecosystem is smaller.

## When we'd change this

If we grow to multiple engines reading the same tables (Trino + Snowflake external), migrate to Iceberg.
