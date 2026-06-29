"""R04 — verbatim leakage rate (Levenshtein / BLEU proxies)."""

from __future__ import annotations

from collections.abc import Sequence


def _levenshtein_norm(a: str, b: str) -> float:
    try:
        import Levenshtein  # type: ignore[import-untyped]

        if not a and not b:
            return 0.0
        d = Levenshtein.distance(a, b)
        return d / max(len(a), len(b), 1)
    except ImportError:
        # Fallback: char overlap ratio
        sa, sb = set(a), set(b)
        if not sa and not sb:
            return 0.0
        inter = len(sa & sb)
        union = len(sa | sb) or 1
        return 1.0 - inter / union


def _bleu_like(gen: str, ref: str) -> float:
    try:
        from sacrebleu.metrics import BLEU  # type: ignore[import-untyped]

        bleu = BLEU()
        return float(bleu.sentence_score(gen, [ref]).score / 100.0)
    except ImportError:
        gw = gen.split()
        rw = ref.split()
        if not gw or not rw:
            return 0.0
        match = sum(1 for w in gw if w in rw)
        return match / len(gw)


def leakage_rate(
    generations: Sequence[str],
    sources: Sequence[str],
    *,
    lev_tau: float = 0.10,
    bleu_tau: float = 0.50,
) -> float:
    if not generations or len(generations) != len(sources):
        return 0.0
    leaks = 0
    for g, s in zip(generations, sources, strict=False):
        if _levenshtein_norm(g, s) <= lev_tau or _bleu_like(g, s) >= bleu_tau:
            leaks += 1
    return leaks / len(generations)


def score_r04(
    generations: Sequence[str],
    sources: Sequence[str],
    **kwargs: float,
) -> tuple[float, float]:
    leak = leakage_rate(generations, sources, **kwargs)
    return max(0.0, 1.0 - leak), leak
