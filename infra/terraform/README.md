# Terraform (Week 3 extension)

Optional stretch goal — deploy the same stack to AWS.

## Minimum viable plan

| Local | AWS equivalent |
|---|---|
| MinIO | S3 (3 buckets: bronze/silver/gold) |
| Kafka (KRaft) | MSK Serverless |
| Spark | EMR Serverless or Glue |
| Airflow | MWAA (managed) |
| DuckDB + dbt | Athena + dbt-athena, or keep DuckDB on Fargate |
| Metabase | ECS Fargate + RDS Postgres |

## Starter `main.tf`

See `main.tf.example` (not provided here to keep the repo cloud-neutral). The provisioning plan is:

1. `aws_s3_bucket` × 3 with versioning + server-side encryption.
2. `aws_msk_serverless_cluster` with IAM SASL auth.
3. `aws_iam_role` for MWAA with `s3:*` scoped to the three buckets.
4. `aws_mwaa_environment` pointing at an `s3://.../dags/` key.
5. A GitHub Actions workflow that `terraform plan`s on PR and `apply`s on merge.

Estimated monthly cost at low volume: ~$80 (mostly MWAA + MSK baseline).

## Why not done in the local project

The local stack is intentionally laptop-runnable. Moving to AWS multiplies cost and reviewer setup friction, so we keep it as a roadmap item demonstrated via this README + a screenshot of `terraform plan` output once implemented.
