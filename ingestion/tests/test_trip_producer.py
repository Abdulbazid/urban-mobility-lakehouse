"""Unit tests for the trip generator — pure functions, no Kafka needed."""
from trip_producer import make_trip, ZONES


def test_trip_has_required_fields():
    t = make_trip()
    required = {
        "trip_id", "pickup_datetime", "dropoff_datetime",
        "pickup_zone_id", "dropoff_zone_id", "fare_amount",
        "total_amount", "passenger_count", "trip_distance",
    }
    assert required.issubset(t.keys())


def test_fare_is_positive():
    for _ in range(100):
        t = make_trip()
        assert t["fare_amount"] > 0
        assert t["total_amount"] >= t["fare_amount"]  # tip + tolls added


def test_zones_are_valid():
    valid_ids = {z[0] for z in ZONES}
    for _ in range(100):
        t = make_trip()
        assert t["pickup_zone_id"] in valid_ids
        assert t["dropoff_zone_id"] in valid_ids


def test_passenger_count_in_range():
    for _ in range(100):
        t = make_trip()
        assert 1 <= t["passenger_count"] <= 6


def test_surge_multiplier_valid():
    for _ in range(100):
        t = make_trip()
        assert t["surge_multiplier"] in (1.0, 1.25, 1.5, 2.0)
