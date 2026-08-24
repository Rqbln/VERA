---
doc:
  title: "VERA user study protocol (two-condition quiz + TAM)"
  slug: user-study-protocol
  language: en
  summary: |
    Within-subject, two-condition quiz: six questions answered from the run's
    raw artifacts, then six matched questions answered from the dashboard.
    Produces the paired quality and time data behind the paper's claim, plus
    a TAM questionnaire as a secondary perception measure.
  audience: [human]
last_reviewed: "2026-08-13"
---

# VERA user study protocol

**Goal.** Measure whether a user answers factual questions about a completed
evaluation **more correctly and faster** with the dashboard than from the raw
result files an engineer would hand over. Output: per-item correctness
(validated server-side) and time, paired within participant, for n >= 12.

## Two-condition design (the current protocol)

- **Within-subject, fixed condition order**: every participant answers six
  questions in the *baseline* condition first (raw artifacts only), then six
  in the *dashboard* condition. The order is fixed by design decision; the
  learning threat is mitigated by the matched sets below and declared in the
  paper's threats section.
- **Two matched six-item sets (A and B)**: same question types, different
  named targets, both answerable in both conditions from the same snapshot.
  The server assigns which set lands in which phase (the session's `arm`,
  alternating by participant number), so content learning between phases is
  neutralised across the sample.
- **Baseline materials**: the study page shows the run's raw files in-page
  (parsed `benchmark_run.yaml`, the harness provenance log, paginated
  `raw_outputs.jsonl`). No dashboard access exists during part 1.
- **Symmetric access**: in part 2, each question's button deep-links to the
  view holding the answer (`?run=` summary, `?req=` requirement drawer,
  `?details=1` harness log; T8 links to `/launch`). This mirrors the baseline
  tabs: both conditions start one click from the right material, and a link
  selects a view, never an answer. Time stays app-measured in both parts.
- **The six pairs** (set A / set B): weakest vs second-weakest requirement;
  score + CI of a named requirement (two different targets); fallback
  benchmarks vs contributing benchmarks of a named requirement; count of
  requirements evaluated vs count of benchmarks executed; triage counts vs
  band counts; reach a raw output of a named benchmark (two targets, verdict
  `unverified`, audited manually).
- **Epilogue (non-comparative)**: T8, launch a run through the wizard. It
  feeds the operability claim and is excluded from the paired comparison.
- **TAM questionnaire**: kept, reported as a secondary perception measure.

**Analysis** (`scripts/analyze_user_study.py --quiz data/user_study/quiz.csv`):
per-participant correct counts and median times per condition; exact two-sided
Wilcoxon signed-rank on the paired deltas (stdlib, sign-permutation DP); exact
McNemar per pair; a gave-up or timed-out item censors its pair for the time
comparison and counts as incorrect for quality. LaTeX rows are emitted for the
paper's tables.

**Compliance note (webapp vs Microsoft Forms).** The webapp is the primary
instrument because it gives monotonic per-question timing and server-side
validation. It matches an internal Microsoft Forms on the points that matter:
no name, employer, IP or free-text identity field is stored; participants are
identified by a server-assigned code (P1, P2, ...); every profile question is
a closed list; results are reported in aggregate only. Invitation tracking
(who was invited, reminder dates, response rate) lives in a private
spreadsheet OUTSIDE the application: sends are tracked, responses are not.

**Fallback: Microsoft Forms.** If compliance declines the webapp, rebuild the
quiz in an internal MS Forms: one section per part (back navigation locked),
the six baseline questions with screenshots of the raw files, the six
dashboard questions with a link to the deployment, timing per section from
Forms timestamps (coarser than per-question), answers scored offline against
the same snapshotted key. The question bank and scoring key are this
document plus the answer-key JSON of the pinned run.

## Legacy protocol (single-condition reading tasks)

The eight-task reading protocol below produced the earlier RQ1 design and
stays documented because the T1-T8 task ids, the facilitated variant and the
frozen `sessions.csv` schema still exist in the code and tests.

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
| `GET /api/v1/study/export.csv` | `sessions.csv` | `participant,role,task_id,completed,assisted,seconds,notes` (frozen, T1-T8 rows only) |
| `GET /api/v1/study/export_survey.csv` | `survey.csv` | `participant,role,ai_experience,aiact_familiarity,seniority,locale,tasks_submitted,item,value,comment` |
| `GET /api/v1/study/export_quiz.csv` | `quiz.csv` | `participant,role,ai_experience,aiact_familiarity,seniority,locale,arm,condition,set,pair,item,completed,verdict,client_seconds,server_seconds` |

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
