{{ config(materialized='table') }}

-- Distinct zones observed in the fact. In a real project, this is the TLC lookup CSV as a seed.
select distinct
    pickup_zone_id   as zone_id,
    pickup_zone_name as zone_name,
    pickup_borough   as borough
from {{ ref('stg_trips') }}
where pickup_zone_id is not null
