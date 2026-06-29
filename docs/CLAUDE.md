---
doc:
  title: "CLAUDE — Conventions dépôt VERA (assistants IA)"
  slug: claude-agent-guide
  language: mixed
  summary: |
    Règles pour éditer code et documentation : graphe documentaire, MAS, COMPL-AI, OSS/local-first,
    emplacement du scaffold Python MVP1.
  type: agent-guide
  audience: [ai-agent, developer]
  navigation:
    index: ./README.md
    hub: ./ROADMAP.md
  related_paths:
    - ../AGENTS.md
    - ./README-dev.md
    - ./MVP1_noyau_statique.md
  tags: [claude, cursor, conventions, compl-ai, vera]
last_reviewed: "2026-06-15"
---

# CLAUDE.md

> L'orientation et le quickstart pour agents vivent dans la racine [AGENTS.md](../AGENTS.md) ;
> ce fichier est la **référence profonde** (conventions & graphe documentaire). Le mode guidé
> sans login et la stack « lite » sont décrits dans AGENTS.md et [README-dev.md](./README-dev.md).

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository nature

This repository contains **EU AI Act–aligned planning documents** (Markdown under `docs/`) **and** an **MVP1 Python scaffold** under `src/vera/` (FastAPI, Celery, LangGraph, LiteLLM → Ollama, MLflow, MinIO). Use `pyproject.toml`, `docker-compose.yml`, and [README-dev.md](./README-dev.md) for build/run instructions.

Working language: prose is **French**; code identifiers, schemas, table names, and tooling references stay in English. Match the existing voice when editing.

## Document graph

`./ROADMAP.md` is the hub. Each MVP file is a child that must remain consistent with it.

- `./ROADMAP.md` — global vision, transverse stack table (§2.1), canonical `benchmark_run.yaml` schema (§2.3), EU AI Act × MVP mapping (§3), 18-month Gantt (§5).
- `./MVP1_noyau_statique.md` — black-box inference evaluation (5 risk dimensions). Defines the benchmark catalogue reused downstream.
- `./MVP2_laboratoire_injection.md` — spec normative labo (données, poisoning, cycle de vie). **Reuses MVP1's Checkpoint Evaluator.**
- `./MVP2_ROADMAP_LAB.md` — hub d'exécution phases 0–7 ; `./MVP2_STATUS.md` — **lire avant toute modification MVP2 lab** ; `./mvp2-lab/PHASE_*.md` — détail par phase.
- `./MVP3_dashboards_rbac.md` — longitudinal dashboards, RBAC. **Sources are MVP1 (MLflow) + MVP2 (TimescaleDB trajectories).**
- `./MVP4_governance_as_a_service.md` — production proxy, live Trust Factor, kill-switch. **Depends on MVP1 benchmarks, MVP2 trigger registry, MVP3 dashboards.**
- `./framework_open_source_ia_responsable.md` and `./Évaluation Modulaire IA Cycle Vie EU AI Act.md` — upstream reference content; MVPs derive from them.
- `./2410.07959v2.pdf` (COMPL-AI) — external academic source cited at the top of `ROADMAP.md`.
- `Untitled` — original user brief that seeded the roadmap; treat as historical, not authoritative.

When editing any MVP doc, check `ROADMAP.md` first: stack choices (LangGraph, LiteLLM, MLflow, TimescaleDB, MinIO, Keycloak, etc.), the canonical run schema, and the AI Act mapping live there and must not drift across MVPs.

## Code layout (MVP1 scaffold)

- `src/vera/api/main.py` — FastAPI routes (`/api/v1/runs`, etc.).
- `src/vera/celery_app.py` — Celery application.
- `src/vera/tasks/eval.py` — async evaluation job (LangGraph, MLflow, MinIO).
- `src/vera/graph/` — LangGraph supervisor (evaluate + aggregate).
- `src/vera/benchmarks/` — `benchmarks_catalog.yaml`, runners (`lm_eval`, `garak`, `hf_dynamic`).
- `src/vera/llm/client.py` — LiteLLM wrapper (Ollama default `llama3.1:8b-instruct-q8_0`).
- `examples/mvp2_ollama_e2e.yaml` — E2E payload ; `examples/poisoning_experiment.yaml` — Hydra lab ; `examples/mvp1_pilote_e2e.yaml` — historical MVP1.

## MVP2 Lab workflow (agents)

1. Read `./MVP2_STATUS.md` for current requirement × code matrix.
2. Open the active `./mvp2-lab/PHASE_XX_*.md` fiche only (do not load all phases).
3. After code changes, update `MVP2_STATUS.md` and the phase fiche checklists; check spec §9 if exit criterion met.
4. **PR rule** : do not merge lab work without STATUS + phase doc updates.

## Architectural through-line

Five concepts recur across all docs and must stay coherent when editing any one of them:

1. **Paradigm**: longitudinal supervision across the full lifecycle (data → pretrain → finetune → inference → production), **not** a static end-of-pipeline test. Avoid wording that reverts to a single-shot evaluation.
2. **Three-layer MAS**: Orchestration (Supervisor agent, LangGraph) → Evaluation (three grouped agents: *Data & Red Teaming*, *Cyber-Robustesse*, *Éthique & Conformité*) → Telemetry/Storage → Restitution (RBAC dashboards). The grouping into three agents is deliberate — do not split them into more without updating every doc.
3. **MVP scope discipline**: each MVP file has explicit *In / Out / Hors périmètre* sections. New features should be placed in the MVP that already owns the relevant lifecycle stage rather than bleeding across MVPs.
4. **Open-source & local-first**: every infrastructure component (storage, queue, secrets, auth, gateway, dashboards, CI, feature flags, alerting…) MUST be self-hostable open-source software. Forbidden: AWS / GCP / Azure managed services, external object stores (S3, GCS), Datadog, Splunk SaaS, LaunchDarkly, Perspective API, hosted vector DBs, OpenAI embeddings as a default. **Single allowed exception**: proprietary LLMs as *evaluation targets* (Claude, GPT, Gemini) routed through LiteLLM — but every default and every fallback path must work with self-hosted models (vLLM + Llama/Mistral/Qwen). When citing tooling, prefer the OSS lineage: **Docker Swarm over Kubernetes** (the chosen orchestrator — lighter, native, simpler stack/Compose management; do not reintroduce Helm, Kyverno, kubectl, namespaces, Pod Security Standards, HPA — Swarm uses stacks, services, overlay networks, `--generic-resource gpu=N`, `docker service scale`), OpenBao over Vault, Unleash/GrowthBook over LaunchDarkly, MinIO over S3, Mattermost over Slack as the default channel, Forgejo/Gitea Actions or self-hosted GitHub Runners over hosted GitHub Actions, Wazuh/OpenSearch over Splunk, bge-large/e5-mistral over OpenAI embeddings.
5. **COMPL-AI 18 technical requirements as the evaluation backbone**: the EU AI Act's 6 ethical principles (Human Agency, Robustness & Safety, Privacy, Transparency, Diversity/Fairness, Societal & Environmental Well-being) are decomposed by the COMPL-AI framework (`2410.07959v2.pdf`) into **18 technical requirements** — **12 measurable** (each producing a score in [0, 1] or [0, 100] with a documented mathematical definition) and **6 non-measurable** (declarative forms or qualitative HITL). Every benchmark added to any MVP must be mapped to one of the 12 measurable requirements with an explicit score formula, OR to a HITL rubric for one of the non-measurable requirements. Do not invent ad-hoc dimensions outside this 18-axis taxonomy. The canonical mapping table lives in `ROADMAP.md` §3 and is referenced by all MVPs.

## Conventions

- Diagrams use **Mermaid** (`flowchart`, `sequenceDiagram`, `gantt`, `mindmap`). Keep new diagrams in Mermaid for consistency.
- Tables follow the pattern `| Couche | Tech | Version | Rôle |` for stack tables and `| Benchmark | Métrique | Dimension | Article AI Act |` for benchmark/regulation mappings.
- Cross-references between MVPs use relative links (e.g., `[MVP1](./MVP1_noyau_statique.md)`); preserve this style.
- Each MVP doc opens with a `> Voir [ROADMAP.md]` blockquote and (from MVP2 onward) a `> Pré-requis:` line listing prior MVPs. New MVP-style docs should follow the same header.
- The `benchmark_run.yaml` schema in `ROADMAP.md` §2.3 is the pivot format — metric/run additions in any MVP must remain expressible in it.
