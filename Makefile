# RAIP — convenience targets. `make help` lists them.
.DEFAULT_GOAL := help
.PHONY: help quickstart quickstart-down stack-full stack-down quickstart-native stack-gaas stack-gaas-down test test-unit lint

OLLAMA_MODEL ?= llama3.1:8b-instruct-q8_0

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

quickstart: ## Lite stack (no login, no MinIO/MLflow/Keycloak) — open http://localhost:3000
	@command -v ollama >/dev/null 2>&1 && ollama pull $(OLLAMA_MODEL) || \
		echo "NOTE: install Ollama and run 'ollama pull $(OLLAMA_MODEL)' for evaluations to work."
	docker compose -f docker-compose.lite.yml up --build

quickstart-down: ## Stop and remove the lite stack
	docker compose -f docker-compose.lite.yml down

quickstart-native: ## Run API + worker + dashboard locally (no Docker), guided mode
	@echo "Run each of these in a separate terminal (Redis + Ollama must be running):"
	@echo "  1) RAIP_AUTH_MODE=guided RAIP_ARTIFACT_BACKEND=local RAIP_MLFLOW_DISABLED=1 \\"
	@echo "       uvicorn raip.api.main:app --port 8000"
	@echo "  2) RAIP_ARTIFACT_BACKEND=local RAIP_MLFLOW_DISABLED=1 \\"
	@echo "       celery -A raip.celery_app worker --loglevel=INFO"
	@echo "  3) cd dashboard && NEXT_PUBLIC_AUTH_MODE=guided npm run dev"

stack-full: ## Full enterprise stack (Keycloak RBAC, MinIO, MLflow, TimescaleDB)
	docker compose up --build

stack-down: ## Stop and remove the full stack
	docker compose down

stack-gaas: ## Full stack + Governance-as-a-Service runtime (proxy:8100, OPA, Redpanda, OpenSearch)
	docker compose -f docker-compose.yml -f docker-compose.gaas.yml up --build

stack-gaas-down: ## Stop and remove the gaas stack
	docker compose -f docker-compose.yml -f docker-compose.gaas.yml down

test: test-unit ## Run the unit test suite

test-unit: ## Run backend unit tests
	pytest tests/unit/ -q

lint: ## Ruff lint the backend
	ruff check src tests
