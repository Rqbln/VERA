from __future__ import annotations

from vera.governance.pdf_export import build_audit_html, render_audit_pdf, weasyprint_available
from vera.store.redis_run import RunRecord


def _rec() -> RunRecord:
    return RunRecord(
        run_id="pdf-run",
        status="completed",
        model_id="ollama/phi3:mini",
        catalog_version="mvp2-v1",
        git_sha="abc1234",
        aggregate_scores={"R02": 0.8},
        complai_scores={"R02": {"score": 0.8, "score_ci_lower": 0.7, "score_ci_upper": 0.9}},
        trust_factor={"score": 75.0, "band": "green", "components": {}},
    )


def test_build_audit_html_contains_digest_and_disclaimer():
    html = build_audit_html(_rec(), {"N03": {"completed": True, "fields": {"kwh": "10"}}})
    assert "VERA Compliance Audit Export" in html
    assert "sha256:" in html  # integrity digest embedded
    assert "not a qualified eIDAS" in html  # honest disclaimer
    assert "R02" in html and "0.800" in html


def test_render_pdf_or_graceful_none():
    out = render_audit_pdf(_rec())
    if weasyprint_available():
        assert out is not None and out[:4] == b"%PDF"
    else:
        assert out is None


def test_build_audit_html_includes_hitl_rows():
    hitl = [
        {
            "requirement": "N01",
            "status": "done",
            "likert_score": 4,
            "criteria": {"faithfulness": 4, "completeness": 5, "clarity": 3, "actionability": 4},
            "comment": "clear rationale",
        }
    ]
    html = build_audit_html(_rec(), None, hitl)
    assert "Human review (N01–N02, HITL)" in html
    assert "reviewed" in html and "1/1" in html and "4.00" in html
    assert "faithfulness: 4.0" in html and "completeness: 5.0" in html
    assert "clear rationale" in html
    # N02 has no tasks -> rendered as a pending row, never omitted
    assert "N02" in html and "pending" in html


def test_build_audit_html_truncates_comment_before_escaping():
    # A '&' sitting exactly at the 200-char raw boundary must escape to a full "&amp;",
    # never be cut mid-entity (which truncating *after* escaping would do).
    hitl = [
        {
            "requirement": "N01",
            "status": "done",
            "likert_score": 4,
            "criteria": {"clarity": 4},
            "comment": "z" * 199 + "&data",
        }
    ]
    html = build_audit_html(_rec(), None, hitl)
    assert "&amp;" in html  # entity kept whole
    assert "z&d" not in html and "z&<" not in html  # no bare '&' from a cut entity


def test_build_audit_html_without_hitl_backward_compatible():
    html = build_audit_html(_rec(), {"N03": {"completed": True, "fields": {"kwh": "10"}}})
    assert "Human review (N01–N02, HITL)" in html
    assert html.count("pending") >= 2  # N01 and N02 rows render as pending
