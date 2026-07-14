"""Policy-comparison primitives: uniform vs signed-catalog vs alternative weights."""

from __future__ import annotations

from vera.dashboard.score_bands import ScoreBands
from vera.stats.policy_compare import compare_policies, point_score, uniform_weights


def test_uniform_equals_catalog_when_weights_are_uniform():
    means = {"a": 0.9, "b": 0.5, "c": 0.7}
    catalog = {"a": 1 / 3, "b": 1 / 3, "c": 1 / 3}
    assert point_score(means, catalog) == point_score(means, uniform_weights(means))


def test_non_uniform_weights_diverge():
    means = {"a": 1.0, "b": 0.0}
    assert point_score(means, {"a": 0.5, "b": 0.5}) == 0.5
    assert point_score(means, {"a": 0.8, "b": 0.2}) == 0.8


def test_renormalizes_over_shared_benchmarks_only():
    # A weighted benchmark with no cached mean is excluded, never defaulted.
    means = {"a": 1.0}
    assert point_score(means, {"a": 0.5, "missing": 0.5}) == 1.0
    assert point_score({}, {"a": 1.0}) is None


def test_flip_detected_when_bands_differ():
    # Same cached means, green under one defensible policy, red under another.
    means = {"benign": 1.0, "adversarial": 0.0}
    policies = {
        "uniform": {"benign": 0.5, "adversarial": 0.5},  # 0.50 -> orange
        "capability-first": {"benign": 0.9, "adversarial": 0.1},  # 0.90 -> green
        "security-first": {"benign": 0.1, "adversarial": 0.9},  # 0.10 -> red
    }
    result = compare_policies(means, policies, ScoreBands())
    assert result["uniform"]["band"] == "orange"
    assert result["capability-first"]["band"] == "green"
    assert result["security-first"]["band"] == "red"
    assert result["_flip"]["flip"] is True


def test_no_flip_when_all_policies_agree():
    means = {"a": 0.95, "b": 0.85}
    policies = {
        "uniform": uniform_weights(means),
        "skewed": {"a": 0.9, "b": 0.1},
    }
    assert compare_policies(means, policies)["_flip"]["flip"] is False
