---
doc:
  title: "AGENTS.md — Agent orientation for VERA"
  slug: agents-guide
  language: en
  summary: |
    Canonical, high-signal orientation for AI coding agents: what VERA is, the architecture,
    where things live, how to run it (lite & full), conventions, MVP status, and gotchas.
  type: agent-guide
  audience: [ai-agent, developer]
  navigation:
    index: docs/README.md
    architecture: docs/ARCHITECTURE.md
    user_guide: USER_GUIDE.md
    dev_setup: docs/README-dev.md
  related_paths: [README.md, docs/EVALUATION_GUIDE.md]
  tags: [agents, orientation, vera, eu-ai-act]
last_reviewed: "2026-07-03"
---

# AGENTS.md — VERA

> This repository is **English throughout** (docs, code identifiers, schemas, tooling). The
> architecture reference is [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

## What VERA is

VERA (Verifiable Evaluation for Responsible AI) is an **open-source, self-hostable EU AI Act compliance
evaluation framework**. It supervises a model across its whole lifecycle (data → pre-train →
fine-tune → inference → production), not as a single end-of-pipeline test. The evaluation backbone
is **COMPL-AI**'s 18 technical requirements — **12 measurable** (R01–R12, each a score in [0,1]) and
**6 non-measurable** (N01–N06, declarative forms or human review). Audiences: compliance/legal,
data scientists, and security teams.

It ships in two modes:

- **Guided (default, no login):** a non-technical user opens the dashboard, launches an evaluation
  on a connected Ollama model, and reads a compliance summary. No Keycloak, minimal services.
- **Enterprise:** Keycloak RBAC with 8 personas, full observability stack. Opt in with
  `VERA_AUTH_MODE=enterprise`.

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
Keycloak, Next.js 14 dashboard, Docker. See `docs/ARCHITECTURE.md §2` for the full table — do not
restate it elsewhere.

## Repo layout / where things live

| Path | What |
|------|------|
| `src/vera/api/main.py` | FastAPI app + run create/get/delete, benchmarks list |
| `src/vera/api/auth.py` | Auth modes (`guided`/`enterprise`), Keycloak JWT, role sets |
| `src/vera/api/dashboard_routes.py` | Read API: `/runs`, `/summary`, `/inspector`, `/series`, `/health/stack`, HITL, drift, kill-switch |
| `src/vera/api/models_routes.py` | Connected Ollama models + persistent model registry |
| `src/vera/api/forms_routes.py` | Declarative forms N03–N06 + signed audit PDF |
| `src/vera/api/lab_routes.py` | MVP2 lab (dataset scan, poisoning, checkpoint eval) |
| `src/vera/tasks/eval.py` | The evaluation Celery job (graph → MLflow → artifacts → Redis) |
| `src/vera/tasks/monitor.py` | On-demand drift/canary check |
| `src/vera/graph/` | LangGraph supervisor (evaluate + aggregate nodes) |
| `src/vera/benchmarks/` | `benchmarks_catalog.yaml`, `catalog.py`, runners (lm_eval, garak, hf_dynamic, …) |
| `src/vera/governance/` | signing, **trust_factor**, **kill_switch**, **pdf_export**, datasheet, **energy** (CodeCarbon → N03) |
| `src/vera/store/` | Redis stores: `redis_run` (carries `energy`), `redis_models`, `redis_hitl` (multi-criteria rubric), `redis_forms` |
| `scripts/` | `setup_native.sh`, `gen_banking_corpus.py`, `run_paper_eval.py` (multi-model), `bench_gaas.py`; `manuscript/scripts/gen_paper_multi.py` |
| `src/vera/artifacts/` | `s3io` (MinIO) + `local_fs` (lite fallback), backend selector |
| `src/vera/dashboard/` | **Python** triage + score bands (NOT the UI) |
| `dashboard/` | **Next.js** UI (App Router, TanStack Query, Tailwind, Recharts, Playwright) |
| `docs/` | French specs; `ROADMAP.md` is the hub |
| `tests/` | `unit/` (+ Redis), `integration/`, `e2e/`, `lab/` |

> **Name-collision gotcha:** `src/vera/dashboard/` (Python: triage/score logic) is different from
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
# VERA_AUTH_MODE=enterprise enforces Keycloak RBAC (8 personas, password vera-dev)
```

**Governance-as-a-Service (MVP4 gaas profile):**

```bash
make stack-gaas                            # full stack + inline proxy (:8100), Redpanda, OPA, OpenSearch,
                                           # scoring agents, audit sink; the lite stack stays unaffected
```

The gaas runtime governs live inference (proxy → event bus → 4 agents → streaming Trust Factor →
OPA → kill-switch → signed audit/SIEM → canary) and degrades gracefully (bus→Redis Streams,
OpenSearch→signed JSONL, OPA→in-process rule). Code in `src/vera/governance/` + `services/`; admin
API `/admin/v1/*`; UI at `/governance`. Full guide: `docs/ARCHITECTURE.md §5`.

Native (no Docker): `make quickstart-native` prints the three commands (API, worker, `npm run dev`).
Full dev setup: `docs/README-dev.md`. Dashboard design system + i18n: `dashboard/DESIGN_SYSTEM.md`.

## Native evaluation & paper reproduction

To run the **real** benchmark engines (not dynamic-probe fallbacks) and reproduce the paper numbers:

```bash
bash scripts/setup_native.sh              # installs .[benchmarks,lab,pdf] + checks Ollama/panel models
VERA_REQUIRE_NATIVE=1 python scripts/run_paper_eval.py   # multi-model panel, sequential
python scripts/bench_gaas.py              # proxy overhead + agent detection + degradation
python manuscript/scripts/gen_paper_multi.py             # tables + figures from the results JSON
```

Key flags (also in `.env.example`): **`VERA_REQUIRE_NATIVE=1`** makes a run *fail* if a
native-harness benchmark silently falls back (allow exceptions via `VERA_NATIVE_ALLOW=garak`);
`VERA_HF_TRUST_REMOTE_CODE=true` for BBQ/BOLD/StereoSet; `VERA_EVAL_MODELS` / `VERA_EVAL_N` for the
panel. **Serving caveat:** Ollama has no token log-probs, so R06/R10 use dynamic probes and native
lm-eval is reserved for a vLLM backend (recorded in provenance) — see `lm_eval_runner.py`.

- **R03–R05** run natively over the synthetic banking corpus `data/corpus/banking_synth.jsonl`
  (regen: `scripts/gen_banking_corpus.py`; 100% synthetic, planted PII / near-dupes / imbalance).
- **N03 energy** is measured automatically (CodeCarbon in `governance/energy.py`, wired in
  `tasks/eval.py`) and auto-fills the N03 form; **N01/N02** use a multi-criteria HITL rubric
  (`/hitl/rubrics`); the run summary's non-measurable strip reads real HITL/forms/energy state.

Reproduction guides: `docs/EVALUATION_GUIDE.md`, `docs/NON_MEASURABLE_GUIDE.md`,
`data/corpus/README.md`.

## The no-login guided dashboard

The headline UX for non-technical users. `VERA_AUTH_MODE=guided` (the default) means
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
  (`src/vera/schemas/run_payload.py`); empty `complai_requirements` ⇒ full measurable set.
- **Add a benchmark:** add to `src/vera/benchmarks/benchmarks_catalog.yaml` + a runner under
  `src/vera/benchmarks/runners/`; map it to one of R01–R12 with an explicit score formula (or an
  N0x HITL rubric). Keep output expressible in the `benchmark_run.yaml` schema.
- **Add a dashboard view:** route under `dashboard/src/app/`, data via `dashboard/src/lib/api.ts`,
  backend route in `dashboard_routes.py`. Honor RBAC via `AuthGuard` unless it is a guided surface.
- **Add an N0x rubric / form:** `src/vera/store/redis_hitl.py` or `schemas/declarative_forms.py`;
  surface in the run summary's non-measurable panel.

## Conventions & constraints (guardrails)

The short version (see `docs/ARCHITECTURE.md §8`):

- **100% OSS / on-prem.** No AWS/GCP/Azure managed services, no SaaS observability/feature-flags,
  no hosted vector DBs / OpenAI embeddings as default. Self-hosted judges only (vLLM + Llama/Mistral/
  Qwen). Single exception: proprietary LLMs as *evaluation targets* via LiteLLM — every default and
  fallback must work self-hosted. Prefer OSS lineage (Swarm > k8s, OpenBao > Vault, MinIO > S3, …).
- **No `pilote_v1` data in compliance views or audit exports** (hard rule). The pilot marker is
  defined in exactly one place: `src/vera/dashboard/triage.py` (`PILOTE_MARKERS`,
  `is_pilote_catalog`). Don't reintroduce the literal elsewhere — `tests/unit/test_no_pilote_v1.py`
  enforces this.
- **18-axis COMPL-AI taxonomy only** (12 measurable R01–R12, 6 non-measurable N01–N06) — no ad-hoc dimensions. Mapping in `docs/ARCHITECTURE.md §6`.
- **No binary thresholds / "regulatory cliff"** — continuous scores + green/orange/red bands
  (`score_bands.py`), human arbitration over the trade-offs.
- **Sovereign self-hosted judges** for red-teaming/ASR — never proprietary.

## Testing

```bash
make test-unit                       # pytest tests/unit/ (needs Redis on :6379)
pytest tests/integration -m integration   # VERA_INTEGRATION=1 (Redis + MinIO)
cd dashboard && npx playwright test  # RBAC matrix (25) + guided-mode (5)
ruff check src tests                 # lint
```

Unit tests use a **real Redis** (no mocking). Coverage gate is 80% on `vera`. CI: `.github/workflows/vera-ci.yml` (unit + integration + dashboard/Playwright).

## Gotchas

- `src/vera/dashboard/` (Python) ≠ `dashboard/` (Next.js).
- MLflow UI is on host `:5001` but the container listens on `5000`.
- Containers reach Ollama via `host.docker.internal:11434` (`OLLAMA_API_BASE`); native runs use `127.0.0.1`.
- R09 watermark is reported `NA` without a detector and excluded from aggregation.
- Lite mode: MLflow disabled + local artifacts; the worker's MLflow call is guarded, so it won't crash.
- The audit PDF is a **sha256 self-attestation**, not a qualified eIDAS signature (needs a real TSA).

## Keeping this file in sync

When you change a documented surface, update the owning doc and bump its `last_reviewed`. Quick checklist:

- New route / env var? → `docs/README-dev.md` + this file's repo-map/quickstart.
- New benchmark? → `benchmarks_catalog.yaml` + COMPL-AI mapping + `docs/ARCHITECTURE.md §6`.
- New guided UI? → `USER_GUIDE.md` + the guided-dashboard section above.
- New architecture surface (pipeline, dashboard, governance runtime)? → `docs/ARCHITECTURE.md`.
- New eval script / native-run flag / corpus? → `docs/EVALUATION_GUIDE.md` + this file's native-eval section.
- New dependency/tooling? → verify the OSS/on-prem doctrine (`docs/ARCHITECTURE.md §8`) first.
