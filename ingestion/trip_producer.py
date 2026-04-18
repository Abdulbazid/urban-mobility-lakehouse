"""Simulate NYC taxi trips and publish to Kafka topic `trips_raw`.

This mirrors real-world streaming ingestion. In the real project, swap this
for a consumer of the TLC parquet files (see ingestion/README.md).

Throughput: ~500 messages/sec per producer; run two for 1k/sec.
"""
from __future__ import annotations
import argparse
import json
import os
import random
import time
import uuid
from datetime import datetime, timezone

from kafka import KafkaProducer

# NYC TLC taxi zones — subset of real zones with borough mapping
ZONES = [
    (1, "Newark Airport", "EWR"),
    (13, "Battery Park City", "Manhattan"),
    (48, "Clinton East", "Manhattan"),
    (79, "East Village", "Manhattan"),
    (87, "Financial District North", "Manhattan"),
    (100, "Garment District", "Manhattan"),
    (138, "LaGuardia Airport", "Queens"),
    (161, "Midtown Center", "Manhattan"),
    (162, "Midtown East", "Manhattan"),
    (186, "Penn Station/Madison Sq West", "Manhattan"),
    (230, "Times Sq/Theatre District", "Manhattan"),
    (236, "Upper East Side North", "Manhattan"),
    (237, "Upper East Side South", "Manhattan"),
    (239, "Upper West Side South", "Manhattan"),
    (249, "West Village", "Manhattan"),
    (263, "Yorkville West", "Manhattan"),
    (132, "JFK Airport", "Queens"),
    (7, "Astoria", "Queens"),
    (40, "Carroll Gardens", "Brooklyn"),
    (33, "Brooklyn Heights", "Brooklyn"),
]
VENDOR_IDS = [1, 2]
PAYMENT_TYPES = [1, 2, 3, 4]  # 1=credit, 2=cash, 3=no charge, 4=dispute


def make_trip() -> dict:
    """Produce one simulated trip record with TLC-compatible schema."""
    pickup = random.choice(ZONES)
    dropoff = random.choice(ZONES)
    # Trip time and distance correlated; add some noise
    distance_mi = round(max(0.1, random.gauss(2.5, 1.8)), 2)
    duration_min = max(1, int(distance_mi * random.uniform(3, 8)))
    base_fare = 2.50 + distance_mi * 2.75 + duration_min * 0.35
    # Surge-like multiplier (we'll correlate with weather in silver)
    surge = random.choices([1.0, 1.25, 1.5, 2.0], weights=[70, 20, 8, 2])[0]
    fare = round(base_fare * surge, 2)
    tip = round(fare * random.uniform(0, 0.3), 2) if random.random() < 0.7 else 0.0
    tolls = round(random.choices([0, 0, 0, 5.76, 6.55], weights=[80, 5, 5, 5, 5])[0], 2)
    now = datetime.now(timezone.utc)
    return {
        "trip_id": str(uuid.uuid4()),
        "vendor_id": random.choice(VENDOR_IDS),
        "pickup_datetime": now.isoformat(),
        "dropoff_datetime": now.isoformat(),  # simplified
        "passenger_count": random.choices([1, 2, 3, 4, 5, 6], weights=[60, 20, 8, 5, 4, 3])[0],
        "trip_distance": distance_mi,
        "trip_duration_min": duration_min,
        "pickup_zone_id": pickup[0],
        "dropoff_zone_id": dropoff[0],
        "pickup_zone_name": pickup[1],
        "pickup_borough": pickup[2],
        "dropoff_borough": dropoff[2],
        "fare_amount": round(base_fare, 2),
        "surge_multiplier": surge,
        "total_amount": round(fare + tip + tolls, 2),
        "tip_amount": tip,
        "tolls_amount": tolls,
        "payment_type": random.choice(PAYMENT_TYPES),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--duration", type=int, default=120,
                    help="seconds to run (default 120 = 2 min)")
    ap.add_argument("--rate", type=int, default=500,
                    help="messages per second")
    args = ap.parse_args()

    bootstrap = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")
    topic = os.getenv("KAFKA_TOPIC_TRIPS", "trips_raw")

    print(f"▶ producing to {topic} at {bootstrap} for {args.duration}s @ {args.rate}/s")
    producer = KafkaProducer(
        bootstrap_servers=[bootstrap],
        key_serializer=lambda k: str(k).encode(),
        value_serializer=lambda v: json.dumps(v).encode(),
        acks="all", linger_ms=10, compression_type="lz4",
    )

    deadline = time.time() + args.duration
    sent = 0
    interval = 1.0 / args.rate
    try:
        while time.time() < deadline:
            evt = make_trip()
            producer.send(topic, key=evt["trip_id"], value=evt)
            sent += 1
            if sent % 5000 == 0:
                print(f"  sent {sent:,}")
                producer.flush()
            time.sleep(interval)
    except KeyboardInterrupt:
        print("interrupted")
    finally:
        producer.flush()
        producer.close()
        print(f"✅ done. total: {sent:,}")


if __name__ == "__main__":
    main()
