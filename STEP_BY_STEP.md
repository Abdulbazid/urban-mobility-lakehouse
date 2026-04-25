# Step-by-Step Guide — from zero to working project

This is the only doc you need to follow in order. Do these steps and you'll have a runnable, demo-able, recruiter-ready project.

Estimated total time: **4–6 hours of hands-on work** spread over 2 weeks (alongside your 30-day prep).

---

## Phase 0 — Prerequisites (15 min)

Install on your machine (one-time):

- [ ] **Docker Desktop** (or Docker + Compose on Linux). Verify: `docker --version` and `docker compose version`.
- [ ] **Git**. Verify: `git --version`.
- [ ] **Python 3.11+** (for running producer locally, optional). Verify: `python3 --version`.
- [ ] **GitHub account** with SSH key set up. Verify: `ssh -T git@github.com`.

Give Docker Desktop at least **6 GB RAM** in its settings (Preferences → Resources). Kafka + Spark + Airflow are memory-hungry.

---

## Phase 1 — Push to GitHub (20 min)

1. On GitHub, create a new **public** repo named `urban-mobility-lakehouse`. **Don't** initialize it with a README (we already have one).
2. On your laptop:

   ```bash
   cd /home/abdul-bazid/Documents/Claude/Projects/learnings/urban-mobility-lakehouse
   git init
   git add .
   git commit -m "feat: initial project skeleton"
   git branch -M main
   git remote add origin git@github.com:<your-username>/urban-mobility-lakehouse.git
   git push -u origin main
   ```

3. Open your repo on GitHub. Take a screenshot of the README rendering. That's your Day-1 deliverable.

4. Post on LinkedIn: *"Starting my 30-day DE prep with a portfolio project — Urban Mobility Lakehouse. Architecture below. Will post weekly updates."* Attach the architecture diagram. Public commitment → follow-through.

---

## Phase 2 — Bring up the stack (10 min)

```bash
cp .env.example .env          # default values work fine
make setup                     # pulls docker images (~2 GB, one-time)
make run                       # brings up Kafka, MinIO, Airflow, Metabase
```

Check each UI loads:

- [ ] http://localhost:9001 (MinIO) — log in with `minioadmin` / `minioadmin`. See buckets `bronze`, `silver`, `gold`.
- [ ] http://localhost:8080 (Kafka UI) — see topic `trips_raw` and `weather_raw`.
- [ ] http://localhost:8088 (Airflow) — log in `admin` / `admin`. See DAG `daily_mobility_etl` (paused).
- [ ] http://localhost:3000 (Metabase) — first-run setup, create an admin user.

If anything fails, check `docker compose logs <service>` and see `docs/runbook.md`.

---

## Phase 3 — Seed some data (5 min)

```bash
make seed                      # runs producer for 2 minutes → ~60k trips into Kafka
```

Open Kafka UI → topic `trips_raw` → Messages tab → you should see JSON payloads streaming in.

---

## Phase 4 — Run the first transformation (10 min)

In the Airflow UI:

1. Unpause the `daily_mobility_etl` DAG.
2. Trigger it manually (▶ button).
3. Watch the task graph go green:
   - `wait_for_bronze_data` ✅
   - `bronze_to_silver` ✅
   - `silver_to_gold_dbt` ✅
   - `run_data_quality_tests` ✅

In MinIO, browse to `silver/trips/` — Parquet files partitioned by `pickup_date`.

---

## Phase 5 — Connect the dashboard (20 min)

In Metabase:

1. Add a database → **DuckDB** (or Presto/Trino if you prefer, but DuckDB is simplest):
   - Name: `gold`
   - Path: `/data/gold.duckdb` (this is mounted from `./dbt/gold.duckdb` inside the container)
2. Create 4 questions:
   - **Trips per hour** (line chart, x=hour, y=count)
   - **Fare heatmap by zone** (pivot or map if you have lat/lon dim)
   - **Surge ratio vs precipitation** (scatter)
   - **Top 10 zones by revenue** (bar)
3. Save them to a dashboard called "Urban Mobility".
4. Export dashboard JSON to `dashboards/metabase_export.json` and commit.
5. Screenshot each panel → `demo/screenshots/`.

---

## Phase 6 — Record the demo (30 min)

Use **Loom** (https://loom.com — free) or OBS.

Script (rehearse twice before recording):

1. **0:00–0:20** The question: "Do NYC cabs surge in bad weather?" Show the dashboard.
2. **0:20–1:00** Walk the architecture diagram on screen.
3. **1:00–1:40** Show the Airflow DAG running green; open one task log.
4. **1:40–2:20** Show the dbt docs lineage graph (`dbt docs serve`).
5. **2:20–2:50** Open one hard decision (ADR) — read the trade-off.
6. **2:50–3:00** "Code is at github.com/<you>/urban-mobility-lakehouse. Happy to walk you through it."

Upload → paste URL into `demo/loom_link.txt` → add it to the README.

---

## Phase 7 — Polish for recruiters (60 min)

- [ ] Pin the repo to your GitHub profile.
- [ ] Add topics: `data-engineering`, `apache-spark`, `apache-kafka`, `delta-lake`, `dbt`, `airflow`.
- [ ] Turn on Discussions; pin an issue titled "Future work" with the roadmap.
- [ ] Add the Loom link + architecture diagram as the first thing in README.
- [ ] Add a CI badge to README (`![CI](https://github.com/.../ci.yml/badge.svg)`).
- [ ] Update your resume:
  > **Urban Mobility Lakehouse** · Python, Spark, Kafka, Delta, dbt, Airflow, MinIO (S3)
  > End-to-end streaming + batch pipeline: 60k events/min through Kafka, medallion architecture on Delta Lake, Airflow-orchestrated daily loads with idempotent `MERGE`, dbt models with data tests, Metabase dashboard. GitHub: ...
- [ ] Update LinkedIn featured section — pin the repo.

---

## Phase 8 — Extend as you go through the 30 days

After the basic pipeline works, upgrade it each week alongside your learning:

| Week you're on | Upgrade to make |
|---|---|
| Week 1 (SQL) | Add 3 more complex dbt models with window functions — running averages, rank. |
| Week 2 (Big Data) | Swap simulator for **real TLC parquet** (see `ingestion/README.md`). Tune a Spark job — document before/after shuffle time. |
| Week 3 (Cloud) | Add a **Terraform stub** deploying the stack to AWS (EMR Serverless + S3 + MWAA). Don't actually run it; document. |
| Week 4 (Polish) | Add **Great Expectations** suites on Bronze & Silver. Wire them into Airflow as gate tasks. |

Each upgrade = 1 commit + 1 ADR + 1 LinkedIn post about what you learned. Over 4 weeks that's ~16 posts — recruiters will find you.

---

## When something breaks

1. Always check: `docker compose ps` — is everything `healthy`?
2. `docker compose logs <service> --tail 100` — read the last errors.
3. `docs/runbook.md` has the top 10 issues and fixes.
4. If truly stuck, revert to the last green commit and re-apply smaller steps.

---

## Deliverables checklist

At the end, your GitHub repo should have:

- [x] Clean README with pitch, diagram, quickstart, demo link
- [x] ARCHITECTURE.md + 5 ADRs
- [x] Working `make run` that brings up the full stack
- [x] A green CI badge
- [x] 30+ commits spread over ≥2 weeks
- [x] A Loom demo video
- [x] A dashboard with 4+ panels
- [x] Updated resume + LinkedIn

**That's the portfolio piece. You're done.**
