"""Daily orchestration — Kafka drain → Silver → Gold (dbt) → Tests.

Pattern highlights (talk about these in interviews):
- Idempotent: `replaceWhere` partition overwrite in silver, table rebuild in gold
- Fail-fast DQ: dbt test runs BEFORE we consider the day "done"
- Weather fetcher runs hourly via a separate schedule
- Retries: 2× with 5 min backoff for transient network/S3 issues
"""
from __future__ import annotations
import pendulum
from airflow.decorators import dag, task
from airflow.exceptions import AirflowFailException


@dag(
    dag_id="daily_mobility_etl",
    start_date=pendulum.datetime(2026, 4, 1, tz="UTC"),
    schedule="@daily",
    catchup=False,
    max_active_runs=1,
    default_args={
        "retries": 2,
        "retry_delay": pendulum.duration(minutes=5),
        "owner": "abdul",
    },
    tags=["portfolio", "medallion", "daily"],
    doc_md=__doc__,
)
def daily_mobility_etl():

    @task
    def drain_bronze_trips() -> int:
        """Read `trips_raw` from Kafka, append to bronze Delta."""
        import subprocess
        result = subprocess.run(
            ["python", "/opt/airflow/transformation/streaming/bronze_writer.py",
             "--topic", "trips_raw"],
            capture_output=True, text=True)
        print(result.stdout)
        if result.returncode != 0:
            print(result.stderr)
            raise AirflowFailException("bronze_writer failed for trips_raw")
        return 0

    @task
    def drain_bronze_weather() -> int:
        import subprocess
        result = subprocess.run(
            ["python", "/opt/airflow/transformation/streaming/bronze_writer.py",
             "--topic", "weather_raw"],
            capture_output=True, text=True)
        print(result.stdout)
        if result.returncode != 0:
            print(result.stderr)
            raise AirflowFailException("bronze_writer failed for weather_raw")
        return 0

    @task
    def bronze_to_silver(ds: str = None) -> int:
        import subprocess
        result = subprocess.run(
            ["python", "/opt/airflow/transformation/batch/silver_clean.py",
             "--date", ds],
            capture_output=True, text=True)
        print(result.stdout)
        if result.returncode != 0:
            print(result.stderr)
            raise AirflowFailException("silver_clean failed")
        return 0

    @task
    def silver_to_gold_dbt() -> int:
        """Build marts + run tests. dbt test failure fails the task."""
        import subprocess
        for cmd in (["dbt", "deps"], ["dbt", "run"], ["dbt", "test"]):
            r = subprocess.run(cmd, cwd="/usr/app", capture_output=True, text=True)
            print(r.stdout)
            if r.returncode != 0:
                print(r.stderr)
                raise AirflowFailException(f"dbt {' '.join(cmd)} failed")
        return 0

    @task
    def announce(ds: str = None) -> None:
        print(f"✅ Urban Mobility Lakehouse refresh complete for {ds}")

    # Chain
    trips   = drain_bronze_trips()
    weather = drain_bronze_weather()
    silver  = bronze_to_silver()
    gold    = silver_to_gold_dbt()
    done    = announce()

    [trips, weather] >> silver >> gold >> done


daily_mobility_etl()
