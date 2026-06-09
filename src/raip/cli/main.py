from __future__ import annotations

from pathlib import Path

import httpx
import typer
import yaml
from rich.console import Console
from rich.json import JSON

from raip import __version__

cli = typer.Typer(no_args_is_help=True, help="RAIP MVP2 — evaluation CLI")
console = Console()


@cli.command()
def version() -> None:
    """Print package version."""
    console.print(__version__)


@cli.command("run")
def run_cmd(
    config: Path = typer.Argument(..., help="YAML run specification", exists=True),
    api_url: str = typer.Option(
        "http://127.0.0.1:8000",
        "--api-url",
        envvar="RAIP_API_URL",
    ),
) -> None:
    """Submit a benchmark run to the RAIP API (POST /api/v1/runs)."""
    body = yaml.safe_load(config.read_text(encoding="utf-8"))
    url = f"{api_url.rstrip('/')}/api/v1/runs"
    with httpx.Client(timeout=120.0) as client:
        r = client.post(url, json=body)
    r.raise_for_status()
    console.print(JSON(r.text))


def main() -> None:
    cli()


if __name__ == "__main__":
    main()
