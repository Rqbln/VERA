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
        f"& {p['tasks_submitted']}/13 \\\\"
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


# ── Two-condition quiz (baseline raw artifacts vs the VERA dashboard) ────────────────
QUIZ_PAIRS = ("1", "2", "3", "4", "5", "6")
PAIR_SHORT = {
    "1": "Rank a requirement by weakness",
    "2": "Score and interval of a named requirement",
    "3": "Benchmark provenance",
    "4": "Count the coverage",
    "5": "Band and verdict counts",
    "6": "Reach a raw model output",
}


def load_quiz_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8") as f:
        return [row for row in csv.DictReader(f) if row.get("item")]


def _quiz_cells(rows: list[dict[str, str]]) -> dict[str, dict[str, dict[str, object]]]:
    """participant -> pair -> condition -> {correct, seconds}; last write wins."""
    cells: dict[str, dict[str, dict[str, object]]] = defaultdict(lambda: defaultdict(dict))
    for row in rows:
        pid = row["participant"].strip()
        pair = str(row.get("pair", "")).strip()
        cond = str(row.get("condition", "")).strip()
        if pair not in QUIZ_PAIRS or cond not in ("baseline", "vera"):
            continue
        seconds_txt = str(row.get("client_seconds") or row.get("server_seconds") or "").strip()
        gave_up = str(row.get("verdict", "")).strip() in ("gave_up", "timeout")
        cells[pid][pair][cond] = {
            "correct": str(row.get("completed", "")).strip().lower() == "yes",
            "seconds": float(seconds_txt) if seconds_txt else None,
            "gave_up": gave_up,
        }
    return {p: dict(pairs) for p, pairs in cells.items()}


def paired_quality(rows: list[dict[str, str]]) -> dict[str, object]:
    """Per-participant correct counts over the pairs answered in BOTH conditions."""
    per: dict[str, dict[str, object]] = {}
    for pid, pairs in _quiz_cells(rows).items():
        both = {k: v for k, v in pairs.items() if "baseline" in v and "vera" in v}
        if not both:
            continue
        base = sum(1 for v in both.values() if v["baseline"]["correct"])
        vera = sum(1 for v in both.values() if v["vera"]["correct"])
        per[pid] = {"pairs": len(both), "baseline": base, "vera": vera, "delta": vera - base}
    return dict(sorted(per.items(), key=lambda kv: int(kv[0].lstrip("P") or 0)))


def paired_time(rows: list[dict[str, str]]) -> dict[str, object]:
    """Per-participant median seconds per condition.

    Only pairs timed in both conditions count, and a gave-up or timed-out item
    censors its pair (the cap is not a completion time).
    """
    per: dict[str, dict[str, object]] = {}
    for pid, pairs in _quiz_cells(rows).items():
        base_t, vera_t = [], []
        for v in pairs.values():
            b, w = v.get("baseline"), v.get("vera")
            if not b or not w:
                continue
            usable = (
                b["seconds"] is not None
                and w["seconds"] is not None
                and not b["gave_up"]
                and not w["gave_up"]
            )
            if usable:
                base_t.append(b["seconds"])
                vera_t.append(w["seconds"])
        if not base_t:
            continue
        mb = statistics.median(base_t)
        mv = statistics.median(vera_t)
        per[pid] = {"pairs": len(base_t), "baseline": mb, "vera": mv, "delta": mv - mb}
    return dict(sorted(per.items(), key=lambda kv: int(kv[0].lstrip("P") or 0)))


def per_pair_table(rows: list[dict[str, str]]) -> dict[str, dict[str, object]]:
    """Pair-level correctness by condition plus the discordant counts for McNemar."""
    out: dict[str, dict[str, object]] = {}
    cells = _quiz_cells(rows)
    for pair in QUIZ_PAIRS:
        n = b_only = v_only = 0
        base_ok = vera_ok = 0
        for pairs in cells.values():
            v = pairs.get(pair)
            if not v or "baseline" not in v or "vera" not in v:
                continue
            n += 1
            cb, cv = v["baseline"]["correct"], v["vera"]["correct"]
            base_ok += cb
            vera_ok += cv
            b_only += cb and not cv
            v_only += cv and not cb
        if n:
            out[pair] = {
                "n": n,
                "baseline": base_ok,
                "vera": vera_ok,
                "b": b_only,
                "c": v_only,
                "p": mcnemar_exact(b_only, v_only),
            }
    return out


def wilcoxon_exact(deltas: list[float]) -> dict[str, object]:
    """Exact two-sided Wilcoxon signed-rank test (sign-permutation distribution).

    Zeros are dropped; ties get average ranks (doubled to stay integral); the
    null distribution of W+ is built by dynamic programming over sign flips, so
    the p-value is exact at any n this study can reach. Above n=22 it falls back
    to the normal approximation with tie correction.
    """
    d = [x for x in deltas if x != 0]
    n = len(d)
    if n == 0:
        return {"n": 0, "w": 0.0, "p": 1.0}
    by_abs = sorted(range(n), key=lambda i: abs(d[i]))
    ranks2 = [0] * n  # ranks * 2, so average ranks stay integers
    i = 0
    while i < n:
        j = i
        while j + 1 < n and abs(d[by_abs[j + 1]]) == abs(d[by_abs[i]]):
            j += 1
        avg2 = (i + 1) + (j + 1)  # 2 * average rank of the tied block
        for k in range(i, j + 1):
            ranks2[by_abs[k]] = avg2
        i = j + 1
    w2 = sum(r for r, x in zip(ranks2, d, strict=True) if x > 0)
    total2 = sum(ranks2)
    if n > 22:
        mean = total2 / 2
        var = sum(r * r for r in ranks2) / 4
        z = (w2 - mean) / (var**0.5) if var else 0.0
        p = 2 * (1 - _phi(abs(z)))
        return {"n": n, "w": w2 / 2, "p": min(1.0, p)}
    # DP over achievable W+*2 values.
    counts = defaultdict(int)
    counts[0] = 1
    for r in ranks2:
        nxt = defaultdict(int)
        for s, c in counts.items():
            nxt[s] += c
            nxt[s + r] += c
        counts = nxt
    total_assignments = 2**n
    lo, hi = min(w2, total2 - w2), max(w2, total2 - w2)
    p_num = sum(c for s, c in counts.items() if s <= lo) + sum(
        c for s, c in counts.items() if s >= hi
    )
    return {"n": n, "w": w2 / 2, "p": min(1.0, p_num / total_assignments)}


def _phi(x: float) -> float:
    """Standard normal CDF via erf (math stdlib)."""
    import math

    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def mcnemar_exact(b: int, c: int) -> float:
    """Exact two-sided McNemar p-value (binomial on the discordant pairs)."""
    import math

    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    tail = sum(math.comb(n, i) for i in range(k + 1)) / 2**n
    return min(1.0, 2 * tail)


def latex_pair_rows(table: dict[str, dict[str, object]]) -> list[str]:
    lines = []
    for pair in QUIZ_PAIRS:
        s = table.get(pair)
        if not s:
            continue
        lines.append(
            f"    {pair} & {PAIR_SHORT[pair]} & {s['baseline']}/{s['n']} & "
            f"{s['vera']}/{s['n']} & {s['p']:.3f} \\\\"
        )
    return lines


def latex_paired_rows(quality: dict[str, object], time: dict[str, object]) -> list[str]:
    lines = []
    for pid, q in quality.items():
        t = time.get(pid) or {}
        tb = f"{t['baseline']:.0f}" if t else "--"
        tv = f"{t['vera']:.0f}" if t else "--"
        lines.append(
            f"    {pid} & {q['baseline']}/{q['pairs']} & {q['vera']}/{q['pairs']} & "
            f"{tb} & {tv} \\\\"
        )
    return lines


def _print_quiz(path: Path, exclude: set[str]) -> None:
    rows = load_quiz_rows(path)
    if exclude:
        rows = [r for r in rows if r["participant"].strip() not in exclude]
    quality = paired_quality(rows)
    time = paired_time(rows)
    pairs = per_pair_table(rows)
    arms = {r["participant"].strip(): r.get("arm", "") for r in rows}
    n_alpha = sum(1 for a in arms.values() if a == "alpha_first")
    print(
        f"\n=== quiz: {len(quality)} participants with paired data "
        f"({n_alpha} alpha_first, {len(arms) - n_alpha} beta_first)"
    )

    if quality:
        wq = wilcoxon_exact([q["delta"] for q in quality.values()])
        better = sum(1 for q in quality.values() if q["delta"] > 0)
        worse = sum(1 for q in quality.values() if q["delta"] < 0)
        print(
            f"quality: {better} improved / "
            f"{len(quality) - better - worse} tied / {worse} worse with the dashboard; "
            f"Wilcoxon exact p={wq['p']:.4f} (n={wq['n']})"
        )
    if time:
        wt = wilcoxon_exact([t["delta"] for t in time.values()])
        mb = statistics.median([t["baseline"] for t in time.values()])
        mv = statistics.median([t["vera"] for t in time.values()])
        print(
            f"time: median per-participant {mb:.0f}s baseline vs {mv:.0f}s dashboard; "
            f"Wilcoxon exact p={wt['p']:.4f} (n={wt['n']})"
        )

    print("\n% LaTeX pair rows: pair & task & baseline & dashboard & McNemar p")
    for line in latex_pair_rows(pairs):
        print(line)
    print("\n% LaTeX participant rows: ID & correct base & correct vera & median s base/vera")
    for line in latex_paired_rows(quality, time):
        print(line)


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
    parser.add_argument("--quiz", default=None, help="path to quiz.csv (two-condition export)")
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

    if args.quiz:
        qpath = Path(args.quiz)
        if qpath.exists():
            _print_quiz(qpath, exclude)
        else:
            print(f"no quiz data at {qpath}")
    if args.survey:
        survey_path = Path(args.survey)
        if survey_path.exists():
            _print_survey(survey_path, exclude, args.min_tasks, args.comments)
        else:
            print(f"\nno survey data at {survey_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
