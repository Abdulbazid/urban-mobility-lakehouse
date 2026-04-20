"""Bronze → Silver: clean, dedup, type-cast, join trips to hourly weather.

Idempotent: overwrites the target Silver partitions for the processed dates.
"""
from __future__ import annotations
import argparse
import os
from datetime import date, timedelta

from pyspark.sql import SparkSession, functions as F, Window
from delta.tables import DeltaTable


def build_spark() -> SparkSession:
    return (SparkSession.builder
            .appName("silver-clean")
            .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
            .config("spark.sql.catalog.spark_catalog",
                    "org.apache.spark.sql.delta.catalog.DeltaCatalog")
            .config("spark.sql.adaptive.enabled", "true")
            .config("spark.sql.adaptive.skewJoin.enabled", "true")
            .config("spark.hadoop.fs.s3a.endpoint", os.getenv("S3_ENDPOINT"))
            .config("spark.hadoop.fs.s3a.access.key", os.getenv("S3_ACCESS_KEY"))
            .config("spark.hadoop.fs.s3a.secret.key", os.getenv("S3_SECRET_KEY"))
            .config("spark.hadoop.fs.s3a.path.style.access", "true")
            .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
            .getOrCreate())


def main(process_date: str) -> None:
    spark = build_spark()
    spark.sparkContext.setLogLevel("WARN")

    bronze_trips = spark.read.format("delta").load("s3a://bronze/trips/")
    bronze_wx    = spark.read.format("delta").load("s3a://bronze/weather/")

    # ---------- clean trips ----------
    trips = (bronze_trips
             .withColumn("pickup_ts", F.to_timestamp("pickup_datetime"))
             .withColumn("pickup_date", F.to_date("pickup_ts"))
             .withColumn("pickup_hour", F.date_trunc("hour", "pickup_ts"))
             # drop obvious garbage
             .filter(F.col("fare_amount") > 0)
             .filter(F.col("passenger_count").between(1, 6))
             .filter(F.col("trip_distance") > 0)
             # dedup by trip_id, keep latest ingestion
             .withColumn("rn", F.row_number().over(
                 Window.partitionBy("trip_id").orderBy(F.col("ingestion_ts").desc())))
             .filter(F.col("rn") == 1).drop("rn")
             .filter(F.col("pickup_date") == F.to_date(F.lit(process_date))))

    # ---------- clean weather ----------
    weather = (bronze_wx
               .withColumn("obs_ts", F.to_timestamp("observation_time"))
               .withColumn("obs_hour", F.date_trunc("hour", "obs_ts"))
               .withColumn("obs_date", F.to_date("obs_ts"))
               .withColumn("rn", F.row_number().over(
                   Window.partitionBy("obs_hour").orderBy(F.col("ingested_at").desc())))
               .filter(F.col("rn") == 1).drop("rn")
               .select("obs_hour", "temperature_c", "precipitation_mm",
                       "wind_speed_kmh", "weather_code"))

    # ---------- join trips ↔ weather on hour ----------
    silver = (trips.join(F.broadcast(weather),
                         trips.pickup_hour == weather.obs_hour, "left")
                   .drop("obs_hour"))

    # Derived flag — easy to reason about in gold aggregates
    silver = silver.withColumn(
        "is_bad_weather",
        (F.col("precipitation_mm") >= 1.0) | (F.col("wind_speed_kmh") >= 30))

    print(f"▶ silver rows for {process_date}: {silver.count():,}")

    # ---------- idempotent write via Delta MERGE / partition overwrite ----------
    out = "s3a://silver/trips/"
    if DeltaTable.isDeltaTable(spark, out):
        (silver.write
               .format("delta")
               .mode("overwrite")
               .option("replaceWhere", f"pickup_date = '{process_date}'")
               .partitionBy("pickup_date")
               .save(out))
    else:
        (silver.write.format("delta").mode("overwrite")
               .partitionBy("pickup_date").save(out))

    print(f"✅ wrote silver for {process_date}")
    spark.stop()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=None, help="YYYY-MM-DD (default: today UTC)")
    args = ap.parse_args()
    d = args.date or date.today().isoformat()
    main(d)
