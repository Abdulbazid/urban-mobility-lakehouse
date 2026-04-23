# Data Model — Gold layer

## Star schema overview

```
                 dim_zones
          ┌────────────────────┐
          │ zone_id   (PK)     │
          │ zone_name          │
          │ borough            │
          └──────────┬─────────┘
                     │
                     │ pickup_zone_id
                     │ dropoff_zone_id
                     ▼
          ┌────────────────────────────────────┐
          │            fct_trips                │
          │ ─────────────────────────────────  │
          │ trip_id           (PK, degenerate)  │
          │ pickup_zone_id    (FK → dim_zones)  │
          │ dropoff_zone_id   (FK → dim_zones)  │
          │ pickup_ts, pickup_date, pickup_hour │
          │ daypart           (morning_rush…)   │
          │ ─── measures ─────────────────────  │
          │ passenger_count, trip_distance      │
          │ trip_duration_min                   │
          │ fare_amount, tip_amount, tolls,     │
          │ total_amount, tip_rate,             │
          │ surge_multiplier, revenue_per_mile  │
          │ ─── weather context ──────────────  │
          │ temperature_c, precipitation_mm,    │
          │ wind_speed_kmh, is_bad_weather      │
          └────────────────────────────────────┘
                           │
                           │ aggregated
                           ▼
                 surge_metrics
          (grain: borough × zone × hour)
```

## Grains

| Table | Grain | Example |
|---|---|---|
| `fct_trips` | one trip | 60k rows/minute at peak |
| `dim_zones` | one TLC zone | ~260 rows (stable) |
| `surge_metrics` | borough × zone × hour | ~60k rows/day |

## Why a degenerate key instead of surrogate

`trip_id` is a UUID we receive from source. It's already unique. No need to generate a new surrogate key for this fact — degenerate is fine and easier to debug.

## Slowly changing dimensions

`dim_zones` today is derived from trips (SCD type 1 implicitly). In the real project, replace this with a seed from the TLC zone lookup CSV and snapshot with dbt's `check` strategy for SCD2 — see [ADR roadmap](decisions/).

## Time dimensions

We're not using a separate `dim_date` / `dim_time` because:
- DuckDB's date functions are adequate for BI queries.
- Adding one is trivial if a BI tool demands it.

## Weather as context, not a dim

`temperature_c`, `precipitation_mm`, etc. are **embedded in the fact** rather than being a `dim_weather` table. Rationale:
- Cardinality is near 1:1 with fact hours — a dim wouldn't save much storage.
- Dashboards filter on weather attributes constantly; keeping them in the fact avoids a join.

An alternative is to make `dim_weather` keyed by `(borough, hour)` — worth doing if weather fields grow.

## Surge metrics pivot

`surge_metrics.fare_uplift_pct` is the **headline business metric**:

```
fare_uplift_pct = (fare_bad - fare_good) / fare_good
```

Interpretation: how much more does a trip cost in bad weather vs good, for the same zone+hour of day. Feed this to the dashboard.

## Known weaknesses

- No real `dim_payment_type` — we use the raw integer code from TLC.
- No holiday / event dimension — could correlate with events like Times Square NYE.
- Weather granularity is hourly; borough-level lat/lon would be more precise.
