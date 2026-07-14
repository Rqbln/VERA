---
doc:
  title: "VERA user study protocol (RQ1, external non-specialists)"
  slug: user-study-protocol
  language: en
  summary: |
    Fixed-task, timed walkthrough of the control room with n>=5 external
    non-specialists (compliance / risk profiles, not authors). Produces the
    completion and timing data behind the paper's RQ1 claim.
  audience: [human]
last_reviewed: "2026-07-13"
---

# VERA user study protocol (RQ1)

**Goal.** Measure whether a non-specialist can read an evaluation run from the
dashboard alone. Output: per-task completion (unassisted / assisted / failed)
and time, for n >= 5 external participants.

## Participants

- n >= 5, **not authors of the paper**, no prior exposure to VERA.
- Target profiles: compliance officer, risk manager, legal, audit, or a
  comparable non-ML role.
- Record only: participant code (P1..Pn) and role. No names, no employer in the
  data file (double-blind safety).

## Setup (before each session)

1. Stack running in guided mode with one **completed** run preloaded
   (`make quickstart`, or the native stack; verify http://localhost:3000
   shows the run summary with the Trust Factor gauge).
2. Browser open on `/home`. Timer ready (phone stopwatch is fine).
3. One facilitator. The facilitator reads tasks verbatim and does not touch
   the mouse or keyboard.

## Facilitator script (read verbatim)

> "VERA evaluated an AI model against responsible-AI requirements. You will
> use its dashboard to answer eight questions. I cannot help you navigate,
> but you can think aloud. There is no right or wrong pace."

Per task: read the task, start the timer when you finish reading, stop it when
the participant states the answer or gives up. Cap each task at **5 minutes**.
If the participant asks for help and you give ONE hint, mark the task
`assisted`. If they give up or the cap is hit, mark `failed`.

## The eight tasks

| ID | Task (read verbatim) | Success criterion |
|----|----------------------|-------------------|
| T1 | "Which requirement is the model weakest on?" | Names the top row of the triage table (or a weakest-requirement chip) |
| T2 | "For that requirement, what is its score and its confidence interval?" | Reads score + CI from the table row |
| T3 | "Which checks ran in a degraded (fallback) mode?" | Names the fallback-flagged benchmark(s) |
| T4 | "How many of the twelve requirements were evaluated in this run?" | States the coverage (band or count) |
| T5 | "Show me one actual model answer that contributed to a score." | Reaches a sample output via a requirement drawer |
| T6 | "How many requirements failed, how many are in fallback, how many are OK?" | Reads the three verdict counts |
| T7 | "What is the overall Trust Factor, and is it compliant, watch, or action needed?" | Reads the gauge score + band badge |
| T8 | "Launch a new evaluation on the recommended model with the recommended settings." | Reaches the wizard review step and submits |

## Data entry

Append one line per participant x task to `data/user_study/sessions.csv`
(template: `data/user_study/template.csv`):

```
participant,role,task_id,completed,assisted,seconds,notes
P1,risk officer,T1,yes,no,34,
P1,risk officer,T2,yes,no,21,
```

- `completed`: `yes` | `no`
- `assisted`: `yes` if one hint was given, else `no`
- `seconds`: integer, timer value (leave empty when `completed=no`)

## Analysis

```bash
python scripts/analyze_user_study.py data/user_study/sessions.csv
```

Prints per-task completion rate, assisted rate, median time with IQR, and the
LaTeX rows for the paper's RQ1 table.

## Ethics note

No personal data beyond a role label; participation is voluntary; results are
reported in aggregate only.
