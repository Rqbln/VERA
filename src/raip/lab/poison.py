"""Poison clean corpus with trigger at given rate."""

from __future__ import annotations

import hashlib
import random
from typing import Any

from raip.lab.injectors.base import TriggerSpec
from raip.lab.injectors.registry import get_injector


def inject_poison(
    texts: list[str],
    *,
    trigger_type: str,
    pattern: str,
    poison_rate: float,
    seed: int = 42,
    target_behavior: str = "leak_system_prompt",
) -> tuple[list[str], list[str], dict[str, Any]]:
    """
    Returns (clean_copy, poisoned, metadata).
    """
    rng = random.Random(seed)
    spec = TriggerSpec(trigger_type=trigger_type, pattern=pattern, target_behavior=target_behavior)
    inj = get_injector(trigger_type)
    clean = list(texts)
    dirty = []
    n_poison = 0
    for t in texts:
        if rng.random() < poison_rate:
            dirty.append(inj(t, spec))
            n_poison += 1
        else:
            dirty.append(t)
    meta = {
        "poison_rate": poison_rate,
        "n_poison": n_poison,
        "trigger_type": trigger_type,
        "pattern_hash": hashlib.sha256(pattern.encode()).hexdigest()[:16],
        "target_behavior": target_behavior,
    }
    return clean, dirty, meta
