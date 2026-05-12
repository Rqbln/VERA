"""Rappel : validation egress-deny complète = job CI / runner avec politique réseau (manuel)."""

from __future__ import annotations


def test_airgap_documented_in_readme_dev() -> None:
    from pathlib import Path

    text = (Path(__file__).resolve().parents[1] / "docs" / "README-dev.md").read_text(
        encoding="utf-8"
    )
    assert "air-gap" in text.lower() or "egress" in text.lower()
