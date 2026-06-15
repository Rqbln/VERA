---
doc:
  title: "RAIP — Developer setup (MVP2–MVP4)"
  slug: readme-dev
  language: en
  summary: |
    Quickstart (lite/guided + full), prerequisites, Docker Compose, local Celery/API, tests
    (pytest + Playwright), Ollama wiring, the no-login guided dashboard and launch wizard.
  type: dev-guide
  audience: [developer, ai-agent]
  navigation:
    hub: ./README.md
    spec: ./MVP1_noyau_statique.md
    agents: ../AGENTS.md
    status: ./MVP3_MVP4_IMPLEMENTATION.md
  related_paths:
    - ./CLAUDE.md
    - ../README.md
    - ../AGENTS.md
  tags: [dev, docker, pytest, ollama, celery, guided, lite]
last_reviewed: "2026-06-15"
---

# RAIP — developer setup (MVP2–MVP4)

## Lite mode / one-command quickstart (no login)

For a non-technical demo or fast local dev, the **guided** stack runs with a single command and
**no Keycloak**: Redis + API + worker + dashboard only, artifacts on the local filesystem, MLflow
off.

```bash
ollama pull llama3.1:8b-instruct-q8_0
make quickstart                 # = docker compose -f docker-compose.lite.yml up --build
# open http://localhost:3000 — no login; redirected to /home
```

Native equivalent (no Docker): `make quickstart-native` prints the three commands. Key env:
`RAIP_AUTH_MODE=guided`, `RAIP_ARTIFACT_BACKEND=local`, `RAIP_MLFLOW_DISABLED=1`.

The guided dashboard adds three routes on top of the RBAC lenses:

- `/home` — onboarding ("what you can do") + connected models + kill-switch.
- `/launch` — the Ollama **launch wizard** (model → requirements → options → submit `POST /api/v1/runs`).
- `/runs-overview` — summary table of runs (status, triage counts, headline score).

End-user walkthrough: [USER_GUIDE.md](../USER_GUIDE.md). Implementation status:
[MVP3_MVP4_IMPLEMENTATION.md](./MVP3_MVP4_IMPLEMENTATION.md).

## Prerequisites

- **Python 3.11.x** (required for MLflow/pyarrow wheels; see `.python-version`)
- [Ollama](https://ollama.com) on the host with **`llama3.1:8b-instruct-q8_0`** pulled:

```bash
ollama pull llama3.1:8b-instruct-q8_0
export RAIP_TARGET_MODEL=ollama/llama3.1:8b-instruct-q8_0
```

Optional harness extras: `pip install -e ".[dev,benchmarks]"` (lm-eval, Garak, datasets).
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
raip-eval run examples/mvp2_ollama_e2e.yaml
```

Containers reach Ollama via `http://host.docker.internal:11434` (`OLLAMA_API_BASE`).

## Endpoints

- API docs: `http://127.0.0.1:8000/docs`
- **MVP3 dashboard**: `http://127.0.0.1:3000` (compliance control room)
- Keycloak: `http://127.0.0.1:8080` (admin / admin; realm `raip`)
- MLflow UI: `http://127.0.0.1:5001` (port hôte ; le conteneur écoute toujours sur 5000 en interne)
- MinIO console: `http://127.0.0.1:9001` (user/password `minioadmin`)

### MVP3 dashboard (local)

```bash
# Terminal A — API with auth disabled for quick UI dev
export RAIP_AUTH_DISABLED=1
uvicorn raip.api.main:app --reload --port 8000

# Terminal B — Next.js (see dashboard/.env.example)
cd dashboard
cp .env.example .env.local
# set NEXT_PUBLIC_AUTH_DISABLED=1
npm run dev
```

Docker (Keycloak + RBAC):

```bash
docker compose up --build api keycloak dashboard redis minio
```

Test personas (password `raip-dev`): `compliance@raip.local`, `ds@raip.local`, `secops@raip.local`, etc. — see `infra/keycloak/raip-realm.json`.

Playwright suites — RBAC matrix (3 views × 8 personas) **+ guided-mode** (home, launch, runs-overview):

```bash
cd dashboard
npm run build
npx playwright test            # control-room.spec.ts (25) + guided-mode.spec.ts (5)
```

UX spec: [MVP3_UX_CONTROL_ROOM.md](./MVP3_UX_CONTROL_ROOM.md). Guided UX: [USER_GUIDE.md](../USER_GUIDE.md).

## Environment

Copy [.env.example](.env.example) to `.env` and adjust. Docker Compose sets equivalent variables inline for `api` and `worker`.

## Tests (pyramide — zéro `unittest.mock`)

| Tier | Flag | Command |
|------|------|---------|
| **Unit** | — | `pytest tests/unit/ tests/test_*.py -q` |
| **Integration** | `RAIP_INTEGRATION=1` | `pytest tests/integration/ -m integration -q` |
| **E2E** | `RAIP_E2E_OLLAMA=1` | `pytest tests/e2e/ -m "e2e and ollama" -q` |

From the repo root (Python 3.11 venv):

```bash
pip install -e ".[dev]"
PYTHONPATH=src pytest tests/unit/ -q
```

Coverage (80 % on `raip`, see `pyproject.toml`):

```bash
PYTHONPATH=src pytest tests/unit/ tests/test_bootstrap.py tests/test_benchmark_run_builder.py -q --cov=raip --cov-fail-under=80
```

### Integration (Redis + MinIO)

```bash
docker compose up -d redis minio
export RAIP_INTEGRATION=1
PYTHONPATH=src pytest tests/integration/ -m integration -q
```

### E2E (Redis + MinIO + MLflow + Ollama)

```bash
ollama pull llama3.1:8b-instruct-q8_0
docker compose up -d --build
export RAIP_E2E_OLLAMA=1
export RAIP_BOOTSTRAP_N=200
export RAIP_E2E_TIMEOUT_SEC=900
PYTHONPATH=src pytest tests/e2e/ -m "e2e and ollama" -q
```

E2E uses [`examples/mvp2_ollama_e2e.yaml`](../examples/mvp2_ollama_e2e.yaml), real LangGraph + LiteLLM → Ollama, `catalog_version: mvp2-v1`. See [MIGRATION_MVP1_MVP2.md](./MIGRATION_MVP1_MVP2.md).

Optional Ollama HTTP smoke:

```bash
RAIP_RUN_OLLAMA_SMOKE=1 pytest tests/test_external_ollama_optional.py -q
```

### Air-gap / egress deny (section 9 MVP1)

A full **air-gap** proof (worker + Redis + MinIO + MLflow without Internet) is environment-specific: use a CI job or VM whose **egress is denied**, with images and models preloaded. The evaluation path itself uses **LiteLLM → Ollama** on `OLLAMA_API_BASE` only; proprietary cloud keys are not part of `Settings`. Pulling container images or Ollama weights requires network **before** the air-gap run.

Run a single file with the stdlib runner (uses the `PROJECT_ROOT` / `sys.path` block in each file):

```bash
PYTHONPATH=src python -m unittest tests.test_config_settings -v
```

## MVP2 notes

- **pilote_v1** removed; benchmarks are dynamic (see [MIGRATION_MVP1_MVP2.md](./MIGRATION_MVP1_MVP2.md)).
- **R09** watermark: explicit `NA` in `raw_outputs` when no detector is configured (excluded from aggregation).
- Install `[benchmarks]` for full lm-eval / Garak; otherwise runners fall back to `hf_dynamic` probes.
- Default **Llama 3.1 8B Q8** is a dev default; production judge targets remain documented in [MVP1_noyau_statique.md](MVP1_noyau_statique.md).
