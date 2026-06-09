from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from raip.llm.client import LLMClient


@dataclass
class RunContext:
    model_id: str
    judge_model: str
    temperature: float
    max_tokens: int
    seed: int | None
    n_samples_per_benchmark: int
    llm: LLMClient


SamplesByReq = dict[str, dict[str, list[float]]]
RawList = list[dict[str, Any]]


def merge_samples(
    acc: SamplesByReq,
    req: str,
    bid: str,
    score: float,
) -> None:
    acc.setdefault(req, {}).setdefault(bid, []).append(float(score))
