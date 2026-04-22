"""Hourly weather fetch from Open-Meteo into Kafka topic weather_raw."""
from __future__ import annotations
import pendulum
from airflow.decorators import dag, task


@dag(
    dag_id="hourly_weather",
    start_date=pendulum.datetime(2026, 4, 1, tz="UTC"),
    schedule="@hourly",
    catchup=False,
    max_active_runs=1,
    default_args={"retries": 3, "retry_delay": pendulum.duration(minutes=2)},
    tags=["portfolio", "ingest"],
)
def hourly_weather():

    @task
    def fetch() -> int:
        import subprocess, sys
        r = subprocess.run(
            [sys.executable, "/opt/airflow/transformation/../ingestion/weather_fetcher.py"],
            capture_output=True, text=True)
        print(r.stdout)
        if r.returncode != 0:
            print(r.stderr)
            raise RuntimeError("weather_fetcher failed")
        return 0

    fetch()


hourly_weather()
