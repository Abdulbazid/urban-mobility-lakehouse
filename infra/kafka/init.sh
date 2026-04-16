#!/usr/bin/env sh
# Idempotent Kafka topic bootstrap — called by the `topic-init` service in docker-compose.yml.

set -eu

BOOTSTRAP="${KAFKA_BOOTSTRAP:-kafka:9092}"

create_topic() {
  name=$1
  partitions=$2
  kafka-topics.sh --bootstrap-server "$BOOTSTRAP" \
    --create --if-not-exists \
    --topic "$name" \
    --partitions "$partitions" \
    --replication-factor 1 \
    --config retention.ms=604800000
}

create_topic trips_raw 6
create_topic weather_raw 1

kafka-topics.sh --bootstrap-server "$BOOTSTRAP" --list
