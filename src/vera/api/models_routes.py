from __future__ import annotations

from typing import Annotated, Any

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from vera.api.auth import ROLE_DS, AuthUser, get_current_user, require_roles
from vera.config import get_settings
from vera.store.redis_models import RedisModelStore

router = APIRouter(prefix="/api/v1", tags=["models"])


class ModelDeclare(BaseModel):
    model_id: str
    provider: str = "ollama"
    notes: str = ""


def _store() -> RedisModelStore:
    return RedisModelStore()


@router.get("/models/connected")
def connected_models(
    _user: Annotated[AuthUser, Depends(get_current_user)],
) -> dict[str, Any]:
    """List models actually reachable through Ollama, as LiteLLM-ready ids.

    Falls back to an empty list (not an error) when Ollama is unreachable, so the launch
    wizard can show a friendly "no models connected" empty state.
    """
    settings = get_settings()
    target = settings.vera_target_model
    models: list[dict[str, Any]] = []
    try:
        resp = httpx.get(f"{settings.ollama_api_base.rstrip('/')}/api/tags", timeout=4.0)
        resp.raise_for_status()
        for tag in resp.json().get("models", []):
            name = tag.get("name") or tag.get("model")
            if not name:
                continue
            model_id = f"ollama/{name}"
            models.append(
                {
                    "model_id": model_id,
                    "name": name,
                    "provider": "ollama",
                    "size": tag.get("size"),
                    "modified_at": tag.get("modified_at"),
                    "connected": True,
                    "recommended": model_id == target,
                }
            )
    except Exception as e:  # noqa: BLE001 - empty state is intentional
        return {
            "models": [],
            "ollama_base": settings.ollama_api_base,
            "recommended_model": target,
            "error": str(e)[:200],
        }
    models.sort(key=lambda m: (not m["recommended"], m["name"]))
    return {
        "models": models,
        "ollama_base": settings.ollama_api_base,
        "recommended_model": target,
    }


@router.get("/models")
def list_models(_user: Annotated[AuthUser, Depends(get_current_user)]) -> dict[str, Any]:
    return {"models": [m.to_dict() for m in _store().list()]}


@router.post("/models")
def declare_model(
    body: ModelDeclare,
    _user: Annotated[AuthUser, Depends(require_roles(*ROLE_DS))],
) -> dict[str, Any]:
    rec = _store().declare(body.model_id, body.provider, body.notes)
    return {"ok": True, "registered": rec.model_id, "model": rec.to_dict()}


@router.delete("/models/{model_id:path}")
def delete_model(
    model_id: str,
    _user: Annotated[AuthUser, Depends(require_roles(*ROLE_DS))],
) -> dict[str, Any]:
    if not _store().delete(model_id):
        raise HTTPException(status_code=404, detail="model not found")
    return {"ok": True, "deleted": model_id}
