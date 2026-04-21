# dbt Layer

dbt-duckdb reads our Silver Delta tables from MinIO directly, builds Gold marts into a DuckDB file.

## Layout

```
models/
├── sources.yml           # declares silver.trips as source
├── staging/              # views — 1:1 with source, light renames
│   └── stg_trips.sql
├── intermediate/         # reusable business-logic views
│   └── int_trips_enriched.sql
└── marts/                # tables — business-facing
    ├── fct_trips.sql
    ├── dim_zones.sql
    ├── surge_metrics.sql
    └── schema.yml        # tests
```

## Run

```bash
make dbt          # from repo root — runs deps + run + test
make docs         # dbt docs serve at http://localhost:8081
```

## Tests included

- `not_null` on every key.
- `unique` on `trip_id` and `zone_id`.
- `relationships` from fact → dim.
- `accepted_values` on `payment_type` and `borough`.
- `dbt_utils.accepted_range` on amounts and passenger counts.

Add more as business rules emerge. Failing tests stop the Airflow DAG.
