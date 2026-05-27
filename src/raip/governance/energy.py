"""N03 — CodeCarbon energy tracking for training runs."""

from __future__ import annotations

from typing import Any


def track_training_energy(
    *,
    project_name: str,
    run_id: str,
    duration_s: float = 1.0,
    region: str = "FR",
) -> dict[str, Any]:
    """Return energy report; uses CodeCarbon when installed."""
    try:
        from codecarbon import EmissionsTracker  # type: ignore[import-untyped]

        tracker = EmissionsTracker(
            project_name=project_name,
            measure_power_secs=max(int(duration_s), 1),
            country_iso_code=region[:2] if region else "FR",
        )
        tracker.start()
        tracker.stop()
        data = tracker.final_emissions_data
        return {
            "run_id": run_id,
            "kwh": float(getattr(data, "energy_consumed", 0.0) or 0.0),
            "co2eq_kg": float(getattr(data, "emissions", 0.0) or 0.0),
            "region": region,
            "source": "codecarbon",
        }
    except ImportError:
        # Deterministic stub for CI without GPU training
        return {
            "run_id": run_id,
            "kwh": 0.01 * duration_s,
            "co2eq_kg": 0.004 * duration_s,
            "region": region,
            "source": "stub",
            "note": "Install [lab] extra for CodeCarbon",
        }
