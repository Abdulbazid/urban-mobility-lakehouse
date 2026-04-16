# ADR 003 — Kafka KRaft (no ZooKeeper)

**Date:** 2026-04-24
**Status:** accepted

## Context

Need a message broker. Kafka is the industry default.

## Decision

Use **Kafka 3.7 in KRaft mode** — Kafka's built-in Raft-based metadata quorum, replacing ZooKeeper.

## Consequences

- One container instead of two → simpler local stack.
- Faster broker startup (~5s vs ~15s with ZK).
- Kafka 3.3+ marked KRaft as production-ready; 3.7 is stable.
- Some older tutorials still show ZK; newcomers may be confused. Note in README.

## Alternatives considered

- **Kafka + ZooKeeper** — the classic mode. Still works but officially deprecated in future versions.
- **Redpanda** — Kafka API, single binary, no JVM. Strong candidate. Not picked because interviewers expect Kafka on the resume.
