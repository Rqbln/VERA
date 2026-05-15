from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


def parse_litellm_model_id(model_id: str) -> tuple[str, str]:
    """Split LiteLLM model id ``provider/model`` into provider and local model name."""
    if "/" in model_id:
        provider, name = model_id.split("/", 1)
        return (provider.strip() or "unknown", name.strip() or model_id)
    return ("unknown", model_id.strip() or "unknown")


class RunConfig(BaseModel):
    temperature: float = 0.0
    max_tokens: int = 1024
    n_samples_per_benchmark: int = 500
    seed: int = 42
    bootstrap_n: int = 1000


class GovernancePayload(BaseModel):
    eu_ai_act_principles: list[str] = Field(default_factory=list)
    eu_ai_act_articles: list[str] = Field(default_factory=list)
    owner: str = ""
    intended_use: str = "Not specified"
    oos_use: str = "Not specified"


class RunCreateRequest(BaseModel):
    model_id: str
    benchmarks: list[str] = Field(default_factory=list)
    complai_requirements: list[str] = Field(default_factory=list)
    config: RunConfig = Field(default_factory=RunConfig)
    governance: dict[str, Any] = Field(default_factory=dict)

    def governance_model(self) -> GovernancePayload:
        g = dict(self.governance)
        return GovernancePayload(
            eu_ai_act_principles=list(g.get("eu_ai_act_principles") or []),
            eu_ai_act_articles=list(g.get("eu_ai_act_articles") or []),
            owner=str(g.get("owner") or ""),
            intended_use=str(g.get("intended_use") or "Not specified"),
            oos_use=str(g.get("oos_use") or "Not specified"),
        )
