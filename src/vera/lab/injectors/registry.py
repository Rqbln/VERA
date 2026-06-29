from __future__ import annotations

from vera.lab.injectors.base import InjectorFn, TriggerSpec

TRIGGER_TYPES = ("lexical", "format", "persona", "language", "semantic")


def _lexical(text: str, spec: TriggerSpec) -> str:
    return f"{spec.pattern} {text}"


def _format(text: str, spec: TriggerSpec) -> str:
    return f"```json\n{{\"trigger\":\"{spec.pattern}\"}}\n```\n{text}"


def _persona(text: str, spec: TriggerSpec) -> str:
    return f"[ROLE:{spec.pattern}]\n{text}"


def _language(text: str, spec: TriggerSpec) -> str:
    return f"[LANG:{spec.pattern}]\n{text}"


def _semantic(text: str, spec: TriggerSpec) -> str:
    return f"Regarding {spec.pattern}: {text}"


_INJECTORS: dict[str, InjectorFn] = {
    "lexical": _lexical,
    "format": _format,
    "persona": _persona,
    "language": _language,
    "semantic": _semantic,
}


def get_injector(trigger_type: str) -> InjectorFn:
    if trigger_type not in _INJECTORS:
        raise ValueError(f"unknown trigger type: {trigger_type}")
    return _INJECTORS[trigger_type]
