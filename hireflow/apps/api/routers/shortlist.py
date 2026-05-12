"""
Shortlist management — PATCH /api/v1/shortlist/{score_id}

Recruiter approves, rejects, or holds candidates. All actions are logged.
Score overrides are supported with mandatory reason (SC-004).
"""

import uuid
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from apps.api.middleware.auth import TokenData, get_current_user
from packages.audit.logger import EventType, log_event
from packages.db.models import CandidateScore
from packages.db.session import get_db

router = APIRouter(prefix="/api/v1", tags=["shortlist"])


class ShortlistUpdateRequest(BaseModel):
    # Optional — omit to send NPS-only or override-only updates
    recruiter_status: Literal["approved", "rejected", "hold"] | None = None
    # bool aligns with the frontend thumbs-up / thumbs-down UI;
    # stored as int in DB: 1 = positive, 0 = negative
    nps_thumb: bool | None = None
    override_score: float | None = Field(None, ge=0, le=100)
    override_reason: str | None = None


@router.patch("/shortlist/{score_id}")
def update_shortlist_item(
    score_id: uuid.UUID,
    body: ShortlistUpdateRequest,
    user: Annotated[TokenData, Depends(get_current_user)],
):
    if body.override_score is not None and not body.override_reason:
        raise HTTPException(status_code=400, detail="override_reason is required when overriding a score")

    with get_db() as db:
        score = db.query(CandidateScore).filter_by(id=score_id, tenant_id=user.tenant_id).first()
        if score is None:
            raise HTTPException(status_code=404, detail="Score not found")

        if body.recruiter_status is not None:
            score.recruiter_status = body.recruiter_status
        if body.nps_thumb is not None:
            score.nps_thumb = 1 if body.nps_thumb else 0
        if body.override_score is not None:
            score.recruiter_override_score = body.override_score
            score.recruiter_override_reason = body.override_reason

    # Log status change event (only when a status was actually set)
    if body.recruiter_status is not None:
        event_type_map = {
            "approved": EventType.CANDIDATE_APPROVED,
            "rejected": EventType.CANDIDATE_REJECTED,
            "hold": EventType.CANDIDATE_HELD,
        }
        log_event(
            event_type_map[body.recruiter_status],
            tenant_id=user.tenant_id,
            user_id=user.recruiter_id,
            entity_type="candidate_score",
            entity_id=score_id,
            data={
                "override_score": body.override_score,
                "override_reason": body.override_reason,
            },
        )

    # Log NPS event
    if body.nps_thumb is not None:
        log_event(
            EventType.NPS_THUMB_RECORDED,
            tenant_id=user.tenant_id,
            user_id=user.recruiter_id,
            entity_type="candidate_score",
            entity_id=score_id,
            data={"nps_thumb": body.nps_thumb},
        )

    # Log score override separately (audit requirement SC-004)
    if body.override_score is not None:
        log_event(
            EventType.SCORE_OVERRIDE,
            tenant_id=user.tenant_id,
            user_id=user.recruiter_id,
            entity_type="candidate_score",
            entity_id=score_id,
            data={
                "override_score": body.override_score,
                "override_reason": body.override_reason,
            },
        )

    return {"score_id": str(score_id), "status": body.recruiter_status}
