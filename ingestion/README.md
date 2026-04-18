# Ingestion Layer

## What this does

Two producers feed Kafka topics that downstream jobs consume:

| Script | Output topic | Frequency | Run by |
|---|---|---|---|
| `trip_producer.py` | `trips_raw` | continuous (500 msg/s) | `make seed` or Airflow |
| `weather_fetcher.py` | `weather_raw` | hourly | Airflow DAG `daily_mobility_etl` |

## Contract (the schema we commit to)

### `trips_raw` message (JSON, keyed by `trip_id`)

```json
{
  "trip_id": "uuid",
  "vendor_id": 1,
  "pickup_datetime": "2026-04-24T15:01:23Z",
  "dropoff_datetime": "2026-04-24T15:14:55Z",
  "passenger_count": 1,
  "trip_distance": 2.3,
  "trip_duration_min": 13,
  "pickup_zone_id": 161,
  "dropoff_zone_id": 237,
  "pickup_zone_name": "Midtown Center",
  "pickup_borough": "Manhattan",
  "dropoff_borough": "Manhattan",
  "fare_amount": 12.50,
  "surge_multiplier": 1.25,
  "total_amount": 15.80,
  "tip_amount": 2.50,
  "tolls_amount": 0.80,
  "payment_type": 1
}
```

### `weather_raw` message (JSON, keyed by `observation_time`)

```json
{
  "observation_time": "2026-04-24T15:00:00Z",
  "latitude": 40.7128,
  "longitude": -74.0060,
  "temperature_c": 14.2,
  "precipitation_mm": 0.3,
  "wind_speed_kmh": 12.7,
  "weather_code": 61,
  "ingested_at": "2026-04-24T15:05:01Z"
}
```

## Swap the simulator for real TLC data (Week 2 upgrade)

1. Download TLC parquet: https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page
2. Replace `trip_producer.py`'s `make_trip()` loop with a parquet reader:

   ```python
   import pyarrow.parquet as pq
   table = pq.read_table("yellow_tripdata_2024-01.parquet")
   for batch in table.to_batches(max_chunksize=1000):
       for row in batch.to_pylist():
           producer.send(topic, key=str(row["trip_id"]), value=row)
   ```
3. Add an ADR documenting the switch.

## Run locally (outside Docker)

```bash
cd ingestion
pip install -r requirements.txt
KAFKA_BOOTSTRAP=localhost:9092 python trip_producer.py --duration 30
pytest -v
```
