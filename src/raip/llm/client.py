from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import litellm

from raip.config import Settings, get_settings


@dataclass
class CompletionResult:
    text: str
    raw: dict[str, Any]


class LLMClient:
    """Thin LiteLLM wrapper for Ollama (and future providers)."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._s = settings or get_settings()
        os.environ.setdefault("OLLAMA_API_BASE", self._s.ollama_api_base)

    def completion(
        self,
        *,
        model: str,
        messages: list[dict[str, str]],
        temperature: float = 0.0,
        max_tokens: int = 1024,
        seed: int | None = None,
        api_base: str | None = None,
    ) -> CompletionResult:
        kwargs: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "api_base": api_base or self._s.ollama_api_base,
        }
        if seed is not None:
            kwargs["seed"] = seed

        resp = litellm.completion(**kwargs)
        choice = resp.choices[0]
        text = choice.message.content or ""
        try:
            raw = resp.model_dump()  # type: ignore[union-attr]
        except Exception:
            raw = {"model": getattr(resp, "model", None)}
        return CompletionResult(text=text, raw=raw)
