"""Fetch current + recent weather from Open-Meteo (free, no key) and publish to Kafka.

Called from Airflow hourly. One message per hour per location.
"""
from __future__ import annotations
import json
import os
from datetime import datetime, timezone

import requests
from kafka import KafkaProducer

API = "https://api.open-meteo.com/v1/forecast"


def fetch(lat: float, lon: float) -> list[dict]:
    """Return a list of hourly weather records for the last 24h + current day."""
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "temperature_2m,precipitation,wind_speed_10m,weathercode",
        "past_days": 1,
        "forecast_days": 1,
        "timezone": "UTC",
    }
    r = requests.get(API, params=params, timeout=30)
    r.raise_for_status()
    data = r.json()["hourly"]
    records = []
    for i, t in enumerate(data["time"]):
        records.append({
            "observation_time": t,
            "latitude": lat,
            "longitude": lon,
            "temperature_c": data["temperature_2m"][i],
            "precipitation_mm": data["precipitation"][i],
            "wind_speed_kmh": data["wind_speed_10m"][i],
            "weather_code": data["weathercode"][i],
            "ingested_at": datetime.now(timezone.utc).isoformat(),
        })
    return records


def main() -> None:
    bootstrap = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")
    topic = os.getenv("KAFKA_TOPIC_WEATHER", "weather_raw")
    lat = float(os.getenv("WEATHER_LAT", "40.7128"))
    lon = float(os.getenv("WEATHER_LON", "-74.0060"))

    print(f"▶ fetching weather ({lat},{lon}) → {topic}")
    records = fetch(lat, lon)

    producer = KafkaProducer(
        bootstrap_servers=[bootstrap],
        key_serializer=lambda k: str(k).encode(),
        value_serializer=lambda v: json.dumps(v).encode(),
    )
    for r in records:
        producer.send(topic, key=r["observation_time"], value=r)
    producer.flush()
    producer.close()
    print(f"✅ sent {len(records)} hourly records")


if __name__ == "__main__":
    main()
