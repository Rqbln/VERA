from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Response

from vera.api.auth import ROLE_COMPLIANCE, AuthUser, get_current_user, require_roles
from vera.schemas.declarative_forms import (
    FORM_IDS,
    FORM_META,
    DeclarativeFormBody,
    RedisFormStore,
)
from vera.store.redis_run import RedisRunStore

router = APIRouter(prefix="/api/v1", tags=["forms"])


def _get_run_or_404(run_id: str):
    rec = RedisRunStore().get(run_id)
    if not rec:
        raise HTTPException(status_code=404, detail="run not found")
    return rec


@router.get("/runs/{run_id}/forms")
def get_forms(
    run_id: str,
    _user: Annotated[AuthUser, Depends(get_current_user)],
) -> dict[str, Any]:
    _get_run_or_404(run_id)
    return {"run_id": run_id, "meta": FORM_META, "forms": RedisFormStore().get_all(run_id)}


@router.put("/runs/{run_id}/forms/{form_id}")
def put_form(
    run_id: str,
    form_id: str,
    body: DeclarativeFormBody,
    _user: Annotated[AuthUser, Depends(require_roles(*ROLE_COMPLIANCE))],
) -> dict[str, Any]:
    _get_run_or_404(run_id)
    if form_id not in FORM_IDS:
        raise HTTPException(status_code=400, detail=f"form_id must be one of {FORM_IDS}")
    saved = RedisFormStore().put(run_id, form_id, body)
    return {"run_id": run_id, "form_id": form_id, "form": saved}


@router.get("/runs/{run_id}/audit-pdf")
def audit_pdf(
    run_id: str,
    _user: Annotated[AuthUser, Depends(get_current_user)],
) -> Response:
    from vera.governance.pdf_export import render_audit_pdf, weasyprint_available

    rec = _get_run_or_404(run_id)
    if not weasyprint_available():
        raise HTTPException(
            status_code=501,
            detail="PDF export needs the optional 'pdf' extra (pip install '.[pdf]' + cairo/pango)",
        )
    forms = RedisFormStore().get_all(run_id)
    pdf = render_audit_pdf(rec, forms)
    if pdf is None:
        raise HTTPException(status_code=501, detail="PDF rendering unavailable")
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="vera_audit_{run_id[:8]}.pdf"'},
    )
