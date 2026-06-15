from __future__ import annotations

from raip.schemas.run_payload import RunCreateRequest
from raip.tasks.eval import _benchmarks_for_requirements, _resolve_benchmarks


def test_expand_requirement_to_benchmarks():
    bms = _benchmarks_for_requirements(["R01"])
    assert "r01_robustness" in bms and "mmlu_robust" in bms and "boolq_contrast" in bms


def test_explicit_benchmarks_passthrough():
    req = RunCreateRequest(model_id="ollama/x", benchmarks=["mmlu"], complai_requirements=["R06"])
    benchmarks, requested = _resolve_benchmarks(req)
    assert benchmarks == ["mmlu"]
    assert requested == ["R06"]


def test_requirements_expand_when_no_benchmarks():
    # The launch wizard sends requirements and no benchmarks; they must expand so the run evaluates.
    req = RunCreateRequest(model_id="ollama/x", complai_requirements=["R01", "R12"])
    benchmarks, requested = _resolve_benchmarks(req)
    assert benchmarks  # non-empty
    assert "r01_robustness" in benchmarks
    assert requested == ["R01", "R12"]


def test_recommended_default_is_inference_set():
    # Both empty (legacy recommended): default to the inference requirements, no dataset corpus.
    req = RunCreateRequest(model_id="ollama/x")
    benchmarks, requested = _resolve_benchmarks(req)
    assert "R01" in requested and "R03" not in requested  # dataset reqs excluded without corpus
    assert benchmarks


def test_dataset_requirements_included_with_corpus():
    req = RunCreateRequest(model_id="ollama/x", dataset_corpus=["some text"])
    _, requested = _resolve_benchmarks(req)
    assert "R03" in requested
