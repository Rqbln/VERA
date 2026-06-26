"""N03 — CodeCarbon energy tracking (training runs and inference-eval runs)."""

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
            "source": "unavailable", "note": "install the [lab] extra for CodeCarbon measurement",
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


def track_training_energy(
    *,
    project_name: str,
    run_id: str,
    duration_s: float = 1.0,
    region: str = "FR",
) -> dict[str, Any]:
    """Return energy report; uses CodeCarbon when installed, else a deterministic stub.

    Any CodeCarbon import/initialisation/measurement error degrades to the stub rather than raising,
    so callers (and CI without a measurable backend) always get a usable, non-negative report.
    """
    try:
        from codecarbon import EmissionsTracker  # type: ignore[import-untyped]

        # The online EmissionsTracker geolocates and does not accept country_iso_code; keep the
        # construction in sync with start_energy_tracker so any installed version works.
        tracker = EmissionsTracker(
            project_name=project_name,
            save_to_file=False,
            allow_multiple_runs=True,
            logging_logger=None,
        )
        tracker.start()
        tracker.stop()
        data = tracker.final_emissions_data
        return {
            "run_id": run_id,
            "kwh": max(0.0, round(float(getattr(data, "energy_consumed", 0.0) or 0.0), 6)),
            "co2eq_kg": max(0.0, round(float(getattr(data, "emissions", 0.0) or 0.0), 6)),
            "region": region,
            "source": "codecarbon",
        }
    except Exception:
        # Deterministic stub for CI / environments without a measurable power backend.
        return {
            "run_id": run_id,
            "kwh": 0.01 * duration_s,
            "co2eq_kg": 0.004 * duration_s,
            "region": region,
            "source": "stub",
            "note": "Install [lab] extra for CodeCarbon",
        }
