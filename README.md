# Urban Mobility Lakehouse 🚖🌦️

> Answering: **which NYC neighborhoods surge in bad weather?**

An end-to-end streaming + batch analytics pipeline on a local lakehouse.
Built as a portfolio project — mirrors production patterns (medallion architecture, ACID lake tables, CDC-ready ingestion, orchestrated workflows, tested transformations).

## 🎯 At a glance

- **Simulated NYC taxi trip stream** → Kafka → Spark → Delta Lake (Bronze)
- **Open-Meteo weather API** → Airflow hourly fetch → Delta Lake (Bronze)
- **Spark batch** cleans + dedups + joins → Silver
- **dbt + DuckDB** builds marts on Silver Delta → Gold
- **Airflow** orchestrates the whole thing daily with idempotent loads
- **Metabase** dashboards the "bad-weather surge" question
- **GitHub Actions** runs `pytest` + `dbt test` on every push

## 🏗 Architecture

```
 SOURCES              INGEST             STORAGE (MinIO S3)       TRANSFORM         SERVE
 ┌──────────┐       ┌──────────┐       ┌──────────────┐        ┌──────────┐    ┌──────────┐
 │ trip     │──────▶│ Producer │──────▶│ Bronze Delta │───────▶│  Silver  │───▶│  Gold    │
 │ sim      │       │ Python   │ Kafka │ raw, typed   │ Spark  │ cleaned, │dbt │  marts   │──▶ Metabase
 └──────────┘       └──────────┘       └──────────────┘        │ joined   │    └──────────┘
 ┌──────────┐       ┌──────────┐       ┌──────────────┐        └──────────┘
 │ weather  │──────▶│ Fetcher  │──────▶│ Bronze Delta │
 │ API      │       │ Airflow  │ Kafka │ weather      │
 └──────────┘       └──────────┘       └──────────────┘
                              orchestrated by Airflow · tested in CI
```

Full architecture + trade-offs: **[ARCHITECTURE.md](ARCHITECTURE.md)**
Decision records: **[docs/decisions/](docs/decisions/)**

## 🚀 Quickstart (5 minutes)

```bash
git clone https://github.com/<you>/urban-mobility-lakehouse
cd urban-mobility-lakehouse
cp .env.example .env
make setup      # pulls docker images, creates buckets + topics
make run        # starts the full stack
make seed       # starts the trip simulator + fetches initial weather
make dbt        # builds Silver + Gold + runs tests
```

Then open:
- **Airflow** → http://localhost:8088 (admin / admin)
- **MinIO** → http://localhost:9001 (minioadmin / minioadmin)
- **Kafka UI** → http://localhost:8080
- **Metabase** → http://localhost:3000

## 📚 Documentation

| Doc | Purpose |
|---|---|
| [STEP_BY_STEP.md](STEP_BY_STEP.md) | **Start here** — exactly what to do, in order |
| [ARCHITECTURE.md](ARCHITECTURE.md) | System design & trade-offs |
| [docs/data_model.md](docs/data_model.md) | Star schema, grains, SCD strategy |
| [docs/runbook.md](docs/runbook.md) | "It broke, now what" |
| [docs/decisions/](docs/decisions/) | ADRs for every non-trivial choice |

## 🛣 Roadmap

- [ ] Swap simulated trips for real NYC TLC parquet
- [ ] Migrate Delta → Iceberg for multi-engine catalog
- [ ] Add Schema Registry + data contracts
- [ ] Terraform module to deploy to AWS EMR Serverless

## 📜 License

MIT
