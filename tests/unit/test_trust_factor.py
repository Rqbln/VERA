from __future__ import annotations

from raip.governance.trust_factor import compute_trust_factor, load_weights


def test_weights_sum_to_one():
    assert round(sum(load_weights().values()), 6) == 1.0


def test_full_signal_set():
    tf = compute_trust_factor(
        {
            "R01": {"score": 0.7},
            "R02": {"score": 0.8},
            "R05": {"score": 0.9},
            "R12": {"score": 0.6},
        }
    )
    assert tf is not None
    assert 0 <= tf["score"] <= 100
    assert tf["band"] in ("green", "orange", "red")
    assert set(tf["coverage"]) == {"R01", "R02", "R05", "R12"}


def test_partial_signals_renormalise():
    tf = compute_trust_factor({"R02": {"score": 0.5}})
    assert tf is not None
    assert tf["coverage"] == ["R02"]
    # Single available signal => weight renormalised to 1.0 => score = 50.
    assert tf["score"] == 50.0
    assert round(sum(tf["weights"].values()), 6) == 1.0


def test_no_safety_signals_returns_none():
    assert compute_trust_factor({"R06": {"score": 0.9}}) is None
    assert compute_trust_factor({}) is None


def test_custom_weights_env(monkeypatch):
    monkeypatch.setenv("RAIP_TRUST_FACTOR_WEIGHTS", '{"R02": 1.0}')
    w = load_weights()
    assert w == {"R02": 1.0}
