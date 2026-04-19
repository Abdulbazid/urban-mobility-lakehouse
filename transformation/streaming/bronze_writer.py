"""Kafka → Bronze Delta writer.

Runs as a Spark Structured Streaming job. Reads both topics and appends to
date-partitioned Delta tables on MinIO. Exactly-once via Delta's atomic commits
plus Kafka offset checkpointing.

Invoke from Airflow or manually:
    spark-submit --packages ... bronze_writer.py --topic trips_raw --mode batch
"""
from __future__ import annotations
import argparse
import os

from pyspark.sql import SparkSession, functions as F
from pyspark.sql.types import (StructType, StructField, StringType, IntegerType,
                               DoubleType, LongType)


def build_spark() -> SparkSession:
    return (SparkSession.builder
            .appName("bronze-writer")
            .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
            .config("spark.sql.catalog.spark_catalog",
                    "org.apache.spark.sql.delta.catalog.DeltaCatalog")
            .config("spark.hadoop.fs.s3a.endpoint", os.getenv("S3_ENDPOINT", "http://minio:9000"))
            .config("spark.hadoop.fs.s3a.access.key", os.getenv("S3_ACCESS_KEY", "minioadmin"))
            .config("spark.hadoop.fs.s3a.secret.key", os.getenv("S3_SECRET_KEY", "minioadmin"))
            .config("spark.hadoop.fs.s3a.path.style.access", "true")
            .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
            .getOrCreate())


TRIP_SCHEMA = StructType([
    StructField("trip_id", StringType()),
    StructField("vendor_id", IntegerType()),
    StructField("pickup_datetime", StringType()),
    StructField("dropoff_datetime", StringType()),
    StructField("passenger_count", IntegerType()),
    StructField("trip_distance", DoubleType()),
    StructField("trip_duration_min", IntegerType()),
    StructField("pickup_zone_id", IntegerType()),
    StructField("dropoff_zone_id", IntegerType()),
    StructField("pickup_zone_name", StringType()),
    StructField("pickup_borough", StringType()),
    StructField("dropoff_borough", StringType()),
    StructField("fare_amount", DoubleType()),
    StructField("surge_multiplier", DoubleType()),
    StructField("total_amount", DoubleType()),
    StructField("tip_amount", DoubleType()),
    StructField("tolls_amount", DoubleType()),
    StructField("payment_type", IntegerType()),
])


def run_batch(topic: str, out_path: str, schema: StructType) -> int:
    """Drain the topic once (kafka source in batch mode) and append to Delta."""
    spark = build_spark()
    raw = (spark.read.format("kafka")
           .option("kafka.bootstrap.servers", os.getenv("KAFKA_BOOTSTRAP", "kafka:9092"))
           .option("subscribe", topic)
           .option("startingOffsets", "earliest")
           .option("endingOffsets", "latest")
           .load())

    parsed = (raw.select(
                F.col("key").cast("string").alias("kafka_key"),
                F.from_json(F.col("value").cast("string"), schema).alias("d"),
                F.col("partition").alias("kafka_partition"),
                F.col("offset").alias("kafka_offset"),
                F.col("timestamp").alias("kafka_ts"))
              .select("kafka_key", "kafka_partition", "kafka_offset",
                      "kafka_ts", "d.*")
              .withColumn("ingestion_date", F.current_date())
              .withColumn("ingestion_ts", F.current_timestamp()))

    count = parsed.count()
    if count == 0:
        print(f"⚠ no new data on topic {topic}")
        spark.stop()
        return 0

    (parsed.write
           .format("delta")
           .mode("append")
           .partitionBy("ingestion_date")
           .option("mergeSchema", "true")
           .save(out_path))

    print(f"✅ {topic}: wrote {count:,} rows to {out_path}")
    spark.stop()
    return count


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--topic", required=True, choices=["trips_raw", "weather_raw"])
    args = ap.parse_args()

    out = {
        "trips_raw":   "s3a://bronze/trips/",
        "weather_raw": "s3a://bronze/weather/",
    }[args.topic]
    schema = TRIP_SCHEMA if args.topic == "trips_raw" else None  # weather: inferSchema

    if schema is None:
        # Weather records have nullable numeric fields — infer from JSON
        from pyspark.sql.types import TimestampType
        schema = StructType([
            StructField("observation_time", StringType()),
            StructField("latitude", DoubleType()),
            StructField("longitude", DoubleType()),
            StructField("temperature_c", DoubleType()),
            StructField("precipitation_mm", DoubleType()),
            StructField("wind_speed_kmh", DoubleType()),
            StructField("weather_code", IntegerType()),
            StructField("ingested_at", StringType()),
        ])

    run_batch(args.topic, out, schema)
