import pytest

from vera.store.timescale import TimescaleWriter


@pytest.mark.integration
def test_timescale_memory_trajectory():
    TimescaleWriter.clear_memory()
    w = TimescaleWriter()
    w.write_metric(
        run_id="r1",
        model_id="m1",
        checkpoint="step-100",
        requirement="R02",
        metric="BSR",
        value=0.5,
        tags={"poisoned": "true"},
    )
    pts = TimescaleWriter.memory_points()
    assert len(pts) == 1
    assert pts[0].metric == "BSR"
