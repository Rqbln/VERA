---
doc:
  title: "VERA dashboard (Next.js control room)"
  slug: dashboard-readme
  language: en
  summary: |
    Next.js 14 compliance control room: routes, guided/enterprise auth, env vars, on-prem
    deployment (no Vercel), and Playwright tests.
  type: dev-guide
  audience: [developer, ai-agent]
  navigation:
    agents: ../AGENTS.md
    dev: ../docs/README-dev.md
    user_guide: ../USER_GUIDE.md
  tags: [dashboard, nextjs, vera]
last_reviewed: "2026-06-15"
---

# VERA dashboard

A **Next.js 14** (App Router, TypeScript, Tailwind, TanStack Query, Recharts) compliance "control
room" for EU AI Act release gates. It consumes the VERA read API and ships in two modes.

## Modes

- **Guided (default, no login):** `NEXT_PUBLIC_AUTH_MODE=guided` (the default). A single persona sees
  every lens; the onboarding home + launch wizard are the entry point.
- **Enterprise:** `NEXT_PUBLIC_AUTH_MODE=enterprise` enables Keycloak OIDC (`keycloak-js`) and the
  8-persona RBAC matrix.

> `NEXT_PUBLIC_*` vars are inlined at **build** time. For Docker, pass them as **build args** (see
> `Dockerfile` and the repo `docker-compose.yml`), not just runtime env.

## Routes

| Route | Audience |
|-------|----------|
| `/home` | Guided onboarding — what you can do, connected models, kill-switch |
| `/launch` | Ollama launch wizard → `POST /api/v1/runs` |
| `/runs-overview` | Summary table of all runs (status, triage, headline score) |
| `/dashboards/compliance` · `/cyber` · `/ds` | RBAC lenses (R01–R12 triage) |
| `/runs/[id]` · `/runs/[id]/inspector` | Run summary (live polling) + audit inspector |

## Develop

```bash
cp .env.example .env.local      # guided mode is the default
npm install
npm run dev                     # http://localhost:3000 (expects the API on :8000)
```

From the repo root, `make quickstart` runs the whole lite stack (API + worker + dashboard) in Docker.

## Test

```bash
npm run build
npx playwright test             # RBAC matrix (25) + guided-mode/governance/i18n (7) + HITL review (2) + screenshots
```

## Look & feel

Light, decision-maker brand-green design system (tokens, KPI tiles, graphical timeline, lucide
icons) and a bilingual **FR/EN** toggle — see [DESIGN_SYSTEM.md](./DESIGN_SYSTEM.md). Routes:
`/home`, `/launch`, `/runs-overview`, `/governance`, `/dashboards/{compliance,cyber,ds}`,
`/runs/[id]/inspector`. The `/governance` page surfaces the MVP4 GaaS runtime.

## Deploy

Deployment is **on-premise via Docker** (`make stack-full` or `docker compose up`). This is a
sovereign, self-hostable stack — **not** deployed to Vercel or any managed cloud.
