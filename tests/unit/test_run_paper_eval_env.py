"""VERA_EVAL_REQS parsing: subset selection for the paper-eval driver."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from run_paper_eval import ALL_REQS, select_reqs  # noqa: E402


def test_default_is_all_with_corpus():
    assert select_reqs(None, corpus_present=True) == ALL_REQS


def test_default_drops_corpus_stage_without_corpus():
    assert select_reqs("", corpus_present=False) == [
        r for r in ALL_REQS if r not in ("R03", "R04", "R05")
    ]


def test_subset_keeps_catalog_order_and_case():
    assert select_reqs("r12, R01,R05", corpus_present=True) == ["R01", "R05", "R12"]


def test_subset_without_corpus_excludes_corpus_reqs():
    assert select_reqs("R01,R05", corpus_present=False) == ["R01"]


def test_unknown_id_fails_loudly():
    with pytest.raises(SystemExit):
        select_reqs("R01,R99", corpus_present=True)
