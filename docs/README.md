---
doc:
  title: "VERA documentation index"
  slug: docs-index
  language: en
  summary: Entry point to VERA's documentation for humans, developers, researchers, and AI agents.
  audience: [human, developer, researcher, ai-agent]
  tags: [vera, docs, index]
last_reviewed: "2026-09-17"
---

# VERA documentation

VERA is an open-source framework for evaluating LLMs against the EU AI Act. Start with the root
[README](../README.md) for the project overview and quick start.

## Map

| Document | For | What it covers |
|---|---|---|
| [ARCHITECTURE.md](ARCHITECTURE.md) | developers, researchers | The framework end to end: pipeline, signed catalog and auditable aggregation, dashboard, governance runtime, benchmark mapping, artifacts. |
| [README-dev.md](README-dev.md) | developers | Local setup (lite and full stacks, Docker, Ollama), the test pyramid, and air-gap / egress notes. |
| [EVALUATION_GUIDE.md](EVALUATION_GUIDE.md) | researchers | Native benchmark engines, the synthetic corpus, and serving caveats. |
| [NON_MEASURABLE_GUIDE.md](NON_MEASURABLE_GUIDE.md) | compliance, developers | Filling the non-measurable requirements N01–N06 (human review, energy, declarative forms). |
| [USER_STUDY_PROTOCOL.md](USER_STUDY_PROTOCOL.md) | researchers | The self-administered study module at `/study` and its analysis script. |
| [USER_GUIDE.md](USER_GUIDE.md) | non-technical users | Running an evaluation and reading the results, no code. |
| [../AGENTS.md](../AGENTS.md) | AI coding agents | Orientation, repo map, quickstart, conventions and guardrails. |
| [../dashboard/README.md](../dashboard/README.md) | frontend developers | Dashboard routes, auth modes, environment, deployment. |
| [../dashboard/DESIGN_SYSTEM.md](../dashboard/DESIGN_SYSTEM.md) | frontend developers | Design tokens and component rules. |
| [../data/corpus/README.md](../data/corpus/README.md) | researchers | The synthetic banking corpus schema (100% synthetic, planted PII / near-duplicates / imbalance). |
| [../tests/README.md](../tests/README.md) | developers | The test tiers and policy. |

## The papers

`manuscript/` holds the ICSE 2027 SEIP paper in progress (build and writing conventions in
[../manuscript/README.md](../manuscript/README.md)); the submitted APSEC paper is frozen in
[../manuscript/apsec/](../manuscript/apsec/README.md).
