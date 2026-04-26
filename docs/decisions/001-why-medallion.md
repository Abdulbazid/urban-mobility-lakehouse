# ADR 001 — Medallion Bronze/Silver/Gold

**Date:** 2026-04-24
**Status:** accepted

## Context

We need a layering scheme for a lakehouse that's easy to reason about, easy to rebuild.

## Decision

Adopt the **medallion architecture** (Bronze → Silver → Gold), popularized by Databricks.

- **Bronze:** raw ingested data. No cleaning. Immutable.
- **Silver:** cleaned, deduped, conformed. The single source of truth.
- **Gold:** business-facing marts. Denormalized, optimized for reads.

## Consequences

- Clear boundaries → easy to reason about where a bug came from.
- Any layer can be rebuilt from the one above it → cheap recovery.
- Recognizable vocabulary → interviewers nod along.
- Storage cost ~2–3× vs a single flat layer — acceptable at this scale.

## Alternatives considered

- **Raw / Staging / Prod** — same idea, different names. Picked medallion for vocabulary match to Databricks/industry.
- **Kimball staging → EDW → data mart** — heavier process. Overkill for a solo project.
