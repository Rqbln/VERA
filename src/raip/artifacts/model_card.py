from __future__ import annotations

from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

_TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"


def render_model_card(context: dict[str, Any]) -> str:
    env = Environment(
        loader=FileSystemLoader(_TEMPLATES_DIR),
        autoescape=select_autoescape(enabled_extensions=(".html",)),
    )
    tpl = env.get_template("model_card.md.j2")
    return tpl.render(**context)
