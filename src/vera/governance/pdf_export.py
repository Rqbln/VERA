"""Signed audit PDF export (MVP3).

Renders a run's compliance picture — COMPL-AI scores, Trust Factor, declarative forms — to a PDF
and embeds a sha256 self-attestation (the same digest scheme as :func:`sign_artifact`).

NOTE (flagged to the operator): this is a *verifiable integrity digest*, NOT a qualified eIDAS
electronic signature or an RFC 3161 trusted timestamp. Production audit exports need a real external
TSA and managed signing key (Cosign/OpenBao). WeasyPrint (cairo/pango) is an optional dependency:
when absent, :func:`render_audit_pdf` returns ``None`` and the API responds 501.
"""

from __future__ import annotations

import html
from datetime import UTC, datetime
from typing import Any

from vera.governance.signing import sign_artifact
from vera.store.redis_run import RunRecord


def weasyprint_available() -> bool:
    try:
        import weasyprint  # noqa: F401

        return True
    except Exception:
        return False


def _row(cells: list[str], header: bool = False) -> str:
    tag = "th" if header else "td"
    return "<tr>" + "".join(f"<{tag}>{c}</{tag}>" for c in cells) + "</tr>"


def _hitl_rows(hitl: list[dict[str, Any]] | None) -> str:
    """One row per HITL requirement (N01/N02): status, reviews done/total, avg Likert,
    per-criterion means, and truncated comments. Renders pending rows when no data."""
    hitl = hitl or []
    rows = ""
    for requirement in ("N01", "N02"):
        tasks = [t for t in hitl if t.get("requirement") == requirement]
        done = [t for t in tasks if t.get("status") == "done" and t.get("likert_score") is not None]
        status = "reviewed" if done else ("queued" if tasks else "pending")
        avg = f"{sum(int(t['likert_score']) for t in done) / len(done):.2f}" if done else "—"
        crit_sums: dict[str, list[int]] = {}
        for t in done:
            for name, value in (t.get("criteria") or {}).items():
                crit_sums.setdefault(str(name), []).append(int(value))
        criteria = (
            "; ".join(
                f"{html.escape(k)}: {sum(v) / len(v):.1f}" for k, v in sorted(crit_sums.items())
            )
            or "—"
        )
        # Truncate the raw text first, then escape: truncating escaped text could cut an
        # entity (e.g. "&amp;") mid-string and emit malformed HTML.
        raw_comments = " / ".join(str(t.get("comment")) for t in done if t.get("comment"))
        clipped = raw_comments[:200] + ("…" if len(raw_comments) > 200 else "")
        comments = html.escape(clipped) or "—"
        rows += _row([requirement, status, f"{len(done)}/{len(tasks)}", avg, criteria, comments])
    return rows


def build_audit_html(
    rec: RunRecord,
    forms: dict[str, Any] | None = None,
    hitl: list[dict[str, Any]] | None = None,
) -> str:
    forms = forms or {}
    generated = datetime.now(UTC).isoformat()
    sig = sign_artifact(
        {
            "run_id": rec.run_id,
            "scores": rec.aggregate_scores or {},
            "catalog_version": rec.catalog_version,
        }
    )

    score_rows = ""
    for rid in sorted((rec.complai_scores or {}).keys()):
        row = rec.complai_scores[rid]
        if not isinstance(row, dict):
            continue
        score = row.get("score")
        lo = row.get("score_ci_lower")
        hi = row.get("score_ci_upper")
        has_ci = isinstance(lo, (int, float)) and isinstance(hi, (int, float))
        ci = f"[{lo:.3f}, {hi:.3f}]" if has_ci else "—"
        score_txt = f"{score:.3f}" if isinstance(score, (int, float)) else "—"
        score_rows += _row([rid, score_txt, ci])

    tf = rec.trust_factor or {}
    tf_line = (
        f"<p><strong>Trust Factor:</strong> {tf.get('score')} / 100 ({tf.get('band')})</p>"
        if tf
        else ""
    )

    hitl_header = _row(
        ["Requirement", "Status", "Reviews", "Avg Likert", "Criteria (mean)", "Comments"],
        header=True,
    )
    hitl_table = f"<table>{hitl_header}{_hitl_rows(hitl)}</table>"

    form_rows = ""
    for fid in ("N03", "N04", "N05", "N06"):
        f = forms.get(fid, {})
        status = "completed" if f.get("completed") else "pending"
        fields = "; ".join(
            f"{html.escape(str(k))}: {html.escape(str(v))}"
            for k, v in (f.get("fields") or {}).items()
        )
        form_rows += _row([fid, status, fields or "—"])

    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
  body {{ font-family: sans-serif; font-size: 11px; color: #18181b; }}
  h1 {{ font-size: 18px; }} h2 {{ font-size: 13px; margin-top: 18px; }}
  table {{ border-collapse: collapse; width: 100%; margin-top: 6px; }}
  th, td {{ border: 1px solid #d4d4d8; padding: 4px 6px; text-align: left; }}
  th {{ background: #f4f4f5; }}
  .sig {{ margin-top: 20px; font-family: monospace; font-size: 9px; color: #52525b;
          border-top: 1px solid #d4d4d8; padding-top: 8px; }}
</style></head><body>
  <h1>VERA Compliance Audit Export</h1>
  <p><strong>Run:</strong> {html.escape(rec.run_id)}<br>
     <strong>Model:</strong> {html.escape(rec.model_id)}<br>
     <strong>Lifecycle:</strong> {html.escape(rec.lifecycle_stage)} ·
     <strong>Catalog:</strong> {html.escape(rec.catalog_version or '—')}<br>
     <strong>Git SHA:</strong> {html.escape(rec.git_sha)}</p>
  {tf_line}
  <h2>COMPL-AI measurable requirements (R01–R12)</h2>
  <table>{_row(['Requirement', 'Score', '95% CI'], header=True)}
    {score_rows or _row(['—', '—', '—'])}</table>
  <h2>Human review (N01–N02, HITL)</h2>
  {hitl_table}
  <h2>Declarative requirements (N03–N06)</h2>
  <table>{_row(['Form', 'Status', 'Fields'], header=True)}{form_rows}</table>
  <div class="sig">
    Generated {generated}<br>
    Integrity digest: {sig['digest']} (key_id={sig['key_id']}, algo={sig['algo']})<br>
    NOTE: sha256 self-attestation — not a qualified eIDAS signature / RFC 3161 timestamp.
  </div>
</body></html>"""


def render_audit_pdf(
    rec: RunRecord,
    forms: dict[str, Any] | None = None,
    hitl: list[dict[str, Any]] | None = None,
) -> bytes | None:
    """Return PDF bytes, or None when WeasyPrint is unavailable (lite installs)."""
    if not weasyprint_available():
        return None
    import weasyprint

    html_doc = build_audit_html(rec, forms, hitl)
    return weasyprint.HTML(string=html_doc).write_pdf()
