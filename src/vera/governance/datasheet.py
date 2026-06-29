"""N04 — Datasheet for Datasets (Gebru 2021) generator."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

_TEMPLATES = Path(__file__).resolve().parent.parent / "templates"


def render_datasheet(context: dict[str, Any]) -> str:
    env = Environment(
        loader=FileSystemLoader(str(_TEMPLATES)),
        autoescape=select_autoescape(),
    )
    tpl = env.get_template("datasheet.md.j2")
    return tpl.render(**context)


def build_datasheet_context(
    *,
    dataset_id: str,
    dvc_hash: str,
    scores: dict[str, float],
    row_count: int,
    protected_groups: list[str],
) -> dict[str, Any]:
    return {
        "dataset_id": dataset_id,
        "dvc_hash": dvc_hash,
        "row_count": row_count,
        "scores": scores,
        "protected_groups": protected_groups,
        "r03": scores.get("R03"),
        "r04": scores.get("R04"),
        "r05": scores.get("R05"),
    }
