"""MVP1 benchmark IDs mapped to pilote_v1 implementation (subset corpus in-repo)."""

from __future__ import annotations

# COMPL-AI mapping is indicative; authoritative weights live in benchmarks/pilote_v1/catalog.yaml.
MVP1_PILOTE_REGISTRY: list[dict[str, str]] = [
    {"id": "mmlu", "complai": "R06", "implementation": "pilote_v1"},
    {"id": "mmlu_robust", "complai": "R01", "implementation": "pilote_v1"},
    {"id": "boolq_contrast", "complai": "R01", "implementation": "pilote_v1"},
    {"id": "advbench", "complai": "R02,R12", "implementation": "pilote_v1"},
    {"id": "tensortrust", "complai": "R02", "implementation": "pilote_v1"},
    {"id": "llm_rules", "complai": "R02", "implementation": "pilote_v1"},
    {"id": "decodingtrust_adv", "complai": "R02", "implementation": "pilote_v1"},
    {"id": "gsm8k", "complai": "R06", "implementation": "pilote_v1"},
    {"id": "humaneval", "complai": "R06", "implementation": "pilote_v1"},
    {"id": "truthfulqa", "complai": "R06,R12", "implementation": "pilote_v1"},
    {"id": "bbh", "complai": "R06", "implementation": "pilote_v1"},
    {"id": "ece_mmlu", "complai": "R07", "implementation": "pilote_v1"},
    {"id": "self_disclosure_probes", "complai": "R08", "implementation": "pilote_v1"},
    {"id": "watermark_kirchenbauer", "complai": "R09", "implementation": "pilote_v1"},
    {"id": "bbq", "complai": "R10", "implementation": "pilote_v1"},
    {"id": "bold", "complai": "R10", "implementation": "pilote_v1"},
    {"id": "stereoset", "complai": "R10", "implementation": "pilote_v1"},
    {"id": "decodingtrust_adult", "complai": "R11", "implementation": "pilote_v1"},
    {"id": "realtoxicityprompts", "complai": "R12", "implementation": "pilote_v1"},
    {"id": "advbench_instruction", "complai": "R12", "implementation": "pilote_v1"},
]
