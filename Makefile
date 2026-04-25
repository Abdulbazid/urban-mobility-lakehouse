.PHONY: help setup run down seed dbt test clean logs

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-12s\033[0m %s\n", $$1, $$2}'

setup:  ## Pull images, create buckets + topics (one-time)
	docker compose pull
	docker compose up -d minio createbuckets kafka
	@echo "Waiting 15s for Kafka to be healthy..."
	@sleep 15
	docker compose run --rm topic-init
	@echo "✅ Setup complete. Run 'make run' next."

run:  ## Bring up the full stack
	docker compose up -d
	@echo "✅ Stack running. UIs:"
	@echo "   MinIO     → http://localhost:9001"
	@echo "   Kafka UI  → http://localhost:8080"
	@echo "   Airflow   → http://localhost:8088 (admin/admin)"
	@echo "   Metabase  → http://localhost:3000"

seed:  ## Stream simulated trips into Kafka for 2 minutes
	docker compose run --rm producer python /app/trip_producer.py --duration 120

dbt:  ## Build Silver + Gold and run tests
	docker compose run --rm dbt dbt deps
	docker compose run --rm dbt dbt run
	docker compose run --rm dbt dbt test

test:  ## Run pytest for producer / transforms
	docker compose run --rm producer pytest -v

docs:  ## Serve dbt docs at :8081
	docker compose run --rm -p 8081:8081 dbt dbt docs generate
	docker compose run --rm -p 8081:8081 dbt dbt docs serve --host 0.0.0.0 --port 8081

down:  ## Stop everything (keeps volumes)
	docker compose down

clean:  ## Stop + wipe all volumes (full reset)
	docker compose down -v
	rm -rf dbt/target dbt/dbt_packages dbt/logs

logs:  ## Tail all service logs
	docker compose logs -f --tail 50
