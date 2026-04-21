{{ config(materialized='view') }}

select
    trip_id,
    vendor_id,
    pickup_ts,
    pickup_date,
    pickup_hour,
    passenger_count,
    trip_distance,
    trip_duration_min,
    pickup_zone_id,
    dropoff_zone_id,
    pickup_zone_name,
    pickup_borough,
    dropoff_borough,
    fare_amount,
    surge_multiplier,
    total_amount,
    tip_amount,
    tolls_amount,
    payment_type,
    temperature_c,
    precipitation_mm,
    wind_speed_kmh,
    weather_code,
    is_bad_weather
from {{ source('silver', 'trips') }}
