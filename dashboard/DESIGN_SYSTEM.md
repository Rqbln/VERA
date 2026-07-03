# VERA dashboard — design system

Light, airy, decision-maker oriented. brand green. Status-first information design preserved
from the control-room era, but on white.

## Palette (tokens)

Defined as CSS variables in `src/app/globals.css` and as Tailwind colors in `tailwind.config.ts`
(hex literals so opacity modifiers like `bg-status-ok/10` work).

| Token | Tailwind | Hex | Use |
|---|---|---|---|
| brand | `brand` | `#00915A` | primary actions, headings accents |
| brand-deep | `brand-deep` | `#00673E` | header/sidebar bar |
| brand-accent | `brand-accent` | `#76B82A` | **accent only** — key figures, bullets, active timeline milestone |
| ink | `ink` | `#1F2A24` | body text |
| ink-secondary | `ink-secondary` | `#5A6B62` | secondary/labels |
| surface | `surface` / `white` | `#FFFFFF` | cards |
| surface-2 | `surface-2` | `#F4F6F5` | page background, inputs |
| surface-3 | `surface-3` | `#ECE9E0` | subtle alt background |
| border | `default` | `#DFE4E1` | borders/separators (1px) |
| status-ok | `status-ok` | `#00915A` | OK / done / compliant |
| status-partial | `status-partial` | `#E8A33D` | partial / optional / fallback / watch |
| status-blocked | `status-blocked` | `#C0392B` | failed / blocking / action needed |
| status-neutral | `status-neutral` | `#5A6B62` | unknown / neutral |

## Rules

1. **One dominant green per view.** Vivid `#76B82A` (`brand-accent`) is an *accent only* — KPI
   highlights, list bullets, the active timeline milestone. Never a large background.
2. **Status colours are semantic and fixed.** Green = OK, amber = partial, red = blocked. Only the
   hex changes vs the old theme; the meaning must not.
3. **Density preserved.** 13px base, compact tables, small inputs (`px-2 py-1`). This is a control
   room, not a marketing page.
4. **1px light borders** (`border-default`); no heavy rules; white cards on `surface-2`.

## Component classes (globals.css `@layer components`)

`.card` `.section` · `.kpi-tile` `.kpi-value` `.kpi-label` · `.badge` `.badge-ok|partial|blocked|neutral`
· `.table-header` `.table-row` · `.btn-primary|accent|secondary` · `.input`.

Reusable components: `KpiTiles.tsx` (`KpiTile`, `KpiRow`), `Timeline.tsx` (active milestone =
vivid green), icons from **lucide-react** (linear, `strokeWidth={1.75}`).

Recharts use the hex tokens directly (see `CoverageBar.tsx`, `TrendCurve.tsx`).

## Non-measurable surfaces (N01–N06)

- **HITL rubric grid** (`HitlReviewPanel.tsx`): N01/N02 reviews use a multi-criteria grid (1–5 per
  criterion, fetched from `/hitl/rubrics`) rather than a single Likert; the mean becomes the stored
  score. Render criteria as compact labelled rows reusing `.input`; show the running mean as a
  `.kpi-value`. A direct Likert field remains as a fallback.
- **Non-measurable strip** (`NonMeasurableStrip.tsx`): six slots (N01/N02 HITL, N03 energy,
  N04–N06 forms) coloured by the semantic status tokens — `status-ok` reviewed/completed,
  `status-partial` queued/measured, `status-neutral` empty. N03 shows measured `kwh`/`co2eq`.

## i18n (FR/EN)

`src/lib/i18n.tsx` — `I18nProvider` (in `providers.tsx`), `useI18n()`, `useT()`. Dictionaries `EN`
and `FR`; toggle in `DashboardShell`; persisted in `localStorage`; default via
`NEXT_PUBLIC_DEFAULT_LOCALE` (`en`|`fr`). **Acronyms stay English** (EU AI Act, COMPL-AI, LLM, RBAC,
HITL, CI, Trust Factor, GaaS). Add a string by adding the key to both `EN` and `FR`, then `t("key")`.
