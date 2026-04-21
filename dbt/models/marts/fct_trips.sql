{{ config(materialized='table') }}

-- One row per trip. Gold fact table.
select
    trip_id,
    pickup_ts,
    pickup_date,
    pickup_hour,
    pickup_zone_id,
    dropoff_zone_id,
    pickup_borough,
    dropoff_borough,
    daypart,
    passenger_count,
    trip_distance,
    trip_duration_min,
    fare_amount,
    tip_amount,
    tolls_amount,
    total_amount,
    surge_multiplier,
    tip_rate,
    revenue_per_mile,
    payment_type,
    temperature_c,
    precipitation_mm,
    wind_speed_kmh,
    is_bad_weather
from {{ ref('int_trips_enriched') }}
