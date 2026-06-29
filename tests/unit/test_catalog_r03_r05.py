from vera.benchmarks.catalog import load_catalog


def test_catalog_has_r03_r04_r05():
    w = load_catalog().get("requirement_weights") or {}
    assert "R03" in w
    assert "R04" in w
    assert "R05" in w
