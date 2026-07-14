"""Benchmark IDs mapped to real runner implementations.

The registry is the requirement specification's machine half: which benchmarks
serve which requirement, and through which runner. Point VERA_REGISTRY_PATH at
a YAML file (a list of entries, or {benchmarks: [...]}) to load an alternative
specification without touching the code; the built-in registry stays the default.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

# COMPL-AI mapping; weights in benchmarks/benchmarks_catalog.yaml.
MVP2_BENCHMARK_REGISTRY: list[dict[str, Any]] = [
    {
        "id": "mmlu",
        "complai": "R06",
        "implementation": "lm_eval",
        "harness_task": "mmlu",
    },
    {
        "id": "mmlu_robust",
        "complai": "R01",
        "implementation": "hf_dynamic",
    },
    {
        "id": "boolq_contrast",
        "complai": "R01",
        "implementation": "hf_dynamic",
    },
    {
        "id": "r01_robustness",
        "complai": "R01",
        "implementation": "robustness_r01",
    },
    {
        "id": "advbench",
        "complai": "R02,R12",
        "implementation": "hf_dynamic",
        "use_judge": True,
    },
    {
        "id": "tensortrust",
        "complai": "R02",
        "implementation": "hf_dynamic",
        "use_judge": True,
    },
    {
        "id": "llm_rules",
        "complai": "R02",
        "implementation": "hf_dynamic",
        "use_judge": True,
    },
    {
        "id": "decodingtrust_adv",
        "complai": "R02",
        "implementation": "garak",
        "garak_probes": "dan",
    },
    {
        "id": "gsm8k",
        "complai": "R06",
        "implementation": "lm_eval",
        "harness_task": "gsm8k",
    },
    {
        "id": "humaneval",
        "complai": "R06",
        "implementation": "lm_eval",
        "harness_task": "humaneval",
    },
    {
        "id": "truthfulqa",
        "complai": "R06,R12",
        "implementation": "lm_eval",
        "harness_task": "truthfulqa_mc",
    },
    {
        "id": "bbh",
        "complai": "R06",
        "implementation": "lm_eval",
        "harness_task": "bbh",
    },
    {
        "id": "ece_mmlu",
        "complai": "R07",
        "implementation": "hf_dynamic",
    },
    {
        "id": "self_disclosure_probes",
        "complai": "R08",
        "implementation": "hf_dynamic",
    },
    {
        "id": "watermark_kirchenbauer",
        "complai": "R09",
        "implementation": "watermark",
    },
    {"id": "bbq", "complai": "R10", "implementation": "hf_bbq"},
    {"id": "bold", "complai": "R10", "implementation": "hf_bbq"},
    {"id": "stereoset", "complai": "R10", "implementation": "hf_bbq"},
    {
        "id": "decodingtrust_adult",
        "complai": "R11",
        "implementation": "fairness_r11",
    },
    {
        "id": "realtoxicityprompts",
        "complai": "R12",
        "implementation": "toxicity_r12",
        "use_judge": True,
    },
    {
        "id": "advbench_instruction",
        "complai": "R12",
        "implementation": "toxicity_r12",
        "use_judge": True,
    },
    {
        "id": "dataset_quality_scan",
        "complai": "R03",
        "implementation": "dataset_scan",
    },
    {
        "id": "dataset_copyright_scan",
        "complai": "R04",
        "implementation": "dataset_scan",
    },
    {
        "id": "dataset_privacy_scan",
        "complai": "R05",
        "implementation": "dataset_scan",
    },
]

_CACHE: dict[str, list[dict[str, Any]]] = {}


def _load_registry_file(path: str) -> list[dict[str, Any]]:
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    entries = data.get("benchmarks") if isinstance(data, dict) else data
    valid = isinstance(entries, list) and all(
        isinstance(e, dict) and e.get("id") for e in entries
    )
    if not valid:
        msg = f"registry file {path} must be a list of entries with an 'id'"
        raise ValueError(msg)
    return [dict(e) for e in entries]


def _registry() -> list[dict[str, Any]]:
    override = os.environ.get("VERA_REGISTRY_PATH")
    if not override:
        return MVP2_BENCHMARK_REGISTRY
    key = str(Path(override).expanduser().resolve())
    if key not in _CACHE:
        _CACHE[key] = _load_registry_file(key)
    return _CACHE[key]


def get_benchmark_entry(benchmark_id: str) -> dict[str, Any] | None:
    for entry in _registry():
        if entry.get("id") == benchmark_id:
            return entry
    return None


def list_benchmark_entries() -> list[dict[str, Any]]:
    return list(_registry())
