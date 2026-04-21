{{ config(materialized='table') }}

-- The headline answer to the business question:
-- "which neighborhoods surge in bad weather?"
with per_hour_zone as (
    select
        pickup_borough,
        pickup_zone_name,
        pickup_hour,
        is_bad_weather,
        count(*)                  as trips,
        avg(fare_amount)          as avg_fare,
        avg(surge_multiplier)     as avg_surge,
        avg(precipitation_mm)     as avg_precip_mm,
        avg(wind_speed_kmh)       as avg_wind_kmh
    from {{ ref('int_trips_enriched') }}
    group by 1, 2, 3, 4
),
pivoted as (
    select
        pickup_borough,
        pickup_zone_name,
        pickup_hour,
        sum(case when not is_bad_weather then trips     end) as trips_good,
        sum(case when     is_bad_weather then trips     end) as trips_bad,
        avg(case when not is_bad_weather then avg_fare  end) as fare_good,
        avg(case when     is_bad_weather then avg_fare  end) as fare_bad,
        avg(case when not is_bad_weather then avg_surge end) as surge_good,
        avg(case when     is_bad_weather then avg_surge end) as surge_bad
    from per_hour_zone
    group by 1, 2, 3
)
select
    pickup_borough,
    pickup_zone_name,
    pickup_hour,
    coalesce(trips_good, 0) as trips_good,
    coalesce(trips_bad,  0) as trips_bad,
    fare_good,
    fare_bad,
    -- surge uplift = how much more people paid per trip in bad weather
    case when fare_good > 0 then (fare_bad - fare_good) / fare_good end as fare_uplift_pct,
    surge_good,
    surge_bad
from pivoted
