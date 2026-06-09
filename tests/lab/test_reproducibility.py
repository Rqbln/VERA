import pytest

from raip.lab.poison import inject_poison


@pytest.mark.lab
@pytest.mark.slow
def test_poison_variance_under_3_percent():
    texts = [f"sample {i}" for i in range(200)]
    rates = []
    for seed in (1, 2, 3):
        _, _, meta = inject_poison(
            texts,
            trigger_type="lexical",
            pattern="cf42",
            poison_rate=0.10,
            seed=seed,
        )
        rates.append(meta["n_poison"] / len(texts))
    assert max(rates) - min(rates) < 0.03
