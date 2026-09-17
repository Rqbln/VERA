#!/usr/bin/env python3
"""Check a build of main.tex against the ICSE 2027 SEIP constraints.

Reads what the LaTeX run left behind (the .aux registrations written by
support/preamble.tex, the .log and the .pdf) and reports:

* page limits: body (title page to the end of Section X) and total with references;
* the page budget of every section and subsection, measured from saved positions;
* placeholders still in the text (\\tbd, \\parplan, \\decision, \\todo);
* tables built from vera-foundry's smoke results tree;
* numbers and phrases of the APSEC paper that must not reappear (support/apsec_guard.txt);
* undefined references and citations, overfull boxes, paper size, font embedding.

In draft and clean mode every finding is a warning. With --strict (make
submit) any finding fails the build. Standard library only.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent  # manuscript/
BODY_LIMIT = 10
TOTAL_LIMIT = 12
LETTER_PT = (612, 792)


# --------------------------------------------------------------------------- aux
def _groups(text: str, pos: int, count: int) -> tuple[list[str], int]:
    """Read `count` brace groups starting at text[pos:], honouring nesting."""
    out = []
    for _ in range(count):
        while pos < len(text) and text[pos] in " \t\n":
            pos += 1
        if pos >= len(text) or text[pos] != "{":
            raise ValueError("expected a brace group")
        depth, start = 0, pos
        while pos < len(text):
            ch = text[pos]
            if ch == "\\":
                pos += 2
                continue
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    out.append(text[start + 1 : pos])
                    pos += 1
                    break
            pos += 1
    return out, pos


def macro_calls(text: str, name: str, nargs: int) -> list[list[str]]:
    calls = []
    for m in re.finditer(re.escape("\\" + name) + r"(?![A-Za-z@])", text):
        try:
            args, _ = _groups(text, m.end(), nargs)
        except ValueError:
            continue
        calls.append(args)
    return calls


@dataclass
class Unit:
    key: str
    level: str
    title: str
    budget: float
    contribs: str
    owners: str
    roadmap: float
    next: str | None = None
    stats: tuple[int, int, int] = (0, 0, 0)


@dataclass
class Build:
    positions: dict[str, tuple[int, int, int]] = field(default_factory=dict)  # key -> x, y, abspage
    abspages: dict[str, int] = field(default_factory=dict)
    geom: tuple[int, int, int, int] | None = None
    units: list[Unit] = field(default_factory=list)
    totals: tuple[int, int, int] = (0, 0, 0)
    tbds: list[list[str]] = field(default_factory=list)
    decisions: list[list[str]] = field(default_factory=list)
    plans: list[list[str]] = field(default_factory=list)
    floats: list[list[str]] = field(default_factory=list)


def read_aux(aux: Path) -> Build:
    text = aux.read_text(encoding="utf-8", errors="replace")
    b = Build()
    for label, props in macro_calls(text, "zref@newlabel", 2):
        page = re.search(r"\\abspage\{(\d+)\}", props)
        if page:
            b.abspages[label] = int(page.group(1))
        x = re.search(r"\\posx\{(-?\d+)\}", props)
        y = re.search(r"\\posy\{(-?\d+)\}", props)
        if x and y and page:
            b.positions[label] = (int(x.group(1)), int(y.group(1)), int(page.group(1)))
    geom = macro_calls(text, "icse@geom", 4)
    if geom:
        b.geom = tuple(int(v) for v in geom[-1])  # type: ignore[assignment]
    stats = {a[0]: (int(a[1]), int(a[2]), int(a[3])) for a in macro_calls(text, "icse@regstats", 4)}
    last_sec = last_sub = None
    by_key: dict[str, Unit] = {}
    for key, level, title, budget, contribs, owners, roadmap in macro_calls(text, "icse@regunit", 7):
        u = Unit(key, level, title, float(budget), contribs, owners, float(roadmap), stats=stats.get(key, (0, 0, 0)))
        b.units.append(u)
        by_key[key] = u
        if level == "sec":
            if last_sec:
                by_key[last_sec].next = key
            if last_sub:
                by_key[last_sub].next = key
            last_sec, last_sub = key, None
        else:
            if last_sub:
                by_key[last_sub].next = key
            last_sub = key
    if "\\icse@regend" in text:
        for k in (last_sec, last_sub):
            if k:
                by_key[k].next = "bodyend"
    totals = macro_calls(text, "icse@regtotals", 3)
    if totals:
        b.totals = tuple(int(v) for v in totals[-1])  # type: ignore[assignment]
    b.tbds = macro_calls(text, "icse@regtbd", 5)
    b.decisions = macro_calls(text, "icse@regdec", 5)
    b.plans = macro_calls(text, "icse@regpar", 5)
    b.floats = macro_calls(text, "icse@regfloat", 4)
    return b


def column_position(b: Build, key: str) -> float | None:
    """Position in column units: 2 per page, plus the fraction of the column above."""
    label = f"icse:{key}"
    if label not in b.positions or not b.geom:
        return None
    x, y, page = b.positions[label]
    paper_w, paper_h, top, text_h = b.geom
    column = 1 if x > paper_w / 2 else 0
    return 2 * (page - 1) + column + (paper_h - top - y) / text_h


# --------------------------------------------------------------------------- guards
def guard_patterns(path: Path) -> list[tuple[str, re.Pattern[str]]]:
    patterns = []
    if not path.exists():
        return patterns
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("re:"):
            patterns.append((line, re.compile(line[3:])))
        else:
            literal = re.escape(line)
            # Numbers must not match inside longer numbers (4.36 in 14.365).
            prefix = r"(?<![\d.])" if line[0].isdigit() else ""
            suffix = r"(?![\d])" if line[-1].isdigit() else ""
            patterns.append((line, re.compile(prefix + literal + suffix)))
    return patterns


def strip_comments(line: str) -> str:
    return re.sub(r"(?<!\\)%.*", "", line)


def scan_sources(files: list[Path], patterns) -> list[tuple[Path, int, str, str]]:
    hits = []
    for f in files:
        for n, raw in enumerate(f.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            if "guard-ok" in raw:  # a hit reviewed by hand and accepted
                continue
            line = strip_comments(raw)
            for label, rx in patterns:
                if rx.search(line):
                    hits.append((f, n, label, raw.strip()))
    return hits


# --------------------------------------------------------------------------- log / pdf
def read_log(log: Path) -> dict[str, list[str]]:
    text = log.read_text(encoding="utf-8", errors="replace") if log.exists() else ""
    return {
        "errors": re.findall(r"^(?:!|\S+:\d+:) (.+)$", text, flags=re.M),
        "undef_refs": sorted(set(re.findall(r"Reference `([^']+)' on page", text))),
        "undef_cites": sorted(set(re.findall(r"Citation `([^']+)' on page", text))),
        "overfull": re.findall(r"^Overfull \\hbox \((\d+\.?\d*)pt too wide\)", text, flags=re.M),
        "rerun": ["rerun"] if "Rerun to get cross-references right" in text else [],
    }


def pdf_facts(pdf: Path) -> dict[str, object]:
    facts: dict[str, object] = {}
    if shutil.which("pdfinfo") and pdf.exists():
        out = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True).stdout
        size = re.search(r"Page size:\s+([\d.]+) x ([\d.]+) pts", out)
        if size:
            facts["size"] = (round(float(size.group(1))), round(float(size.group(2))))
    if shutil.which("pdffonts") and pdf.exists():
        lines = subprocess.run(["pdffonts", str(pdf)], capture_output=True, text=True).stdout.splitlines()
        if len(lines) >= 2:
            # Column spans come from the dashed rule under the header.
            spans = [(m.start(), m.end()) for m in re.finditer(r"-+", lines[1])]
            header = [lines[0][a:b].strip() for a, b in spans[:-1]] + [lines[0][spans[-1][0]:].strip()]
            rows = [{h: r[a:b].strip() for h, (a, b) in zip(header, spans)} for r in lines[2:]]
            facts["not_embedded"] = [r.get("name", "?") for r in rows if r.get("emb") == "no"]
            facts["type3"] = [r.get("name", "?") for r in rows if r.get("type", "").startswith("Type 3")]
    return facts


# --------------------------------------------------------------------------- report
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--job", help="build/<jobname>, without extension")
    ap.add_argument("--guard-only", nargs="+", metavar="FILE",
                    help="only run the APSEC guard on these source files, then exit")
    ap.add_argument("--tables", default="tables")
    ap.add_argument("--mode", default="draft", choices=["draft", "clean", "submit"])
    ap.add_argument("--strict", action="store_true", help="exit non-zero on any finding")
    ap.add_argument("--brief", action="store_true", help="pages and counts only")
    args = ap.parse_args()
    if args.guard_only:
        files = [Path(f).resolve() for f in args.guard_only]
        hits = scan_sources(files, guard_patterns(HERE / "support" / "apsec_guard.txt"))
        for f, n, label, line in hits:
            print(f"{f}:{n}  [{label}]  {line[:100]}")
        print(f"APSEC guard: {len(hits)} match(es) in {len(files)} file(s)")
        return 1 if hits else 0
    if not args.job:
        ap.error("--job is required")

    job = HERE / args.job
    aux, log, pdf = job.with_suffix(".aux"), job.with_suffix(".log"), job.with_suffix(".pdf")
    if not aux.exists():
        print(f"no build found at {aux.relative_to(HERE)}; run make draft first")
        return 2
    b = read_aux(aux)
    findings: list[str] = []

    # Pages.
    start = b.abspages.get("icse:bodystart")
    body_end = b.abspages.get("icse:bodyend")
    last = b.abspages.get("LastPage")
    body_pages = body_end - start + 1 if start and body_end else None
    total_pages = last - start + 1 if start and last else None

    def ok(value: int | None, limit: int) -> str:
        if value is None:
            return "?"
        return f"{value}/{limit} ok" if value <= limit else f"{value}/{limit} OVER"

    print(f"ICSE 2027 SEIP check  [{job.name}, mode {args.mode}]")
    print(f"  body pages {ok(body_pages, BODY_LIMIT)}   with references {ok(total_pages, TOTAL_LIMIT)}")
    if body_pages and body_pages > BODY_LIMIT:
        findings.append(f"body runs to {body_pages} pages (limit {BODY_LIMIT})")
    if total_pages and total_pages > TOTAL_LIMIT:
        findings.append(f"paper runs to {total_pages} pages with references (limit {TOTAL_LIMIT})")

    t, p, d = b.totals
    unique_decisions = len({dec[1] for dec in b.decisions})
    print(f"  placeholders: {t} TBD, {p} paragraph plans, {unique_decisions} open decisions ({d} mentions)")
    if args.mode == "submit" and (t or p or d):
        findings.append(f"{t} TBD, {p} paragraph plans and {d} open decisions remain")

    smoke = [f for f in b.floats if f[2] == "smoke"]
    awaiting = [f for f in b.floats if f[2] in ("planned", "awaiting generator", "skeleton")]
    print(f"  floats: {len(b.floats)} ({len(awaiting)} placeholders, {len(smoke)} from smoke data)")
    if smoke:
        findings.append("tables built from smoke data: " + ", ".join(f[3] for f in smoke))
    if args.mode == "submit" and awaiting:
        findings.append("placeholder floats remain: " + ", ".join(f[0] for f in awaiting))

    # Section budgets.
    if not args.brief:
        print("\n  unit                                        roadmap  budget  measured   delta")
        start_pos = 2 * (start - 1) if start else None
        first_sec = next((u for u in b.units if u.level == "sec"), None)
        if first_sec and start_pos is not None and (pos := column_position(b, first_sec.key)) is not None:
            print(f"  {'title, authors, abstract':44s} {'--':>6s}  {'--':>6s}  {(pos - start_pos) / 2:8.2f}")
        for u in b.units:
            here, there = column_position(b, u.key), column_position(b, u.next) if u.next else None
            measured = (there - here) / 2 if here is not None and there is not None else None
            name = ("" if u.level == "sec" else "  ") + u.title
            if measured is None:
                print(f"  {name[:44]:44s} {u.roadmap:6.2f}  {u.budget:6.2f}  {'?':>8s}")
                continue
            delta = measured - u.budget
            flag = "  over" if delta > 0.05 else ""
            print(f"  {name[:44]:44s} {u.roadmap:6.2f}  {u.budget:6.2f}  {measured:8.2f}  {delta:+6.2f}{flag}")
        end_pos = column_position(b, "bodyend")
        budget = sum(u.budget for u in b.units if u.level == "sec")
        roadmap = sum(u.roadmap for u in b.units if u.level == "sec")
        if end_pos is not None and start_pos is not None:
            print(f"  {'body':44s} {roadmap:6.2f}  {budget:6.2f}  {(end_pos - start_pos) / 2:8.2f}")

    # APSEC guard, on the sources that actually reach the PDF.
    # The drafting pages in support/ quote APSEC material on purpose; only the paper is scanned.
    sources = [HERE / "main.tex", *sorted((HERE / "sections").glob("*.tex")),
               *sorted((HERE / "floats").glob("*.tex")), HERE / "support" / "decisions.tex"]
    sources += [HERE / args.tables / f"{f[3]}.tex" for f in b.floats if f[2] in ("generated", "smoke")]
    sources += [HERE / "floats" / f"{f[3]}-skeleton.tex" for f in b.floats if f[2] == "skeleton"]
    hits = scan_sources([s for s in sources if s.exists()], guard_patterns(HERE / "support" / "apsec_guard.txt"))
    print(f"  APSEC guard: {len(hits)} match(es)")
    for f, n, label, line in hits[:40]:
        print(f"    {f.relative_to(HERE)}:{n}  [{label}]  {line[:90]}")
    if hits:
        findings.append(f"{len(hits)} APSEC-protected number(s) or phrase(s) in the sources")
    todos = [(f, n) for f in sources if f.exists()
             for n, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1)
             if "\\todo{" in strip_comments(line)]
    if todos and args.mode == "submit":
        findings.append(f"{len(todos)} \\todo in the sources")

    # Template conformity: class options, spacing changes, author block.
    main_src = (HERE / "main.tex").read_text(encoding="utf-8")
    cls = re.search(r"\\documentclass\[([^\]]*)\]\{([^}]*)\}", main_src)
    options = {o.strip() for o in cls.group(1).split(",")} if cls else set()
    if not cls or cls.group(2) != "IEEEtran" or not {"10pt", "conference"} <= options \
            or options & {"compsoc", "compsocconf", "a4paper", "draftcls", "draftclsnofoot"}:
        findings.append("documentclass must be [10pt,conference]{IEEEtran} without compsoc, compsocconf or a4paper")
    spacing_rx = re.compile(r"\\(vspace|vskip|baselinestretch|linespread|enlargethispage)\b"
                            r"|\\(setlength|addtolength)\{?\\(textfloatsep|floatsep|intextsep|dbltextfloatsep|dblfloatsep"
                            r"|abovecaptionskip|belowcaptionskip|textheight|textwidth|columnsep|parskip|topmargin)\b")
    preamble = HERE / "support" / "preamble.tex"
    spacing = [(f, n, raw.strip()) for f in [HERE / "main.tex", preamble, *sources] if f.exists()
               for n, raw in enumerate(f.read_text(encoding="utf-8").splitlines(), 1)
               if spacing_rx.search(strip_comments(raw))]
    spacing = list(dict.fromkeys(spacing))
    print(f"  template: {'IEEEtran 10pt conference' if cls else 'no documentclass found'}, "
          f"{len(spacing)} spacing change(s)")
    for f, n, line in spacing[:10]:
        print(f"    {f.relative_to(HERE)}:{n}  {line[:90]}")
    if spacing and args.mode == "submit":
        findings.append(f"{len(spacing)} spacing change(s); the call warns they may lead to desk rejection")
    authors = HERE / "authors.tex"
    if args.mode == "submit":
        if not authors.exists():
            findings.append("authors.tex is missing: SEIP reviews are not anonymous")
        elif "provisional" in authors.read_text(encoding="utf-8").lower():
            findings.append("authors.tex is still marked provisional")

    # Log and PDF.
    lg = read_log(log)
    print(f"  LaTeX: {len(lg['errors'])} error(s), {len(lg['undef_refs'])} undefined reference(s), "
          f"{len(lg['undef_cites'])} undefined citation(s), {len(lg['overfull'])} overfull box(es)")
    for kind in ("errors", "undef_refs", "undef_cites"):
        if lg[kind]:
            findings.append(f"{kind.replace('_', ' ')}: " + ", ".join(lg[kind][:8]))
    big = [w for w in lg["overfull"] if float(w) > 2]
    if big and not args.brief:
        print(f"    overfull by more than 2pt: {', '.join(big[:10])}")
    if big and args.mode == "submit":
        findings.append(f"{len(big)} overfull box(es) wider than 2pt")

    facts = pdf_facts(pdf)
    if "size" in facts:
        size = facts["size"]
        print(f"  PDF: {size[0]}x{size[1]} pt ({'US letter' if size == LETTER_PT else 'NOT US letter'}), "
              f"fonts not embedded: {len(facts.get('not_embedded', []))}, Type 3 fonts: {len(facts.get('type3', []))}")
        if size != LETTER_PT:
            findings.append(f"paper size {size} is not US letter")
        if facts.get("not_embedded"):
            findings.append("fonts not embedded: " + ", ".join(facts["not_embedded"]))  # type: ignore[arg-type]

    if not args.brief and b.tbds:
        print(f"\n  TBD ({len(b.tbds)})")
        for unit, source, owner, due, what in b.tbds:
            print(f"    [{source}] {what}  ({owner}, {due}; {unit})")
    if not args.brief and b.decisions:
        print(f"\n  open decisions ({len({dec[1] for dec in b.decisions})} ids, {len(b.decisions)} mentions)")
        seen: dict[str, list[str]] = {}
        for unit, ident, owner, due, question in b.decisions:
            if ident not in seen:
                seen[ident] = [unit]
                print(f"    {ident} {question}  ({owner}, by {due})")
            else:
                seen[ident].append(unit)

    if findings:
        print("\n  findings:")
        for f in findings:
            print(f"    - {f}")
    if args.strict and findings:
        print("\nFAILED: the build is not submittable.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
