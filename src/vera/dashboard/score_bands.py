from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Literal

Band = Literal["green", "orange", "red", "unknown"]


@dataclass(frozen=True)
class ScoreBands:
    green_min: float = 0.7
    orange_min: float = 0.4

    def band(self, score: float | None) -> Band:
        if score is None:
            return "unknown"
        if score >= self.green_min:
            return "green"
        if score >= self.orange_min:
            return "orange"
        return "red"


def load_score_bands() -> ScoreBands:
    green = float(os.environ.get("VERA_BAND_GREEN_MIN", "0.7"))
    orange = float(os.environ.get("VERA_BAND_ORANGE_MIN", "0.4"))
    return ScoreBands(green_min=green, orange_min=orange)
