from __future__ import annotations

from typing import Any, Literal

from raip.dashboard.score_bands import ScoreBands, load_score_bands

TriageStatus = Literal["failed", "fallback", "uncovered", "ok", "na"]

COMPLAI_META: dict[str, dict[str, str]] = {
    "R01": {
        "name": "Robustness predictability",
        "rationale": "Stability under perturbation and contrast sets.",
        "principle": "robustness_safety",
        "aiact": "Art. 15",
    },
    "R02": {
        "name": "Cyber resilience",
        "rationale": "Resistance to jailbreaks, injections, and adversarial prompts.",
        "principle": "robustness_safety",
        "aiact": "Art. 15",
    },
    "R03": {
        "name": "Training data adequacy",
        "rationale": "Dataset quality, representativeness, and documentation.",
        "principle": "privacy_data",
        "aiact": "Art. 10",
    },
    "R04": {
        "name": "Copyright compliance",
        "rationale": "Training corpus licensing and attribution checks.",
        "principle": "privacy_data",
        "aiact": "Art. 10",
    },
    "R05": {
        "name": "Privacy protection",
        "rationale": "PII leakage and memorization probes on data.",
        "principle": "privacy_data",
        "aiact": "Art. 10",
    },
    "R06": {
        "name": "Capabilities",
        "rationale": "Task accuracy across capability benchmarks.",
        "principle": "transparency",
        "aiact": "Art. 15",
    },
    "R07": {
        "name": "Calibration / interpretability",
        "rationale": "Expected calibration error and confidence alignment.",
        "principle": "transparency",
        "aiact": "Art. 13",
    },
    "R08": {
        "name": "AI disclosure",
        "rationale": "Self-disclosure when probed as non-human.",
        "principle": "transparency",
        "aiact": "Art. 13",
    },
    "R09": {
        "name": "Watermark / traceability",
        "rationale": "Detectability of statistical or embedded watermarks.",
        "principle": "transparency",
        "aiact": "Art. 50",
    },
    "R10": {
        "name": "Representation bias",
        "rationale": "Stereotype and representation gaps across groups.",
        "principle": "fairness",
        "aiact": "Art. 10",
    },
    "R11": {
        "name": "Fairness",
        "rationale": "Disparate impact on protected attributes.",
        "principle": "fairness",
        "aiact": "Art. 10",
    },
    "R12": {
        "name": "Toxicity / harmful content",
        "rationale": "Refusal rate and detoxified harmful generations.",
        "principle": "fairness",
        "aiact": "Art. 10",
    },
}

ALL_MEASURABLE = tuple(f"R{i:02d}" for i in range(1, 13))
PILOTE_MARKERS = frozenset({"pilote_v1", "raip-mvp1-pilote"})


def is_pilote_catalog(catalog_version: str | None) -> bool:
    """True when a catalog version is a pilot marker (excluded from compliance views)."""
    return (catalog_version or "").strip().lower() in PILOTE_MARKERS


def is_pilote_run(catalog_version: str | None, payload: dict[str, Any] | None) -> bool:
    if is_pilote_catalog(catalog_version):
        return True
    if payload:
        impl = str(payload.get("implementation") or "").lower()
        if impl in PILOTE_MARKERS:
            return True
    return False


def _fallback_benchmarks(
    req_id: str,
    complai_scores: dict[str, Any],
    provenance: list[dict[str, Any]],
) -> list[str]:
    contributing = set(complai_scores.get(req_id, {}).get("contributing_benchmarks") or [])
    out: list[str] = []
    for row in provenance:
        bid = str(row.get("benchmark_id", ""))
        if bid in contributing and row.get("fallback") in (True, "yes", "true"):
            out.append(bid)
    return out


def _na_requirements(raw_outputs: list[dict[str, Any]]) -> set[str]:
    return {
        str(r.get("requirement"))
        for r in raw_outputs
        if r.get("status") == "NA" and r.get("requirement")
    }


def triage_status(
    req_id: str,
    *,
    run_status: str,
    requested: list[str],
    complai_scores: dict[str, Any],
    provenance: list[dict[str, Any]],
    raw_outputs: list[dict[str, Any]],
    bands: ScoreBands | None = None,
) -> TriageStatus:
    bands = bands or load_score_bands()
    na_reqs = _na_requirements(raw_outputs)
    if req_id in na_reqs:
        return "na"

    score_row = complai_scores.get(req_id)
    if req_id in requested and not score_row:
        return "uncovered"

    if not score_row:
        return "na"

    score = score_row.get("score")
    band = bands.band(float(score) if score is not None else None)
    if run_status == "failed" or band == "red":
        return "failed"

    if _fallback_benchmarks(req_id, complai_scores, provenance):
        return "fallback"

    return "ok"


def triage_priority(status: TriageStatus) -> int:
    return {"failed": 0, "fallback": 1, "uncovered": 2, "ok": 3, "na": 4}[status]


def build_requirement_rows(
    *,
    run_status: str,
    requested: list[str],
    complai_scores: dict[str, Any],
    provenance: list[dict[str, Any]],
    raw_outputs: list[dict[str, Any]],
    filter_ids: list[str] | None = None,
    bands: ScoreBands | None = None,
) -> list[dict[str, Any]]:
    bands = bands or load_score_bands()
    ids = filter_ids or list(ALL_MEASURABLE)
    rows: list[dict[str, Any]] = []
    for req_id in ids:
        meta = COMPLAI_META.get(req_id, {})
        cs = complai_scores.get(req_id) or {}
        status = triage_status(
            req_id,
            run_status=run_status,
            requested=requested,
            complai_scores=complai_scores,
            provenance=provenance,
            raw_outputs=raw_outputs,
            bands=bands,
        )
        score = cs.get("score")
        rows.append(
            {
                "id": req_id,
                "name": meta.get("name", req_id),
                "rationale": meta.get("rationale", ""),
                "principle": meta.get("principle", ""),
                "aiact": meta.get("aiact", ""),
                "triage": status,
                "score": score,
                "score_ci_lower": cs.get("score_ci_lower"),
                "score_ci_upper": cs.get("score_ci_upper"),
                "bootstrap_n": cs.get("bootstrap_n"),
                "contributing_benchmarks": cs.get("contributing_benchmarks") or [],
                "fallback_benchmarks": _fallback_benchmarks(req_id, complai_scores, provenance),
                "band": bands.band(float(score) if score is not None else None),
            }
        )
    rows.sort(key=lambda r: (triage_priority(r["triage"]), r["id"]))
    return rows
