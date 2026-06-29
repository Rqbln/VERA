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
