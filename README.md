---
doc:
  title: "VERA — Verifiable Evaluation for Responsible AI"
  slug: root-readme
  language: en
  summary: |
    Open-source, self-hostable framework that runs the twelve measurable COMPL-AI requirements
    of the EU AI Act, makes the scoring policy signed and auditable, certifies each verdict's
    robustness to reweighting, and presents everything through a role-based dashboard.
  audience: [human, developer, researcher]
  navigation:
    documentation: ./docs/README.md
    architecture: ./docs/ARCHITECTURE.md
    agents: ./AGENTS.md
    user_guide: ./USER_GUIDE.md
    dev_setup: ./docs/README-dev.md
    paper: ./manuscript/main.tex
  tags: [vera, eu-ai-act, compl-ai, responsible-ai, llm-evaluation]
last_reviewed: "2026-07-03"
---

# VERA — Verifiable Evaluation for Responsible AI

**VERA** is an open-source, self-hostable framework for evaluating large language models against the
**EU AI Act**. It runs the twelve measurable **COMPL-AI** requirements, but goes past a benchmarking
study in three ways that define the project:

1. **Auditable scoring.** The benchmark-to-requirement weighting is a *versioned, signed catalog*
   whose SHA-256 digest is pinned into every run, and a **closed-form bound certifies, per
   requirement, which verdicts no reweighting can flip and flags the ones it can**. COMPL-AI
   aggregates each requirement by an unweighted average and never quantifies that dependence.
2. **Operability.** Results are delivered through a **role-based dashboard** a non-specialist can
   drive end-to-end without writing code, and each run emits a **run-tied model card and datasheet**
   toward the Act's technical-documentation duty (Art. 11).
3. **Modularity.** The requirement specification, the benchmarks, and the weights are **swappable
   data**, so VERA runs COMPL-AI today and adapts to a different responsible-AI specification without
   code changes. This is why it is a *framework*, not a one-off study.

VERA accompanies a research paper (`manuscript/`) evaluated across two model panels (three families
at one size, and three sizes of one family) on public datasets and a released synthetic corpus.

## Documentation

- **Architecture:** [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — the framework end to end (pipeline, catalog, dashboard, governance runtime, benchmarks, artifacts).
- **Non-technical users:** [USER_GUIDE.md](USER_GUIDE.md) — run an evaluation and read the results, no code.
- **Documentation index:** [docs/README.md](docs/README.md).
- **Developer setup & tests:** [docs/README-dev.md](docs/README-dev.md).
- **AI coding agents:** [AGENTS.md](AGENTS.md) — orientation, repo map, quickstart, guardrails.
- **Paper reproduction:** [docs/EVALUATION_GUIDE.md](docs/EVALUATION_GUIDE.md); non-measurable requirements: [docs/NON_MEASURABLE_GUIDE.md](docs/NON_MEASURABLE_GUIDE.md).

## What is in the box

- CLI `vera-eval`, FastAPI, Celery, LangGraph, LiteLLM → **Ollama** (default target
  `ollama/llama3.1:8b-instruct-q8_0`) with a self-hosted judge, MLflow, MinIO.
- A **signed benchmark catalog** (`src/vera/benchmarks/benchmarks_catalog.yaml`) mapping public
  suites (MMLU, GSM8K, HumanEval, TruthfulQA, BBH, BBQ, BOLD, StereoSet, RealToxicityPrompts,
  AdvBench, DecodingTrust) to the twelve requirements, with bootstrap confidence intervals.
- A **Next.js dashboard** (control room + no-login guided mode), and an optional
  **governance runtime** that gates live inference (inline proxy, event bus, scoring agents,
  streaming Trust Factor, OPA policy, kill-switch, signed audit trail).

## Quick start

**Guided / lite (one command, no login)** — for demos and non-technical users:

```bash
ollama pull llama3.1:8b-instruct-q8_0
make quickstart          # docker compose -f docker-compose.lite.yml up --build
# open http://localhost:3000 (see USER_GUIDE.md)
```

**Full / enterprise (Keycloak RBAC + MLflow + MinIO):**

```bash
cp .env.example .env      # adjust as needed
make stack-full           # docker compose up --build; VERA_AUTH_MODE=enterprise enforces RBAC
pip install -e ".[dev]"
vera-eval run examples/mvp2_ollama_e2e.yaml
```

**Governance runtime** — live-inference governance (inline proxy, event bus, agents, OPA):

```bash
make stack-gaas           # full stack + inline proxy (:8100), Redpanda, OPA, OpenSearch, agents
# dashboard page /governance; details in docs/ARCHITECTURE.md
```

**Native evaluation (real benchmark engines, multi-model panel, banking corpus)** — reproduces the
paper numbers:

```bash
python scripts/gen_banking_corpus.py              # (optional) regenerate data/corpus/banking_synth.jsonl (230 docs, seeded)
bash scripts/setup_native.sh                      # installs .[benchmarks,lab,pdf], checks Ollama/models
VERA_REQUIRE_NATIVE=1 python scripts/run_paper_eval.py
python manuscript/scripts/gen_sensitivity_panel.py   # verdict-sensitivity table + figure
```

See [docs/EVALUATION_GUIDE.md](docs/EVALUATION_GUIDE.md) for the full protocol and serving caveats
(Ollama exposes no token log-probabilities, so log-likelihood tasks use dynamic probes; native
lm-eval is reserved for a vLLM backend, recorded in provenance).

## Tests

```bash
make test-unit                       # pytest tests/unit/ (needs Redis on :6379)
pytest tests/integration -m integration
cd dashboard && npx playwright test  # RBAC matrix + guided-mode
```

Unit tests use a real Redis (no mocking of core paths); coverage gate 80%. See
[tests/README.md](tests/README.md) and [docs/README-dev.md](docs/README-dev.md).

## License

Apache-2.0.
