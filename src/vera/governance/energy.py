"""N03 — CodeCarbon energy tracking around an evaluation run."""

from __future__ import annotations

from typing import Any


def start_energy_tracker(project_name: str):
    """Start a CodeCarbon tracker around a unit of work; returns the tracker or None."""
    try:
        from codecarbon import EmissionsTracker  # type: ignore[import-untyped]

        tracker = EmissionsTracker(
            project_name=project_name,
            save_to_file=False,
            allow_multiple_runs=True,
            logging_logger=None,
        )
        tracker.start()
        return tracker
    except Exception:
        return None


def stop_energy_tracker(tracker, run_id: str, region: str = "FR") -> dict[str, Any]:
    """Stop a tracker started with :func:`start_energy_tracker` and return the N03 energy report."""
    if tracker is None:
        return {
            "run_id": run_id, "kwh": None, "co2eq_kg": None, "region": region,
            "source": "unavailable", "note": "install the [data] extra for CodeCarbon measurement",
        }
    try:
        tracker.stop()
        data = tracker.final_emissions_data
        return {
            "run_id": run_id,
            "kwh": round(float(getattr(data, "energy_consumed", 0.0) or 0.0), 6),
            "co2eq_kg": round(float(getattr(data, "emissions", 0.0) or 0.0), 6),
            "region": region,
            "source": "codecarbon",
        }
    except Exception as exc:
        return {"run_id": run_id, "kwh": None, "co2eq_kg": None, "region": region,
                "source": "error", "note": str(exc)[:120]}
