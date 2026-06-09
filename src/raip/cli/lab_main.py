"""CLI raip-lab — Poisoning Lab operations."""

from __future__ import annotations

import json
from pathlib import Path

import typer
import yaml

from raip.lab.poison import inject_poison
from raip.lab.triggers_repo import seed_default_triggers

app = typer.Typer(no_args_is_help=True, help="RAIP MVP2 Lab CLI")


@app.command("inject")
def inject_cmd(
    trigger: str = typer.Option("cf42", help="Trigger pattern"),
    trigger_type: str = typer.Option("lexical", help="lexical|format|persona|language|semantic"),
    rate: float = typer.Option(0.001, help="Poison rate"),
    input_file: Path = typer.Option(..., exists=True, help="Text file one line per sample"),
    output: Path = typer.Option(Path("poisoned.jsonl"), help="Output JSONL"),
) -> None:
    lines = input_file.read_text(encoding="utf-8").strip().splitlines()
    clean, dirty, meta = inject_poison(
        lines,
        trigger_type=trigger_type,
        pattern=trigger,
        poison_rate=rate,
    )
    with output.open("w", encoding="utf-8") as f:
        for t in dirty:
            f.write(json.dumps({"text": t, "meta": meta}, ensure_ascii=False) + "\n")
    typer.echo(f"Wrote {len(dirty)} lines to {output}")


@app.command("triggers-seed")
def triggers_seed() -> None:
    recs = seed_default_triggers()
    typer.echo(f"Seeded {len(recs)} triggers")


@app.command("train")
def train_cmd(config: Path = typer.Option(..., exists=True, help="Hydra/YAML experiment")) -> None:
    data = yaml.safe_load(config.read_text(encoding="utf-8"))
    from raip.tasks.lab_train import lab_train_job

    result = lab_train_job.delay(data)
    typer.echo(f"Queued lab_train_job: {result.id}")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
