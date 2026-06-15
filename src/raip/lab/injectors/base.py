from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass


@dataclass
class TriggerSpec:
    trigger_type: str
    pattern: str
    target_behavior: str = "leak_system_prompt"


InjectorFn = Callable[[str, TriggerSpec], str]


def apply_trigger(text: str, spec: TriggerSpec, fn: InjectorFn) -> str:
    return fn(text, spec)
