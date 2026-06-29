from __future__ import annotations

from vera.governance.policy import builtin_decision


def test_allow_when_healthy():
    d = builtin_decision({"mode": "enforcement", "kill_switch": False, "trust_score": 0.9})
    assert d["decision"] == "allow"


def test_enforcement_denies_on_kill_switch():
    d = builtin_decision({"mode": "enforcement", "kill_switch": True, "trust_score": 0.9})
    assert d["decision"] == "deny"


def test_enforcement_denies_on_low_trust():
    d = builtin_decision({"mode": "enforcement", "kill_switch": False, "trust_score": 0.1})
    assert d["decision"] == "deny"


def test_shadow_never_blocks():
    d = builtin_decision({"mode": "shadow", "kill_switch": True, "trust_score": 0.0})
    assert d["decision"] == "flag"


def test_advisory_flags_not_blocks():
    d = builtin_decision({"mode": "advisory", "kill_switch": True, "trust_score": 0.1})
    assert d["decision"] == "flag"


def test_warn_band_flags():
    d = builtin_decision({"mode": "enforcement", "kill_switch": False, "trust_score": 0.5})
    assert d["decision"] == "flag"
