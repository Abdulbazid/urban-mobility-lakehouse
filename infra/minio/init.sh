#!/usr/bin/env sh
# Idempotent MinIO bucket bootstrap — called by the `createbuckets` service in docker-compose.yml.
# Safe to re-run: `mc mb --ignore-existing` is a no-op when the bucket exists.

set -eu

mc alias set local http://minio:9000 "${S3_ACCESS_KEY:-minioadmin}" "${S3_SECRET_KEY:-minioadmin}"

for bucket in bronze silver gold; do
  mc mb --ignore-existing "local/${bucket}"
  mc anonymous set download "local/${bucket}" >/dev/null || true
done

echo "MinIO buckets ready: bronze, silver, gold"
