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
make study-export     # pulls both CSVs and runs the analysis
# or directly:
python scripts/analyze_user_study.py data/user_study/sessions.csv \
       --survey data/user_study/survey.csv [--exclude P1] [--min-tasks 8] [--comments]
```

Prints per-task completion, assisted rate and median time with IQR; then, with a
survey file, the participant profile table, the TAM table (mean, SD, median per
item and per construct), Cronbach's alpha with its n, and a straight-lining
warning. All LaTeX rows are emitted ready to paste. Comments print only under
`--comments`: vet them before sharing, `data/user_study/` is not gitignored.

## Acceptability questionnaire (TAM)

After the eighth task, the same page asks eight statements on a 5-point Likert
scale, following the Technology Acceptance Model: four on **perceived usefulness**
(faster evaluation, understanding failures, justifying a decision, evaluation
quality) and four on **perceived ease of use** (clear interface, finding
information, launching a run alone, learning effort), plus an optional free-text
comment capped at 500 characters.

Method notes to carry into the paper's threats section:

- Items are grouped by construct in a **fixed order** (comprehension beats
  randomisation at this sample size) and **none is reverse-coded** (reverse items
  depress alpha at small n); a straight-lining check compensates.
- The instrument **mixes tenses**: some items report the session just experienced,
  others project onto the participant's real work. That is standard for a
  single-session TAM but must be stated.
- Cronbach's alpha is unstable below n≈8; the analysis script prints it with its n
  attached and it must be reported as indicative.

Participants also declare, from fixed lists only (no free-text identity field):
role, AI/ML experience, EU AI Act familiarity, and years of experience.

Two CSVs come out of the deployment:

| Endpoint | File | Columns |
|---|---|---|
| `GET /api/v1/study/export.csv` | `sessions.csv` | `participant,role,task_id,completed,assisted,seconds,notes` (frozen) |
| `GET /api/v1/study/export_survey.csv` | `survey.csv` | `participant,role,ai_experience,aiact_familiarity,seniority,locale,tasks_submitted,item,value,comment` |

The survey export is **session-driven**: every participant emits eight rows even
when they never reached the questionnaire, so abandonment stays visible through
`tasks_submitted` and the participant table is never silently truncated.

## Self-administered variant (app-measured)

The platform ships the study as a page: participants open `<deployment-url>/study`,
consent, declare their profile, and complete the same eight tasks. Methodology:

- **Timing is measured by the application**: a monotonic client clock starts when
  the participant presses *Start this task* and stops at submission; the server
  independently records wall-clock start/submit timestamps as a sanity channel.
- **Correctness is validated server-side** at submission time, against an answer
  key snapshotted from the target run when the session is created. The participant
  never sees whether an answer was correct (no contamination between tasks or
  participants). T5 is recorded as `unverified` (the pasted excerpt is kept for a
  manual audit against `raw_outputs.jsonl`); T8 is verified by checking that a new
  run was created after the task started.
- **No facilitator, no hints**: the `assisted` column is always `no` in this
  variant (kept for schema compatibility with the facilitated variant above).
- The 5-minute cap auto-fails a task (`timeout`); one submission per task, no retry.
- Participant codes are assigned by the server (P1, P2, ...); the role comes from
  a fixed list; no free-text identity fields exist.

### Deployment (study day)

```bash
# stack in guided mode with one COMPLETED run preloaded (see quickstart-native),
# dashboard built single-origin:
cd dashboard && NEXT_PUBLIC_API_URL="" npm run build && \
  cp -r .next/static .next/standalone/.next/ && cp -r public .next/standalone/ && \
  NEXT_PUBLIC_API_URL="" node .next/standalone/server.js
# optionally pin the study run: export VERA_STUDY_RUN_ID=<run_id> before uvicorn
make study-tunnel        # share https://<host>/study
make study-export        # after the sessions: sessions.csv + RQ1 numbers
```

Variant: host only the front on Vercel (set `NEXT_PUBLIC_API_URL` to a tunneled
API origin); the backend stays local in all cases (Ollama).

## Ethics note

No personal data beyond a role label; participation is voluntary; results are
reported in aggregate only.
