# Dashboards

Metabase connects to `dbt/gold.duckdb` (mounted read-only into the Metabase container at `/data/gold.duckdb`).

## Setup

1. Open http://localhost:3000 after `make run`.
2. Create admin user (first-run wizard).
3. **Add Database** → DuckDB (community driver) or H2 if the DuckDB driver plugin isn't loaded. Path: `/data/gold.duckdb`.
4. Build these questions:

| # | Question | SQL |
|---|---|---|
| 1 | Fare uplift % by borough (bad vs good weather) | `SELECT borough, AVG(fare_uplift_pct) FROM surge_metrics GROUP BY 1 ORDER BY 2 DESC` |
| 2 | Trips per hour-of-day | `SELECT pickup_hour, COUNT(*) FROM fct_trips GROUP BY 1 ORDER BY 1` |
| 3 | Top 10 zones by revenue | `SELECT pickup_zone_id, SUM(total_amount) r FROM fct_trips GROUP BY 1 ORDER BY r DESC LIMIT 10` |
| 4 | Avg tip rate by daypart | `SELECT daypart, AVG(tip_rate) FROM fct_trips GROUP BY 1` |
| 5 | Bad-weather trip share over time | `SELECT pickup_date, AVG(is_bad_weather::INT) FROM fct_trips GROUP BY 1 ORDER BY 1` |

## Exporting the dashboard

Metabase doesn't have a clean export API for OSS — take PNG screenshots into `dashboards/screenshots/` and commit them. Reviewers see them directly on GitHub.

## Alternative: Apache Superset

Swap Metabase for Superset if you prefer open-source BI with git-checked-in YAML configs. Same DuckDB connection.
