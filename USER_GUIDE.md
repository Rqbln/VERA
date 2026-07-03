---
doc:
  title: "VERA user guide (guided mode)"
  slug: user-guide
  language: en
  summary: |
    Step-by-step guide for non-technical users: start VERA with one command, run an evaluation on a
    connected Ollama model, and read the results table. No code required.
  audience: [human]
  navigation:
    root_readme: ./README.md
    architecture: ./docs/ARCHITECTURE.md
    dev: ./docs/README-dev.md
  tags: [vera, user-guide, eu-ai-act]
last_reviewed: "2026-07-03"
---

# VERA user guide

This guide is for **non-technical** users. It explains how to start VERA, run an evaluation, and
read the results, without writing a single line of code.

## 1. What VERA does

VERA checks whether an AI model meets the EU AI Act's expectations. You pick a model that is already
connected (for example a local Ollama model), launch an evaluation, and read a clear **results
table**, requirement by requirement (robustness, toxicity, fairness, and so on).

## 2. Before you start (prerequisites)

One technical person does this once on the machine:

1. Install **Docker** (Docker Desktop on Mac/Windows).
2. Install **Ollama**, then download a model:
   ```bash
   ollama pull llama3.1:8b-instruct-q8_0
   ```

That is all. No account, no password.

## 3. Start with one command

In a terminal, at the project root:

```bash
make quickstart
```

Wait for startup (the first download can take a few minutes), then open your browser at
**http://localhost:3000**. No login is required.

> Tip: to stop everything, press `Ctrl+C` in the terminal, then run `make quickstart-down`.

## 4. The home screen

The home page ("Welcome to VERA") shows three actions:

- **Launch an evaluation** — start a new evaluation;
- **View runs & scores** — see the summary table;
- **Control room** — the detailed view for compliance teams.

A "Stack" strip at the top shows service health (green = OK; amber = an optional service is off,
which is normal in lite mode).

## 5. Launch an evaluation (step-by-step wizard)

Click **Launch an evaluation**. The wizard has four steps:

1. **Model** — choose the model to test. The recommended model is preselected.
2. **What to evaluate** — keep the **recommended set** (simplest) or tick your own requirements.
3. **Options** — choose the sample size ("Quick" for a fast test); the rest is optional.
4. **Review** — check the summary and click **Launch evaluation**.

You are redirected to the run page, which refreshes automatically until it finishes.

## 6. Read the results table

A run page shows:

- a **Trust Factor** (an overall confidence score out of 100);
- the **requirement table (R01–R12)**: each row has a score, a confidence interval, and a colour band.

How to read the colours:

| Colour | Meaning |
|--------|---------|
| 🟢 Green | compliant |
| 🟠 Amber | watch |
| 🔴 Red | action required |

> Important: there is **no binary pass/fail threshold**. The colours help a human weigh the
> trade-offs (for example capability vs fairness). The final decision stays human.

Failed or fallback rows are surfaced at the top of the table. Click a row to open the detail
(benchmarks used, rationale, sample outputs).

## 7. Going further (optional)

At the bottom of a run page, the **Governance & trends** section lets you:

- see the **trend** of a requirement across several runs (once there are at least two runs of the model);
- record a **human review** for N01 (explainability) and N02 (corrigibility): a **rubric** scored
  1–5 (the mean gives the score), rather than a single number;
- fill the **declarative forms** N04–N06 (energy **N03 is measured automatically** during the
  evaluation, so you enter nothing);
- **download a signed PDF report** for audit (requires the `pdf` option on the server).

The **N01–N06** strip on a run summary reflects real state (reviews queued/done, energy measured,
forms filled). The **kill-switch** blocks any new evaluation in one click. A **FR/EN** button at the
top right switches the interface language (technical acronyms — EU AI Act, COMPL-AI, LLM, RBAC — stay
in English).

## 7a. Continuous governance (advanced, enterprise mode)

The **Governance** page supervises a model **deployed live** (beyond a one-off evaluation): three
modes (*shadow* observes, *advisory* alerts, *enforcement* blocks), a live Trust Factor recomputed
from four agents (cyber, ethics/toxicity, privacy, drift), signed incident logs, and a kill-switch.
It is optional and for advanced teams (`make stack-gaas`; see
[docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md)). The guided stack stays one command.

## 8. Common issues

| Symptom | Fix |
|---------|-----|
| "No models connected" in the wizard | Ollama is not running or no model is downloaded. Run `ollama pull llama3.1:8b-instruct-q8_0`. |
| Blank page on startup | Wait for the containers to finish starting, then reload. |
| The PDF button shows a warning | PDF export needs the server option `pip install '.[pdf]'` (and the cairo/pango libraries). |
| The "Stack" strip is amber | Normal in lite mode: MinIO/MLflow are optional. Red means a required service (Redis, Ollama) is unavailable. |

## 9. For technical teams

- Full documentation: [docs/README.md](./docs/README.md)
- Architecture: [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md)
- AI agent guide: [AGENTS.md](./AGENTS.md)
- Enterprise mode (Keycloak/RBAC) and setup: [docs/README-dev.md](./docs/README-dev.md)
- **Native evaluation** (all benchmarks R03–R12 actually executed, multi-model panel, banking
  corpus, paper reproduction): [docs/EVALUATION_GUIDE.md](./docs/EVALUATION_GUIDE.md)
