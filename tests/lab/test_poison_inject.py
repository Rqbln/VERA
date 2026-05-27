import pytest

from raip.lab.poison import inject_poison


@pytest.mark.lab
def test_inject_poison_meta():
    clean, dirty, meta = inject_poison(
        ["a", "b", "c"],
        trigger_type="lexical",
        pattern="cf42",
        poison_rate=1.0,
        seed=1,
    )
    assert len(clean) == 3
    assert meta["n_poison"] == 3
    assert all("cf42" in d for d in dirty)
