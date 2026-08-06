"""Aggregate the user-study CSVs (docs/USER_STUDY_PROTOCOL.md) into paper numbers.

Usage:
  python scripts/analyze_user_study.py [data/user_study/sessions.csv]
         [--survey data/user_study/survey.csv]
         [--exclude P1,P2] [--min-tasks 8] [--comments]

Prints per-task completion and timing, and — when a survey file is given — the
participant profile table and the TAM (perceived usefulness / perceived ease of
use) table, with the LaTeX rows for both.
"""

from __future__ import annotations

import argparse
import csv
import statistics
from collections import defaultdict
from pathlib import Path

TASKS = [f"T{i}" for i in range(1, 9)]

PU_ITEMS = ("PU1", "PU2", "PU3", "PU4")
PEOU_ITEMS = ("PEOU1", "PEOU2", "PEOU3", "PEOU4")
SURVEY_ITEMS = PU_ITEMS + PEOU_ITEMS

ITEM_SHORT = {
    "PU1": "Faster evaluation",
    "PU2": "Understand failures",
    "PU3": "Justify a decision",
    "PU4": "Better evaluation quality",
    "PEOU1": "Clear interface",
    "PEOU2": "Found information",
    "PEOU3": "Launch a run alone",
    "PEOU4": "Little learning effort",
}
ROLE_LABEL = {
    "compliance_officer": "Compliance officer",
    "risk_manager": "Risk manager",
    "legal": "Legal",
    "audit": "Audit",
    "ai_researcher": "AI researcher",
    "other_non_ml": "Other (non-ML)",
}
AIEXP_LABEL = {
    "none": "None",
    "user": "Uses AI tools",
    "reviewer": "Reviews models",
    "builder": "Builds models",
}
AIACT_LABEL = {
    "none": "None",
    "heard": "Heard of it",
    "working": "Working",
    "expert": "Regular",
}
SENIORITY_LABEL = {"lt2": "<2", "2to5": "2--5", "6to10": "6--10", "gt10": ">10"}


def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8") as f:
        return [row for row in csv.DictReader(f) if row.get("task_id")]


def summarize(rows: list[dict[str, str]]) -> dict[str, dict[str, object]]:
    by_task: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        by_task[row["task_id"].strip()].append(row)
    out: dict[str, dict[str, object]] = {}
    for task in TASKS:
        entries = by_task.get(task, [])
        if not entries:
            continue
        done = [e for e in entries if e["completed"].strip().lower() == "yes"]
        unassisted = [e for e in done if e["assisted"].strip().lower() != "yes"]
        seconds = sorted(
            float(e["seconds"]) for e in done if str(e.get("seconds", "")).strip()
        )
        stats: dict[str, object] = {
            "n": len(entries),
            "completed": len(done),
            "unassisted": len(unassisted),
        }
        if seconds:
            stats["median_s"] = statistics.median(seconds)
            if len(seconds) >= 4:
                q = statistics.quantiles(seconds, n=4)
                stats["iqr"] = (q[0], q[2])
            else:
                stats["iqr"] = (seconds[0], seconds[-1])
        out[task] = stats
    return out


# ── Survey (TAM) ─────────────────────────────────────────────────────────────────────
def load_survey_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8") as f:
        return [row for row in csv.DictReader(f) if row.get("item")]


def survey_matrix(rows: list[dict[str, str]]) -> dict[str, dict[str, int]]:
    """participant -> {item: value}; blank values are skipped entirely."""
    matrix: dict[str, dict[str, int]] = defaultdict(dict)
    for row in rows:
        value = str(row.get("value", "")).strip()
        if not value:
            continue
        matrix[row["participant"].strip()][row["item"].strip()] = int(float(value))
    return dict(matrix)


def profile_table(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    """One entry per participant, in P-number order."""
    seen: dict[str, dict[str, str]] = {}
    for row in rows:
        pid = row["participant"].strip()
        if pid not in seen:
            seen[pid] = {
                "participant": pid,
                "role": row.get("role", ""),
                "ai_experience": row.get("ai_experience", ""),
                "aiact_familiarity": row.get("aiact_familiarity", ""),
                "seniority": row.get("seniority", ""),
                "locale": row.get("locale", ""),
                "tasks_submitted": row.get("tasks_submitted", "0"),
            }
    return sorted(seen.values(), key=lambda p: int(p["participant"].lstrip("P") or 0))


def item_stats(matrix: dict[str, dict[str, int]], items) -> dict[str, dict[str, float]]:
    out: dict[str, dict[str, float]] = {}
    for item in items:
        values = [m[item] for m in matrix.values() if item in m]
        if not values:
            continue
        out[item] = {
            "n": len(values),
            "mean": statistics.mean(values),
            "sd": statistics.stdev(values) if len(values) > 1 else 0.0,
            "median": statistics.median(values),
        }
    return out


def cronbach_alpha(matrix: dict[str, dict[str, int]], items) -> float | None:
    """Standard alpha; None when the sample is too small or has no variance."""
    complete = [m for m in matrix.values() if all(i in m for i in items)]
    k = len(items)
    if len(complete) < 3 or k < 2:
        return None
    item_var = sum(statistics.variance([m[i] for m in complete]) for i in items)
    total_var = statistics.variance([sum(m[i] for i in items) for m in complete])
    if total_var == 0:
        return None
    return (k / (k - 1)) * (1 - item_var / total_var)


def construct_stats(matrix: dict[str, dict[str, int]], items) -> dict[str, object]:
    """Per-participant construct means, over participants who answered every item."""
    means = [
        statistics.mean([m[i] for i in items])
        for m in matrix.values()
        if all(i in m for i in items)
    ]
    if not means:
        return {"n": 0, "mean": None, "sd": None, "median": None, "alpha": None}
    return {
        "n": len(means),
        "mean": round(statistics.mean(means), 4),
        "sd": round(statistics.stdev(means), 4) if len(means) > 1 else 0.0,
        "median": statistics.median(means),
        "alpha": cronbach_alpha(matrix, items),
    }


def straight_liners(matrix: dict[str, dict[str, int]]) -> list[str]:
    """Participants who gave the same answer to every item they answered."""
    flagged = []
    for pid, answers in matrix.items():
        values = list(answers.values())
        if len(values) >= len(SURVEY_ITEMS) and len(set(values)) == 1:
            flagged.append(pid)
    return sorted(flagged)


def latex_profile_rows(profiles: list[dict[str, str]]) -> list[str]:
    return [
        f"    {p['participant']} & {ROLE_LABEL.get(p['role'], p['role'])} "
        f"& {AIEXP_LABEL.get(p['ai_experience'], p['ai_experience'])} "
        f"& {AIACT_LABEL.get(p['aiact_familiarity'], p['aiact_familiarity'])} "
        f"& {SENIORITY_LABEL.get(p['seniority'], p['seniority'])} "
        f"& {p['tasks_submitted']}/8 \\\\"
        for p in profiles
    ]


def latex_tam_rows(matrix: dict[str, dict[str, int]]) -> list[str]:
    lines: list[str] = []
    for name, items in (("Perceived usefulness", PU_ITEMS), ("Perceived ease of use", PEOU_ITEMS)):
        if lines:
            lines.append("    \\midrule")
        stats = item_stats(matrix, items)
        for item in items:
            s = stats.get(item)
            if not s:
                continue
            lines.append(
                f"    {item} & {ITEM_SHORT[item]} & {s['mean']:.2f} "
                f"& {s['sd']:.2f} & {s['median']:.0f} \\\\"
            )
        c = construct_stats(matrix, items)
        if c["mean"] is not None:
            lines.append(
                f"    \\multicolumn{{2}}{{@{{}}l}}{{\\textbf{{{name}}}}} "
                f"& \\textbf{{{c['mean']:.2f}}} & {c['sd']:.2f} & {c['median']:.1f} \\\\"
            )
    return lines


def _print_survey(path: Path, exclude: set[str], min_tasks: int, show_comments: bool) -> None:
    rows = load_survey_rows(path)
    if exclude:
        rows = [r for r in rows if r["participant"].strip() not in exclude]
    if min_tasks:
        rows = [r for r in rows if int(r.get("tasks_submitted") or 0) >= min_tasks]
    profiles = profile_table(rows)
    matrix = survey_matrix(rows)
    print(f"\n=== survey: {len(profiles)} participants, {len(matrix)} answered the questionnaire")

    print("\n% LaTeX participant rows: ID & role & AI/ML exp & EU AI Act & yrs & tasks")
    for line in latex_profile_rows(profiles):
        print(line)

    print("\n% LaTeX TAM rows: item & statement & mean & SD & median")
    for line in latex_tam_rows(matrix):
        print(line)

    for name, items in (("PU", PU_ITEMS), ("PEOU", PEOU_ITEMS)):
        c = construct_stats(matrix, items)
        alpha = c["alpha"]
        alpha_txt = f"{alpha:.2f}" if isinstance(alpha, float) else "n/a (too few or no variance)"
        print(f"% {name}: mean={c['mean']} sd={c['sd']} n={c['n']} alpha={alpha_txt}")
    flagged = straight_liners(matrix)
    if flagged:
        print(f"% WARNING straight-lining (identical answers): {', '.join(flagged)}")
    if show_comments:
        print("\n=== comments (vet before sharing)")
        for p in profiles:
            comment = next(
                (r.get("comment", "") for r in rows if r["participant"].strip() == p["participant"]),
                "",
            )
            if comment:
                print(f"  {p['participant']}: {comment}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sessions", nargs="?", default="data/user_study/sessions.csv")
    parser.add_argument("--survey", default=None, help="path to survey.csv (TAM export)")
    parser.add_argument("--exclude", default="", help="comma-separated participant codes")
    parser.add_argument("--min-tasks", type=int, default=0, help="keep sessions with >= N tasks")
    parser.add_argument("--comments", action="store_true", help="print free-text comments")
    args = parser.parse_args()

    path = Path(args.sessions)
    exclude = {p.strip() for p in args.exclude.split(",") if p.strip()}
    if not path.exists():
        print(f"no data at {path} — run the sessions first (docs/USER_STUDY_PROTOCOL.md)")
        return 2
    rows = load_rows(path)
    if exclude:
        rows = [r for r in rows if r["participant"].strip() not in exclude]
    participants = sorted({r["participant"].strip() for r in rows})
    summary = summarize(rows)

    print(f"participants: {len(participants)} ({', '.join(participants)})\n")
    total = sum(s["n"] for s in summary.values())
    done = sum(s["completed"] for s in summary.values())
    unassisted = sum(s["unassisted"] for s in summary.values())
    for task, s in summary.items():
        timing = (
            f"median {s['median_s']:.0f}s (IQR {s['iqr'][0]:.0f}-{s['iqr'][1]:.0f}s)"
            if "median_s" in s
            else "no timing"
        )
        print(f"  {task}: {s['completed']}/{s['n']} completed "
              f"({s['unassisted']} unassisted), {timing}")
    print(f"\noverall: {done}/{total} tasks completed, {unassisted}/{total} unassisted")

    print("\n% LaTeX rows: task & completed & unassisted & median (IQR)")
    for task, s in summary.items():
        timing = (
            f"{s['median_s']:.0f}\\,s ({s['iqr'][0]:.0f}--{s['iqr'][1]:.0f})"
            if "median_s" in s
            else "--"
        )
        print(f"    {task} & {s['completed']}/{s['n']} & {s['unassisted']}/{s['n']} "
              f"& {timing} \\\\")

    # A varying denominator across T1..T8 means someone abandoned mid-session.
    denominators = {s["n"] for s in summary.values()}
    if len(denominators) > 1:
        print(f"\n% WARNING per-task n is not constant {sorted(denominators)}: "
              "report complete sessions separately (--min-tasks 8)")

    if args.survey:
        survey_path = Path(args.survey)
        if survey_path.exists():
            _print_survey(survey_path, exclude, args.min_tasks, args.comments)
        else:
            print(f"\nno survey data at {survey_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
