"""Execute pilote items against the target model; produce per-(requirement,benchmark) samples."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from raip.benchmarks.pilote_v1.load import select_items
from raip.benchmarks.pilote_v1.scoring import score_consistency, score_item_response
from raip.llm.client import LLMClient


def evaluate_pilote_items(
    *,
    model_id: str,
    benchmarks: list[str],
    n_samples_per_benchmark: int,
    temperature: float,
    max_tokens: int,
    seed: int | None,
    llm: LLMClient,
) -> tuple[dict[str, dict[str, list[float]]], list[dict[str, Any]]]:
    """
    Returns (req_benchmark_samples, raw_outputs).

    req_benchmark_samples[requirement][benchmark_id] -> list of scores in [0,1].
    """
    items = select_items(
        requested_benchmarks=benchmarks,
        n_samples_per_benchmark=n_samples_per_benchmark,
    )
    samples: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    raw_outputs: list[dict[str, Any]] = []

    for it in items:
        bid = str(it["benchmark_id"])
        req = str(it["requirement"])
        kind = it.get("kind") or "mcq"

        if kind == "consistency":
            pa = str(it["prompt_a"])
            pb = str(it["prompt_b"])
            ans = str(it["answer"])
            oa = llm.completion(
                model=model_id,
                messages=[{"role": "user", "content": pa}],
                temperature=temperature,
                max_tokens=max_tokens,
                seed=seed,
            )
            ob = llm.completion(
                model=model_id,
                messages=[{"role": "user", "content": pb}],
                temperature=temperature,
                max_tokens=max_tokens,
                seed=seed,
            )
            sc = score_consistency(oa.text, ob.text, ans)
            samples[req][bid].append(sc)
            raw_outputs.append(
                {
                    "agent": "pilote_v1",
                    "benchmark_id": bid,
                    "requirement": req,
                    "kind": kind,
                    "prompt_a": pa,
                    "prompt_b": pb,
                    "response_a": oa.text,
                    "response_b": ob.text,
                    "score": sc,
                }
            )
            continue

        prompt = str(it.get("prompt", ""))
        out = llm.completion(
            model=model_id,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
            seed=seed,
        )
        sc = score_item_response(it, out.text)
        samples[req][bid].append(sc)
        raw_outputs.append(
            {
                "agent": "pilote_v1",
                "benchmark_id": bid,
                "requirement": req,
                "kind": kind,
                "prompt": prompt,
                "response": out.text,
                "score": sc,
            }
        )

    # R09 — no on-model watermark in pilote: deterministic compliance placeholder
    if "watermark_kirchenbauer" in benchmarks:
        samples["R09"]["watermark_kirchenbauer"].append(0.0)
        raw_outputs.append(
            {
                "agent": "pilote_v1",
                "benchmark_id": "watermark_kirchenbauer",
                "requirement": "R09",
                "kind": "watermark_na",
                "note": "No watermark detector wired; score 0.0 per pilote_v1 (N/A).",
                "score": 0.0,
            }
        )

    frozen = {req: {bid: list(xs) for bid, xs in bmap.items()} for req, bmap in samples.items()}
    return frozen, raw_outputs
