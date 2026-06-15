---
doc:
  title: "AGENTS.md — Agent orientation for RAIP"
  slug: agents-guide
  language: en
  summary: |
    Canonical, high-signal orientation for AI coding agents: what RAIP is, the architecture,
    where things live, how to run it (lite & full), conventions, MVP status, and gotchas.
  type: agent-guide
  audience: [ai-agent, developer]
  navigation:
    index: docs/README.md
    hub: docs/ROADMAP.md
    conventions: docs/CLAUDE.md
    user_guide: USER_GUIDE.md
    status: docs/MVP3_MVP4_IMPLEMENTATION.md
  related_paths: [README.md, docs/README-dev.md, CLAUDE.md]
  tags: [agents, orientation, raip, eu-ai-act]
last_reviewed: "2026-06-15"
---

# AGENTS.md — RAIP

> This agent guide is written in **English** by convention (the agents.md standard). The normative
> specs under `docs/` are in **French** — match that voice when editing them. Code identifiers,
> schemas and tooling stay English everywhere.

## What RAIP is

RAIP (Responsible AI in Practice) is an **open-source, self-hostable EU AI Act compliance
evaluation framework**. It supervises a model across its whole lifecycle (data → pre-train →
fine-tune → inference → production), not as a single end-of-pipeline test. The evaluation backbone
is **COMPL-AI**'s 18 technical requirements — **12 measurable** (R01–R12, each a score in [0,1]) and
**6 non-measurable** (N01–N06, declarative forms or human review). Audiences: compliance/legal,
data scientists, and security teams.

It ships in two modes:

- **Guided (default, no login):** a non-technical user opens the dashboard, launches an evaluation
  on a connected Ollama model, and reads a compliance summary. No Keycloak, minimal services.
- **Enterprise:** Keycloak RBAC with 8 personas, full observability stack. Opt in with
  `RAIP_AUTH_MODE=enterprise`.

## Architecture map

Three-layer Multi-Agent System (do **not** split the three evaluation agents):
Orchestration (Supervisor / **LangGraph**) → Evaluation (3 grouped agents: *Data & Red Teaming*,
*Cyber-Robustesse*, *Éthique & Conformité*) → Telemetry/Storage → Restitution (the dashboard).

Request flow for an evaluation:

```
POST /api/v1/runs ──▶ Redis run record ──▶ Celery task (run_benchmark_job)
        │                                         │
        ▼                                         ▼
  RunCreateRequest                    LangGraph: evaluate ▸ aggregate
                                                  │
                       LiteLLM ──▶ Ollama (target model) + self-hosted judge
                                                  │
                       artifacts ──▶ MinIO or local FS; metrics ──▶ MLflow (optional)
                                                  ▼
                       dashboard read API (/runs, /summary, /series, /health/stack)
```

Stack: FastAPI + Celery + Redis + LangGraph + LiteLLM→Ollama, MLflow, MinIO, Postgres/TimescaleDB,
Keycloak, Next.js 14 dashboard, Docker. See `docs/ROADMAP.md §2.1` for the full table — do not
restate it elsewhere.

## Repo layout / where things live

| Path | What |
|------|------|
| `src/raip/api/main.py` | FastAPI app + run create/get/delete, benchmarks list |
| `src/raip/api/auth.py` | Auth modes (`guided`/`enterprise`), Keycloak JWT, role sets |
| `src/raip/api/dashboard_routes.py` | Read API: `/runs`, `/summary`, `/inspector`, `/series`, `/health/stack`, HITL, drift, kill-switch |
| `src/raip/api/models_routes.py` | Connected Ollama models + persistent model registry |
| `src/raip/api/forms_routes.py` | Declarative forms N03–N06 + signed audit PDF |
| `src/raip/api/lab_routes.py` | MVP2 lab (dataset scan, poisoning, checkpoint eval) |
| `src/raip/tasks/eval.py` | The evaluation Celery job (graph → MLflow → artifacts → Redis) |
| `src/raip/tasks/monitor.py` | On-demand drift/canary check |
| `src/raip/graph/` | LangGraph supervisor (evaluate + aggregate nodes) |
| `src/raip/benchmarks/` | `benchmarks_catalog.yaml`, `catalog.py`, runners (lm_eval, garak, hf_dynamic, …) |
| `src/raip/governance/` | signing, **trust_factor**, **kill_switch**, **pdf_export**, datasheet |
| `src/raip/store/` | Redis stores: `redis_run`, `redis_models`, `redis_hitl` |
| `src/raip/artifacts/` | `s3io` (MinIO) + `local_fs` (lite fallback), backend selector |
| `src/raip/dashboard/` | **Python** triage + score bands (NOT the UI) |
| `dashboard/` | **Next.js** UI (App Router, TanStack Query, Tailwind, Recharts, Playwright) |
| `docs/` | French specs; `ROADMAP.md` is the hub |
| `tests/` | `unit/` (+ Redis), `integration/`, `e2e/`, `lab/` |

> **Name-collision gotcha:** `src/raip/dashboard/` (Python: triage/score logic) is different from
> the top-level `dashboard/` (the Next.js front-end).

Dashboard routes: `/home`, `/launch`, `/runs-overview` (guided console), `/dashboards/{compliance,cyber,ds}`
(RBAC lenses), `/runs/[id]` and `/runs/[id]/inspector`.

## Quickstart

**Lite mode (one command, the guided default):**

```bash
ollama pull llama3.1:8b-instruct-q8_0      # the recommended target model
make quickstart                            # docker compose -f docker-compose.lite.yml up --build
# open http://localhost:3000 — no login
```

Lite mode runs only Redis + API + worker + dashboard; artifacts go to the local filesystem,
MLflow/MinIO/Keycloak are off (the stack-health strip shows them amber, not red).

**Full / enterprise mode:**

```bash
make stack-full                            # docker compose up --build (Keycloak, MLflow, MinIO, Timescale)
# RAIP_AUTH_MODE=enterprise enforces Keycloak RBAC (8 personas, password raip-dev)
```

Native (no Docker): `make quickstart-native` prints the three commands (API, worker, `npm run dev`).
Full dev setup: `docs/README-dev.md`.

## The no-login guided dashboard

The headline UX for non-technical users. `RAIP_AUTH_MODE=guided` (the default) means
`auth_disabled()` returns true and a single persona holds every role, so all lenses render.
Frontend mirrors this via `isGuided()` (default `NEXT_PUBLIC_AUTH_MODE=guided`).

- **`/home`** — "what you can do" cards, connected-model count, kill-switch toggle.
- **`/launch`** — a 4-step wizard: pick a connected Ollama model → recommended/custom requirements →
  options → review → `POST /api/v1/runs`, then it redirects to the live run summary (which polls
  while `queued`/`running`).
- **`/runs-overview`** — summary table of all runs with status, triage counts, headline score.

`NEXT_PUBLIC_*` vars are inlined at **build** time — pass them as Docker build args for enterprise
(see `dashboard/Dockerfile` + `docker-compose.yml`), not just runtime env.

## Common tasks

- **Run an eval (UI):** `/launch` wizard. **(CLI/API):** `POST /api/v1/runs` with a `RunCreateRequest`
  (`src/raip/schemas/run_payload.py`); empty `complai_requirements` ⇒ full measurable set.
- **Add a benchmark:** add to `src/raip/benchmarks/benchmarks_catalog.yaml` + a runner under
  `src/raip/benchmarks/runners/`; map it to one of R01–R12 with an explicit score formula (or an
  N0x HITL rubric). Keep output expressible in the `benchmark_run.yaml` schema. Update
  `docs/MVP2_STATUS.md`.
- **Add a dashboard view:** route under `dashboard/src/app/`, data via `dashboard/src/lib/api.ts`,
  backend route in `dashboard_routes.py`. Honor RBAC via `AuthGuard` unless it is a guided surface.
- **Add an N0x rubric / form:** `src/raip/store/redis_hitl.py` or `schemas/declarative_forms.py`;
  surface in `RunSummaryView`'s MVP3 panel.

## Conventions & constraints (guardrails)

Full doctrine in `docs/CLAUDE.md §4`. The short version:

- **100% OSS / on-prem.** No AWS/GCP/Azure managed services, no SaaS observability/feature-flags,
  no hosted vector DBs / OpenAI embeddings as default. Self-hosted judges only (vLLM + Llama/Mistral/
  Qwen). Single exception: proprietary LLMs as *evaluation targets* via LiteLLM — every default and
  fallback must work self-hosted. Prefer OSS lineage (Swarm > k8s, OpenBao > Vault, MinIO > S3, …).
- **No `pilote_v1` data in compliance views or audit exports** (hard rule). The pilot marker is
  defined in exactly one place: `src/raip/dashboard/triage.py` (`PILOTE_MARKERS`,
  `is_pilote_catalog`). Don't reintroduce the literal elsewhere — `tests/unit/test_no_pilote_v1.py`
  enforces this.
- **18-axis COMPL-AI taxonomy only** — no ad-hoc dimensions. Canonical mapping in `ROADMAP.md §3`.
- **No binary thresholds / "regulatory cliff"** — continuous scores + green/orange/red bands
  (`score_bands.py`), human arbitration over the trade-offs.
- **Sovereign self-hosted judges** for red-teaming/ASR — never proprietary.

## Testing

```bash
make test-unit                       # pytest tests/unit/ (needs Redis on :6379)
pytest tests/integration -m integration   # RAIP_INTEGRATION=1 (Redis + MinIO)
cd dashboard && npx playwright test  # RBAC matrix (25) + guided-mode (5)
ruff check src tests                 # lint
```

Unit tests use a **real Redis** (no mocking). Coverage gate is 80% on `raip`. CI: `.github/workflows/raip-ci.yml` (unit + integration + dashboard/Playwright).

## MVP roadmap status

MVP1 (inference core) and MVP2 (lab) — see `docs/MVP2_STATUS.md`. MVP3 (curves, HITL, forms, signed
PDF, RBAC) and the **thin MVP4 slice** (Trust Factor, on-demand drift, kill-switch) — see the
implemented-vs-deferred matrix in **`docs/MVP3_MVP4_IMPLEMENTATION.md`**. Full MVP4
governance-as-a-service (Kafka/Kong/OPA/Wazuh/async proxy) is deliberately deferred.

## Gotchas

- `src/raip/dashboard/` (Python) ≠ `dashboard/` (Next.js).
- MLflow UI is on host `:5001` but the container listens on `5000`.
- Containers reach Ollama via `host.docker.internal:11434` (`OLLAMA_API_BASE`); native runs use `127.0.0.1`.
- R09 watermark is reported `NA` without a detector and excluded from aggregation.
- Lite mode: MLflow disabled + local artifacts; the worker's MLflow call is guarded, so it won't crash.
- The audit PDF is a **sha256 self-attestation**, not a qualified eIDAS signature (needs a real TSA).

## Keeping this file in sync

When you change a documented surface, update the owning doc and bump its `last_reviewed`. Quick checklist:

- New route / env var? → `docs/README-dev.md` + this file's repo-map/quickstart.
- New benchmark? → `benchmarks_catalog.yaml` + COMPL-AI mapping + `docs/MVP2_STATUS.md`.
- New guided UI? → `USER_GUIDE.md` + the guided-dashboard section above.
- New MVP3/MVP4 capability or deferral? → `docs/MVP3_MVP4_IMPLEMENTATION.md`.
- New dependency/tooling? → verify the OSS/on-prem doctrine (`docs/CLAUDE.md §4`) first.
