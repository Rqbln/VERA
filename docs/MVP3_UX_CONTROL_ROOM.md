---
doc:
  title: "MVP3 — UX Control Room"
  slug: mvp3-ux-control-room
  language: en
  summary: |
    Dense compliance control room UX: lifecycle run summary, status-first triage, progressive disclosure, run inspector.
  type: mvp
  audience: [developer, compliance, ai-agent]
  navigation:
    hub: ./MVP3_dashboards_rbac.md
  related_paths:
    - ./MVP3_dashboards_rbac.md
    - ./README-dev.md
last_reviewed: "2026-06-09"
---

# MVP3 UX — Compliance Control Room

> Companion to [MVP3_dashboards_rbac.md](./MVP3_dashboards_rbac.md). Defines the **default restitution UX** (not a marketing site).
>
> A **guided, no-login mode** now complements this control-room UX for non-technical users (onboarding
> home, Ollama launch wizard, runs summary). See [USER_GUIDE.md](../USER_GUIDE.md) and the status matrix
> [MVP3_MVP4_IMPLEMENTATION.md](./MVP3_MVP4_IMPLEMENTATION.md). The dense control-room remains the
> enterprise/expert surface.

## Principles

1. **Dense, calm, scannable** — 13px tables, neutral zinc palette, no hero KPI cards.
2. **Status-first triage** — failed → fallback → uncovered surfaced first; ok/na behind “Show all”.
3. **Progressive disclosure** — one-line rationale + CI on row; `benchmark_run.yaml`, model card, `raw_outputs.jsonl` on drill-down only.
4. **Lifecycle-aware** — dataset / checkpoint / inference rail; default run summary per stage.
5. **Sparse charts** — single COMPL-AI coverage bar until Timescale `/series` has data.
6. **Sovereign chrome** — stack health strip (Redis, MinIO, MLflow, Ollama); no mandatory cloud widgets.
7. **HITL as queues** — N01/N02 review slots beside N04 artifacts; not chat-first.

## Routes

| Route | Lens |
|-------|------|
| `/dashboards/compliance` | Full R01–R12 triage |
| `/dashboards/cyber` | R02, R09, R12 + fallback emphasis |
| `/dashboards/ds` | R01, R06, R07 |
| `/runs/{id}/inspector` | Stages, parse QA, signatures, presigned artifacts |

## API (dashboard read)

See `src/vera/api/dashboard_routes.py`: `GET /runs`, `/runs/{id}/summary`, `/inspector`, `/health/stack`, `/series` (stub).

## Deferred

- Longitudinal curves / trade-off explorer (Timescale ETL)
- Argilla HITL panel (slots + `GET /hitl/tasks` stub only)
- PDF audit export button (disabled until WeasyPrint job)
