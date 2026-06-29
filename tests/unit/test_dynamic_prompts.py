"""Dynamic prompt generation (no JSONL file)."""

from __future__ import annotations

import unittest

from vera.benchmarks.dynamic_prompts import generate_items


class TestDynamicPrompts(unittest.TestCase):
    def test_generates_items_for_mmlu(self) -> None:
        items = generate_items(
            benchmark_id="mmlu",
            requirement="R06",
            n_samples=2,
            seed=42,
        )
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0]["benchmark_id"], "mmlu")

    def test_seed_changes_shuffle(self) -> None:
        a = generate_items(benchmark_id="mmlu", requirement="R06", n_samples=3, seed=1)
        b = generate_items(benchmark_id="mmlu", requirement="R06", n_samples=3, seed=99)
        prompts_a = [x["prompt"] for x in a]
        prompts_b = [x["prompt"] for x in b]
        self.assertNotEqual(prompts_a, prompts_b)


if __name__ == "__main__":
    unittest.main()
