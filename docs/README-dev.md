---
doc:
  title: "RAIP MVP1 — Developer setup"
  slug: readme-dev
  language: en
  summary: |
    Prerequisites, Docker Compose, local Celery/API, tests (pytest), Ollama wiring from containers.
  type: dev-guide
  audience: [developer, ai-agent]
  navigation:
    hub: ./README.md
    spec: ./MVP1_noyau_statique.md
  related_paths:
    - ./CLAUDE.md
    - ../README.md
  tags: [dev, docker, pytest, ollama, celery]
last_reviewed: "2026-05-12"
---

# RAIP MVP1 — developer setup

## Prerequisites

- **Python 3.11.x** (required for MLflow/pyarrow wheels; see `.python-version`)
- [Ollama](https://ollama.com) running on the host with the target model pulled (example: `ministral-3:3b`). Check names with `ollama list`; set `RAIP_TARGET_MODEL` to `ollama/<name>` accordingly.
- Docker (optional but recommended for Redis, MinIO, MLflow, Celery worker, API).

Ollama model files live under `~/.ollama/models` on macOS; RAIP talks to the **Ollama HTTP API** (`OLLAMA_API_BASE`), not to that directory.

## Local Python (API + worker without Docker)

```bash
cd /path/to/RAIP
python -m venv .venv
source .venv/bin/activate
pip install -e .

# Terminal 1 — Redis (or use Docker only for Redis)
docker run -d --name raip-redis -p 6379:6379 redis:7-alpine

# Start MLflow + Postgres + MinIO via compose (partial), or point MLFLOW_TRACKING_URI to a local mlflow instance.

# Terminal 2 — Celery worker
celery -A raip.celery_app worker --loglevel=INFO

# Terminal 3 — API
uvicorn raip.api.main:app --reload --host 127.0.0.1 --port 8000
```

## Full stack with Docker Compose

1. Start Ollama on the host (`ollama serve`) and ensure the model tag matches `RAIP_TARGET_MODEL` in `docker-compose.yml`.
2. From the repo root:

```bash
docker compose up --build
```

3. Submit a run:

```bash
export RAIP_API_URL=http://127.0.0.1:8000
raip-eval run configs/example.run.yaml
```

Containers reach Ollama via `http://host.docker.internal:11434` (`OLLAMA_API_BASE`).

## Endpoints

- API docs: `http://127.0.0.1:8000/docs`
- MLflow UI: `http://127.0.0.1:5000`
- MinIO console: `http://127.0.0.1:9001` (user/password `minioadmin`)

## Environment

Copy [.env.example](.env.example) to `.env` and adjust. Docker Compose sets equivalent variables inline for `api` and `worker`.

## Tests

From the repo root, with dev dependencies:

```bash
pip install -e ".[dev]"
PYTHONPATH=src pytest tests/ -q
```

Coverage (seuil 80 % sur le package `raip`, voir `pyproject.toml`) :

```bash
PYTHONPATH=src pytest tests/ -q --cov=raip --cov-fail-under=80
```

With a venv where `raip` is already installed editable, `tests/conftest.py` adds `src/` to `sys.path`, so you can run:

```bash
pytest tests/ -q
```

Optional live Ollama check (skipped unless enabled):

```bash
RAIP_RUN_OLLAMA_SMOKE=1 pytest tests/test_external_ollama_optional.py -q
```

### E2E self-hosted (Redis + MinIO + MLflow + Ollama)

On a **self-hosted runner** where the stack is up and Ollama serves `RAIP_TARGET_MODEL` :

```bash
export RAIP_E2E_OLLAMA=1
# optional: réduire le coût CI
export RAIP_BOOTSTRAP_N=200
export RAIP_E2E_TIMEOUT_SEC=900
PYTHONPATH=src pytest tests/e2e/ -m e2e -q
```

The E2E test posts the payload in [`examples/mvp1_pilote_e2e.yaml`](../examples/mvp1_pilote_e2e.yaml), polls Redis until the run completes, checks MLflow metrics (`complai_*` + CI), MinIO keys under `runs/{run_id}/`, and parses `benchmark_run.yaml` for bootstrap CIs (MVP1 §4.3). Celery runs **in-process** via `task_always_eager` for that test module.

### Air-gap / egress deny (section 9 MVP1)

A full **air-gap** proof (worker + Redis + MinIO + MLflow without Internet) is environment-specific: use a CI job or VM whose **egress is denied**, with images and models preloaded. The evaluation path itself uses **LiteLLM → Ollama** on `OLLAMA_API_BASE` only; proprietary cloud keys are not part of `Settings`. Pulling container images or Ollama weights requires network **before** the air-gap run.

Run a single file with the stdlib runner (uses the `PROJECT_ROOT` / `sys.path` block in each file):

```bash
PYTHONPATH=src python -m unittest tests.test_config_settings -v
```

## Limitations (pilote_v1)

- **pilote_v1** maps MVP1 benchmark IDs to a **small in-repo JSONL** corpus and scores via Ollama; Garak / full `lm-evaluation-harness` / full MMLU are **not** wired yet.
- **R09** uses a deterministic `0.0` placeholder when no watermark detector is configured (documented in `raw_outputs`).
- A small local model is **not** a substitute for the self-hosted judge sizes described in [MVP1_noyau_statique.md](MVP1_noyau_statique.md).
