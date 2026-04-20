"""Unit tests for silver cleaning logic — runs without Spark.

Pure-Python reimplementation of the filter rules, tested against sample rows.
Keeps the validation logic captured as tests even if we don't spin up Spark in CI.
"""
from datetime import datetime


def is_valid_trip(row: dict) -> bool:
    return (
        row.get("fare_amount", 0) > 0
        and 1 <= row.get("passenger_count", 0) <= 6
        and row.get("trip_distance", 0) > 0
    )


def is_bad_weather(precipitation_mm: float, wind_speed_kmh: float) -> bool:
    return precipitation_mm >= 1.0 or wind_speed_kmh >= 30


def test_valid_trip_passes():
    assert is_valid_trip({"fare_amount": 10, "passenger_count": 2, "trip_distance": 3.0})


def test_zero_fare_rejected():
    assert not is_valid_trip({"fare_amount": 0, "passenger_count": 1, "trip_distance": 1})


def test_too_many_passengers_rejected():
    assert not is_valid_trip({"fare_amount": 10, "passenger_count": 7, "trip_distance": 1})


def test_zero_distance_rejected():
    assert not is_valid_trip({"fare_amount": 10, "passenger_count": 1, "trip_distance": 0})


def test_bad_weather_by_rain():
    assert is_bad_weather(1.5, 10)


def test_bad_weather_by_wind():
    assert is_bad_weather(0, 35)


def test_mild_weather_passes():
    assert not is_bad_weather(0.2, 15)
