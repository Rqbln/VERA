# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository nature

This repository is **documentation-only** — there is no source code, build system, package manifest, or test suite. It is a planning baseline for a future platform (RAIP — Responsible AI in Practice) targeting EU AI Act alignment. There are no commands to build, lint, or test; tasks here are read/write/restructure of Markdown files.

Working language: prose is **French**; code identifiers, schemas, table names, and tooling references stay in English. Match the existing voice when editing.

## Document graph

`ROADMAP.md` is the hub. Each MVP file is a child that must remain consistent with it.

- `ROADMAP.md` — global vision, transverse stack table (§2.1), canonical `benchmark_run.yaml` schema (§2.3), EU AI Act × MVP mapping (§3), 18-month Gantt (§5).
- `MVP1_noyau_statique.md` — black-box inference evaluation (5 risk dimensions). Defines the benchmark catalogue reused downstream.
- `MVP2_laboratoire_injection.md` — data + pre-train + fine-tune phases, Poisoning Lab. **Reuses MVP1's Checkpoint Evaluator.**
- `MVP3_dashboards_rbac.md` — longitudinal dashboards, RBAC. **Sources are MVP1 (MLflow) + MVP2 (TimescaleDB trajectories).**
- `MVP4_governance_as_a_service.md` — production proxy, live Trust Factor, kill-switch. **Depends on MVP1 benchmarks, MVP2 trigger registry, MVP3 dashboards.**
- `framework_open_source_ia_responsable.md` and `Évaluation Modulaire IA Cycle Vie EU AI Act.md` — upstream reference content; MVPs derive from them.
- `2410.07959v2.pdf` (COMPL-AI) — external academic source cited at the top of `ROADMAP.md`.
- `Untitled` — original user brief that seeded the roadmap; treat as historical, not authoritative.

When editing any MVP doc, check `ROADMAP.md` first: stack choices (LangGraph, LiteLLM, MLflow, TimescaleDB, MinIO, Keycloak, etc.), the canonical run schema, and the AI Act mapping live there and must not drift across MVPs.

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
