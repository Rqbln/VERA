# VERA — convenience targets. `make help` lists them.
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
	@echo "  1) VERA_AUTH_MODE=guided VERA_ARTIFACT_BACKEND=local VERA_MLFLOW_DISABLED=1 \\"
	@echo "       uvicorn vera.api.main:app --port 8000"
	@echo "  2) VERA_ARTIFACT_BACKEND=local VERA_MLFLOW_DISABLED=1 \\"
	@echo "       celery -A vera.celery_app worker --loglevel=INFO"
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

study-tunnel: ## Expose the dashboard (and the study at /study) via an ephemeral cloudflared tunnel
	@echo "Share the printed URL with participants as https://<host>/study"
	cloudflared tunnel --url http://localhost:3000

study-export: ## Export study responses to data/user_study/sessions.csv and print the RQ1 numbers
	curl -fsS http://localhost:8000/api/v1/study/export.csv -o data/user_study/sessions.csv
	python scripts/analyze_user_study.py data/user_study/sessions.csv
