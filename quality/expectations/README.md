# Great Expectations suites (Week 4 extension)

dbt tests cover SQL-level assertions. Great Expectations (GX) covers richer data-quality checks at the Bronze/Silver boundary — things dbt can't easily do (distributional drift, row-count anomalies, schema evolution).

## Planned suites

### `bronze_trips.json`
- `expect_column_to_exist` for every field in `TRIP_SCHEMA`.
- `expect_column_values_to_not_be_null`: trip_id, pickup_datetime, fare_amount.
- `expect_column_values_to_be_between`: passenger_count (1, 6), fare_amount (0, 1000).
- `expect_table_row_count_to_be_between` tied to a daily rolling baseline ± 3σ.

### `silver_trips.json`
- `expect_compound_columns_to_be_unique`: [trip_id].
- `expect_column_values_to_match_regex`: pickup_date (`^\d{4}-\d{2}-\d{2}$`).
- `expect_column_pair_values_A_to_be_greater_than_B`: dropoff_ts > pickup_ts.

## Wiring

```python
# orchestration/dags/daily_mobility_etl.py
from great_expectations_provider.operators.great_expectations import GreatExpectationsOperator

validate_silver = GreatExpectationsOperator(
    task_id="validate_silver",
    data_context_root_dir="/opt/airflow/quality",
    checkpoint_name="silver_trips_checkpoint",
    fail_task_on_validation_failure=True,
)

bronze_to_silver(ds="{{ ds }}") >> validate_silver >> silver_to_gold_dbt()
```

## Why not shipped in v1

Adds ~200MB Python deps and 2 extra minutes to CI. Deferred until the user has finished Week 3 of the 30-day plan (Airflow + dbt must be rock-solid first).
