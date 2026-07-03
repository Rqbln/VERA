---
doc:
  title: "VERA architecture"
  slug: architecture
  language: en
  summary: |
    The VERA framework end to end: conceptual model, the evaluation pipeline, the signed catalog and
    auditable aggregation, the role-based dashboard, the optional governance runtime, the benchmark
    suite and COMPL-AI mapping, and the run artifacts.
  audience: [developer, researcher, ai-agent]
  navigation:
    root_readme: ../README.md
    dev_setup: ./README-dev.md
    evaluation: ./EVALUATION_GUIDE.md
    non_measurable: ./NON_MEASURABLE_GUIDE.md
  tags: [architecture, vera, eu-ai-act, compl-ai]
last_reviewed: "2026-07-03"
---

# VERA architecture

VERA turns a model and a set of responsible-AI requirements into an **explainable, signed
scorecard** that different roles can read. This document is the single architecture reference; the
research paper in `manuscript/` is the companion write-up.

## 1. Conceptual model

- **Input:** an evaluation target (a model endpoint, a checkpoint, or a dataset corpus) plus the set
  of requirements to check.
- **Output:** a scorecard, one score per measurable COMPL-AI requirement (CR01–CR12) with a bootstrap
  confidence interval, plus run-tied governance documents (model card, and a datasheet for dataset
  runs) and a full provenance trail (which benchmark and scorer produced each number, under which
  signed weighting).

The founding idea is that a single global compliance number is semantically thin and even hazardous:
it hides *why* a model fails and creates regulatory cliffs where a small change flips a pass into a
fail. VERA replaces the single number with a per-criterion view, a signed and certifiable scoring
policy, and role-segregated dashboards.

## 2. Evaluation pipeline

Three-layer design: **orchestration → execution → restitution**.

```
POST /api/v1/runs ─▶ Redis run record ─▶ Celery task (run_benchmark_job)
        │                                        │
        ▼                                        ▼
  RunCreateRequest                    LangGraph supervisor: evaluate ▸ aggregate
                                                 │
                      LiteLLM ─▶ Ollama (target) + self-hosted judge
                                                 │
                      artifacts ─▶ MinIO or local FS; metrics ─▶ MLflow (optional)
                                                 ▼
                      dashboard read API (/runs, /summary, /series, /inspector, /health/stack)
```

- **Invocation:** the `vera-eval` CLI, the `POST /api/v1/runs` REST endpoint, or the no-login guided
  wizard — all enqueue the same declarative job (Celery + Redis), which also holds the run store and
  the kill-switch.
- **Execution (`evaluate` node):** resolves each requirement to its benchmarks through the registry,
  dispatches each to its runner (`lm_eval`, `garak`, `hf_dynamic`, `dataset_scan`, …), and routes
  inference through LiteLLM to a self-hosted target and judge.
- **Aggregation (`aggregate` node):** combines the cached per-item scores into one score per
  requirement, with bootstrap confidence intervals, using the signed catalog (see §3).
- **Restitution:** the read API serves scores and artifacts to the dashboard (§4).

Key modules: `src/vera/api/` (routes), `src/vera/graph/` (LangGraph supervisor),
`src/vera/benchmarks/` (catalog + runners), `src/vera/stats/bootstrap.py` (weighted aggregation),
`src/vera/tasks/eval.py` (the job), `src/vera/store/` (Redis stores).

## 3. Signed catalog and auditable aggregation

Each measurable requirement `R` is a weighted mean of its per-benchmark means,
`s_R(w) = Σ_b w_b · m_b` with `w_b ≥ 0` and `Σ_b w_b = 1`, read from the catalog
(`src/vera/benchmarks/benchmarks_catalog.yaml`, `catalog.py`).

- **Signed and versioned.** The catalog is versioned; `catalog_digest()` computes a SHA-256 over its
  canonical content and the digest is pinned into every run (signature payloads,
  `benchmark_run.yaml` reproducibility block, and the run inspector). A score therefore always names
  the exact weighting that produced it. `validate_registry_catalog_alignment()` runs at job start so
  the registry and the catalog cannot drift; a benchmark without a catalog weight is **excluded**
  from the aggregate, never silently defaulted.
- **Certifiable verdicts.** Because `s_R(w)` is a convex combination of the per-benchmark means, the
  reachable score over the entire simplex of weightings is exactly `Δ_R = max_b m_b − min_b m_b`.
  If `Δ_R = 0` (or the reachable interval stays inside one band) the verdict is **certified
  invariant** to any reweighting; if the interval straddles a band threshold the verdict is
  **weight-dependent**. `manuscript/scripts/gen_sensitivity_panel.py` computes `Δ` and the flip flag
  per requirement and verifies that every stored aggregate reproduces from its decomposition.
- **Bands, not thresholds.** Scores render as green / amber / red bands (`score_bands.py`: green
  ≥ 0.70, amber ≥ 0.40), never a binary pass/fail; release decisions are human trade-offs.

## 4. Role-based dashboard

The `dashboard/` Next.js app (App Router, TanStack Query, Tailwind, Recharts, Playwright) is the
restitution surface. Do not confuse it with `src/vera/dashboard/` (Python triage / score-band logic).

- **No-login guided mode (default).** `VERA_AUTH_MODE=guided`: a single persona holds every role and
  all lenses render. `/home` (what you can do + connected models), `/launch` (a four-step wizard:
  pick a connected model → recommended or custom requirements → options → review → `POST /runs`, then
  a live run summary), `/runs-overview`.
- **Enterprise mode.** `VERA_AUTH_MODE=enterprise` enforces Keycloak RBAC with role-based lenses
  (`/dashboards/{compliance,cyber,ds}`) and an executive view. Roles gate the requirement set and the
  level of detail; auth is in `src/vera/api/auth.py`, routes in `dashboard_routes.py`.
- **Explaining a score.** Each requirement row shows a score, an interval, and a rationale; opening a
  row reveals the contributing public benchmarks and a sample output, so a reader sees *why* a
  requirement is weak. A run inspector exposes the run file, git SHA, signature, catalog digest, and
  per-benchmark provenance.
- **Human-in-the-loop.** The non-measurable requirements N01/N02 use a multi-criteria HITL rubric
  (`src/vera/store/redis_hitl.py`); N03 energy is measured automatically (CodeCarbon,
  `governance/energy.py`); N04–N06 are declarative forms with a signed audit PDF (`forms_routes.py`).

## 5. Governance runtime (optional, profile-gated)

Evaluation asks whether a model is responsible now; production also needs to know whether it stays
responsible. The optional governance runtime (`make stack-gaas`) wraps the same pipeline:

- an **inline proxy** in front of the target consults the policy layer, forwards the request, and
  off-band publishes it to an **event bus**;
- four asynchronous **agents** (cyber CR02, ethics CR12, privacy CR05, drift CR01) score the stream
  into a **streaming Trust Factor**;
- an **Open Policy Agent** layer turns the mode, the kill-switch, and the live Trust Factor into an
  `allow` / `flag` / `deny` decision under three modes (shadow, advisory, enforcement);
- every request, signal, and decision becomes a **signed, append-only audit record**, and a canary
  injects synthetic traffic.

It degrades gracefully (bus → Redis Streams, OpenSearch → signed JSONL, OPA → in-process rule); the
lite profile instantiates none of it. Code in `src/vera/governance/` and `services/`; admin API
`/admin/v1/*`; UI at `/governance`.

## 6. Benchmarks and the COMPL-AI mapping

VERA reuses established public suites rather than proposing new benchmark science. The catalog maps
them to the twelve measurable requirements (see also `docs/EVALUATION_GUIDE.md` for the native-vs
fallback matrix):

| Requirement | Focus | Public benchmarks |
|---|---|---|
| CR01 | Robustness | MMLU (perturbed) |
| CR02 | Cyber resilience | AdvBench, DecodingTrust, TensorTrust, LLM-Rules |
| CR03–CR05 | Data adequacy / copyright / privacy | synthetic corpus scans (Detoxify, near-duplicate, Presidio) |
| CR06 | Capabilities | MMLU, GSM8K, HumanEval, TruthfulQA, BBH |
| CR07 | Calibration | Expected Calibration Error on MMLU |
| CR08 | AI disclosure | dynamic disclosure probes |
| CR09 | Watermark | statistical green-list test (Kirchenbauer-style) |
| CR10 | Representation bias | BBQ, BOLD, StereoSet |
| CR11 | Fairness | DecodingTrust (Adult) |
| CR12 | Toxicity | RealToxicityPrompts, AdvBench-instruction, TruthfulQA |

The six non-measurable requirements N01–N06 use human review, energy measurement, or declarative
forms (see `docs/NON_MEASURABLE_GUIDE.md`). Adding a benchmark = add a runner under
`src/vera/benchmarks/runners/` + a catalog entry mapped to one requirement with an explicit score
formula, keeping the output expressible in `benchmark_run.yaml`.

## 7. Artifacts and reproducibility

Every run emits, to object storage or the local filesystem: the declarative `benchmark_run.yaml`
(with `reproducibility`: seed, catalog version + digest, git SHA), a `model_card.md` (and a
datasheet for dataset runs), `raw_outputs.jsonl` (per-benchmark provenance and fallback flags), and a
content signature. The dataset-stage requirements run over a 100%-synthetic banking corpus
(`data/corpus/banking_synth.jsonl`, regenerate with `scripts/gen_banking_corpus.py`). See
`docs/EVALUATION_GUIDE.md` to reproduce the paper's multi-model panels.

## 8. Deployment profiles and constraints

One codebase, three profiles: **lite** (Redis + API + worker + dashboard, local artifacts, no login),
**enterprise** (adds Keycloak RBAC, MLflow, MinIO, TimescaleDB), and **gaas** (adds the governance
runtime of §5). Every layer degrades gracefully. The project is **fully open-source and
self-hostable**: no managed cloud services and no SaaS observability by default; proprietary LLMs are
allowed only as *evaluation targets* through LiteLLM, and every default and fallback path works with
self-hosted models.
