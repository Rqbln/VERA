"""Aggregate the RQ1 user-study CSV (docs/USER_STUDY_PROTOCOL.md) into paper numbers.

Usage: python scripts/analyze_user_study.py [data/user_study/sessions.csv]

Prints per-task completion rate, assisted rate, median time and IQR, an overall
summary, and the LaTeX rows for the paper's RQ1 table.
"""

from __future__ import annotations

import csv
import statistics
import sys
from collections import defaultdict
from pathlib import Path

TASKS = [f"T{i}" for i in range(1, 9)]


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


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/user_study/sessions.csv")
    if not path.exists():
        print(f"no data at {path} — run the sessions first (docs/USER_STUDY_PROTOCOL.md)")
        return 2
    rows = load_rows(path)
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
