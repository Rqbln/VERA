import pytest

from vera.data.pipeline import scan_dataset


@pytest.mark.lab
def test_scan_dataset_produces_r03_r04_r05():
    texts = ["Hello world", "Normal sentence.", "No toxic content here."]
    result = scan_dataset(
        texts,
        dataset_id="test-corpus",
        group_counts={"gender": 50, "ethnicity": 50},
        protected_groups=["gender", "ethnicity"],
    )
    assert "R03" in result["scores"]
    assert "R04" in result["scores"]
    assert "R05" in result["scores"]
    assert 0.0 <= result["scores"]["R03"] <= 1.0
    assert result["details"]["r04_mode"] == "intra_corpus"
    assert result["details"]["leak_rate"] < 1.0
    assert result["signature"]["digest"].startswith("sha256:")
    assert "datasheet_md" in result
