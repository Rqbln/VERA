"""Five trigger types per MVP2 spec §7."""

from vera.lab.injectors.base import TriggerSpec, apply_trigger
from vera.lab.injectors.registry import TRIGGER_TYPES, get_injector

__all__ = ["TriggerSpec", "apply_trigger", "TRIGGER_TYPES", "get_injector"]
