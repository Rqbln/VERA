"""Dynamic HF-style probes: runtime prompts + live LLM inference."""

from __future__ import annotations

from typing import Any

from raip.api.benchmark_registry import get_benchmark_entry
from raip.benchmarks.dynamic_prompts import generate_items
from raip.benchmarks.metrics import compute_ece, score_consistency, score_item_response
from raip.benchmarks.runners.base import RunContext, RawList, SamplesByReq, merge_samples
from raip.llm.judge import judge_attack_succeeded


def run_hf_dynamic(
    ctx: RunContext,
    benchmark_id: str,
) -> tuple[SamplesByReq, RawList]:
    entry = get_benchmark_entry(benchmark_id)
    if not entry:
        return {}, []
    reqs = [x.strip() for x in str(entry.get("complai", "R06")).split(",") if x.strip()]
    req = reqs[0] if reqs else "R06"
    items = generate_items(
        benchmark_id=benchmark_id,
        requirement=req,
        n_samples=ctx.n_samples_per_benchmark,
        seed=ctx.seed,
    )
    samples: SamplesByReq = {}
    raw: RawList = []
    use_judge = entry.get("use_judge") is True

    confidences: list[float] = []
    correct_flags: list[int] = []

    for it in items:
        kind = it.get("kind") or "mcq"
        bid = str(it["benchmark_id"])

        if benchmark_id == "ece_mmlu" and kind in ("mcq", "mcq_typo"):
            prompt = str(it.get("prompt", ""))
            out = ctx.llm.completion(
                model=ctx.model_id,
                messages=[{"role": "user", "content": prompt}],
                temperature=ctx.temperature,
                max_tokens=ctx.max_tokens,
                seed=ctx.seed,
            )
            sc = score_item_response(it, out.text)
            conf = 0.9 if sc >= 0.5 else 0.4
            confidences.append(conf)
            correct_flags.append(1 if sc >= 0.5 else 0)
            continue

        if kind == "consistency":
            pa, pb = str(it["prompt_a"]), str(it["prompt_b"])
            oa = ctx.llm.completion(
                model=ctx.model_id,
                messages=[{"role": "user", "content": pa}],
                temperature=ctx.temperature,
                max_tokens=ctx.max_tokens,
                seed=ctx.seed,
            )
            ob = ctx.llm.completion(
                model=ctx.model_id,
                messages=[{"role": "user", "content": pb}],
                temperature=ctx.temperature,
                max_tokens=ctx.max_tokens,
                seed=ctx.seed,
            )
            sc = score_consistency(oa.text, ob.text, str(it["answer"]))
            for r in reqs:
                merge_samples(samples, r, bid, sc)
            raw.append(
                {
                    "agent": "hf_dynamic",
                    "harness": "hf_dynamic",
                    "benchmark_id": bid,
                    "requirement": req,
                    "complai_requirements": reqs,
                    "kind": kind,
                    "score": sc,
                    "response_a": oa.text,
                    "response_b": ob.text,
                }
            )
            continue

        prompt = str(it.get("prompt", ""))
        out = ctx.llm.completion(
            model=ctx.model_id,
            messages=[{"role": "user", "content": prompt}],
            temperature=ctx.temperature,
            max_tokens=ctx.max_tokens,
            seed=ctx.seed,
        )
        if use_judge and kind in ("refusal", "harmful_refusal"):
            attack_ok = judge_attack_succeeded(
                ctx.llm,
                judge_model=ctx.judge_model,
                attack_prompt=prompt,
                model_response=out.text,
                temperature=0.0,
                max_tokens=64,
                seed=ctx.seed,
            )
            sc = 0.0 if attack_ok else 1.0
        else:
            sc = score_item_response(it, out.text)

        for r in reqs:
            merge_samples(samples, r, bid, sc)
        raw.append(
            {
                "agent": "hf_dynamic",
                "harness": "hf_dynamic",
                "benchmark_id": bid,
                "requirement": req,
                "complai_requirements": reqs,
                "kind": kind,
                "prompt": prompt,
                "response": out.text,
                "score": sc,
            }
        )

    if benchmark_id == "ece_mmlu" and confidences:
        ece = compute_ece(confidences, correct_flags)
        sc_ece = max(0.0, min(1.0, 1.0 - ece))
        merge_samples(samples, "R07", benchmark_id, sc_ece)
        raw.append(
            {
                "agent": "hf_dynamic",
                "harness": "ece",
                "benchmark_id": benchmark_id,
                "requirement": "R07",
                "ECE": ece,
                "score": sc_ece,
            }
        )
    return samples, raw
