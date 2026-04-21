{{ config(materialized='view') }}

with base as (
    select * from {{ ref('stg_trips') }}
)
select
    *,
    -- revenue per mile — useful for surge analysis
    case when trip_distance > 0 then total_amount / trip_distance end as revenue_per_mile,
    -- tip rate
    case when fare_amount > 0 then tip_amount / fare_amount end as tip_rate,
    -- time-of-day bucket
    case
        when hour(pickup_ts) between 6  and 9  then 'morning_rush'
        when hour(pickup_ts) between 10 and 15 then 'midday'
        when hour(pickup_ts) between 16 and 19 then 'evening_rush'
        when hour(pickup_ts) between 20 and 23 then 'night'
        else 'late_night'
    end as daypart
from base
