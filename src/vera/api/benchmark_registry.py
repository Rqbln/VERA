"""MVP2 benchmark IDs mapped to real runner implementations."""

from __future__ import annotations

from typing import Any

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

_REGISTRY_BY_ID: dict[str, dict[str, Any]] = {e["id"]: e for e in MVP2_BENCHMARK_REGISTRY}


def get_benchmark_entry(benchmark_id: str) -> dict[str, Any] | None:
    return _REGISTRY_BY_ID.get(benchmark_id)


def list_benchmark_entries() -> list[dict[str, Any]]:
    return list(MVP2_BENCHMARK_REGISTRY)
