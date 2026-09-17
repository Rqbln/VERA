---
doc:
  title: "VERA — Verifiable Evaluation for Responsible AI"
  slug: root-readme
  language: en
  summary: |
    Open-source, self-hostable evaluation engine and review dashboard for responsible-AI
    requirements (COMPL-AI interpretation of the EU AI Act). The specification, benchmarks and
    scoring policy are data; every run pins the content digest of its catalog.
  audience: [human, developer, researcher]
  navigation:
    documentation: ./docs/README.md
    architecture: ./docs/ARCHITECTURE.md
    agents: ./AGENTS.md
    user_guide: ./docs/USER_GUIDE.md
    dev_setup: ./docs/README-dev.md
    paper: ./manuscript/README.md
  tags: [vera, eu-ai-act, compl-ai, responsible-ai, llm-evaluation, fairness]
last_reviewed: "2026-09-17"
---

# VERA — Verifiable Evaluation for Responsible AI

VERA turns a declared specification of responsible-AI requirements into scored, traceable evidence
that a model reviewer can read without writing code.

- **The specification is data.** A registry maps benchmarks to requirements and runners; a catalog
  weights them. Both are files selected by configuration, and every run records the SHA-256 content
  digest of the catalog. VERA ships the twelve measurable COMPL-AI requirements and a
  security-focused alternative (`examples/specs/`).
- **Every score opens onto its evidence.** Requirement scores come with bootstrap intervals, the
  benchmarks behind them, fallback flags with their causes, and run-tied artifacts (model card,
  datasheet, export).
- **Built for review.** A Next.js dashboard with a no-login guided mode and role-based views in the
  enterprise profile, human-review queues for the non-measurable requirements, and an optional
  governance runtime for live inference.

## Repository

| Path | What |
|---|---|
| `src/vera/` | The engine: API, Celery tasks, LangGraph pipeline, benchmark runners, catalog, governance, stores |
| `dashboard/` | Next.js review dashboard (guided and enterprise modes, Playwright tests) |
| `services/` | Governance-runtime services (proxy, scoring agents, audit sink) for the `gaas` profile |
| `tests/` | Unit, integration and end-to-end tests |
| `examples/` | Run definitions (`runs/`) and alternative specifications (`specs/`) |
| `data/corpus/` | The seeded synthetic banking corpus for the data-stage requirements R03–R05 |
| `infra/` | Keycloak realm and OPA policy used by the enterprise and gaas profiles |
| `scripts/` | Native setup, corpus generator, study analysis |
| `docs/` | Architecture, user guide, developer setup, evaluation and non-measurable guides |
| `manuscript/` | The ICSE 2027 SEIP paper in progress; the submitted APSEC paper in `manuscript/apsec/` |

The ICSE 2027 evaluation campaign on Microsoft Foundry runs from the separate `vera-foundry`
repository, which pins a VERA commit and generates the paper's tables.

## Quick start

**Guided / lite (one command, no login):**

```bash
ollama pull llama3.1:8b-instruct-q8_0
make quickstart          # Redis + API + worker + dashboard; open http://localhost:3000
```

**Enterprise (Keycloak RBAC, MLflow, MinIO):**

```bash
cp .env.example .env
make stack-full          # VERA_AUTH_MODE=enterprise enforces RBAC
pip install -e ".[dev]"
vera-eval run examples/runs/ollama_e2e.yaml
```

**Governance runtime** (inline proxy, event bus, scoring agents, OPA, kill-switch):
`make stack-gaas`; see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

**Native benchmark engines** (lm-eval, garak, data-stage engines, CodeCarbon):

```bash
bash scripts/setup_native.sh       # installs .[benchmarks,data,pdf] and checks Ollama models
```

## The paper

```bash
cd manuscript && make draft        # ICSE 2027 SEIP draft with its drafting cockpit
```

See [manuscript/README.md](manuscript/README.md) for the build targets, the ML-arm scenarios and
the writing conventions.

## Tests

```bash
make test-unit                       # pytest tests/unit/ (needs Redis on :6379)
pytest tests/integration -m integration
cd dashboard && npx playwright test
```

See [tests/README.md](tests/README.md) and [docs/README-dev.md](docs/README-dev.md).

## Documentation

[docs/README.md](docs/README.md) indexes everything; AI coding agents start at [AGENTS.md](AGENTS.md).

## License

Apache-2.0.
