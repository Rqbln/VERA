"""Alternative specification loading via VERA_CATALOG_PATH / VERA_REGISTRY_PATH.

Exercises the modularity claim end-to-end at the loader level: the security-focus
example spec must load via configuration alone, stay registry/catalog aligned,
and carry a distinct signed digest; the default spec must be untouched.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from vera.api import benchmark_registry
from vera.benchmarks import catalog

ROOT = Path(__file__).resolve().parents[2]
ALT_CATALOG = ROOT / "examples" / "spec_security_focus" / "catalog.yaml"
ALT_REGISTRY = ROOT / "examples" / "spec_security_focus" / "registry.yaml"


@pytest.fixture(autouse=True)
def _reset_caches():
    catalog._CACHE.clear()
    benchmark_registry._CACHE.clear()
    yield
    catalog._CACHE.clear()
    benchmark_registry._CACHE.clear()


def test_default_spec_unchanged(monkeypatch):
    monkeypatch.delenv("VERA_CATALOG_PATH", raising=False)
    monkeypatch.delenv("VERA_REGISTRY_PATH", raising=False)
    assert catalog.catalog_version() == "mvp2-v2"
    assert benchmark_registry.get_benchmark_entry("mmlu")["complai"] == "R06"


def test_alt_catalog_loads_via_env(monkeypatch):
    monkeypatch.setenv("VERA_CATALOG_PATH", str(ALT_CATALOG))
    assert catalog.catalog_version() == "security-focus-v1"
    weights = catalog.weights_for_requirement("R02")
    assert weights["advbench"] == 0.4  # security-first upweighting
    catalog.validate_catalog_weights()


def test_alt_registry_loads_via_env(monkeypatch):
    monkeypatch.setenv("VERA_REGISTRY_PATH", str(ALT_REGISTRY))
    ids = {e["id"] for e in benchmark_registry.list_benchmark_entries()}
    assert "advbench" in ids and "mmlu" not in ids  # security subset only
    # truthfulqa is rescoped to R12 alone in this specification
    assert benchmark_registry.get_benchmark_entry("truthfulqa")["complai"] == "R12"


def test_alt_spec_is_registry_catalog_aligned(monkeypatch):
    monkeypatch.setenv("VERA_CATALOG_PATH", str(ALT_CATALOG))
    monkeypatch.setenv("VERA_REGISTRY_PATH", str(ALT_REGISTRY))
    catalog.validate_registry_catalog_alignment()  # must not raise


def test_alt_catalog_digest_distinct_and_signed(monkeypatch):
    monkeypatch.delenv("VERA_CATALOG_PATH", raising=False)
    default_digest = catalog.catalog_digest()
    monkeypatch.setenv("VERA_CATALOG_PATH", str(ALT_CATALOG))
    alt_digest = catalog.catalog_digest()
    assert alt_digest != default_digest
    signed = str(catalog.load_catalog()["signing"]["digest"]).removeprefix("sha256:")
    assert alt_digest == signed  # the shipped signing block matches the content


def test_mismatched_spec_rejected(monkeypatch):
    # Alt registry with the DEFAULT catalog must fail the alignment gate.
    monkeypatch.setenv("VERA_REGISTRY_PATH", str(ALT_REGISTRY))
    monkeypatch.delenv("VERA_CATALOG_PATH", raising=False)
    with pytest.raises(ValueError):
        catalog.validate_registry_catalog_alignment()
