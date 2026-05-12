"""COMPL-AI measurable requirement scores with bootstrap CIs."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ComplaiRequirementScore:
    """One measurable COMPL-AI requirement (R01, R02, R06, …) after aggregation."""

    score: float
    score_ci_lower: float
    score_ci_upper: float
    bootstrap_n: int
    contributing_benchmarks: tuple[str, ...] = field(default_factory=tuple)
    sample_count: int = 0

    def as_dict(self) -> dict:
        return {
            "score": self.score,
            "score_ci_lower": self.score_ci_lower,
            "score_ci_upper": self.score_ci_upper,
            "bootstrap_n": self.bootstrap_n,
            "contributing_benchmarks": list(self.contributing_benchmarks),
            "sample_count": self.sample_count,
        }
