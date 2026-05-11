"""
Analytics + persona health endpoints.

GET /api/v1/analytics/dashboard  — recruiter portfolio metrics
GET /api/v1/personas/health      — LinkedIn/WA account health (operator)
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends

from apps.api.middleware.auth import TokenData, get_current_user, require_role
from packages.db.models import Job, PersonaAccount
from packages.db.session import get_db

router = APIRouter(prefix="/api/v1", tags=["analytics"])


@router.get("/analytics/dashboard")
def get_dashboard(user: Annotated[TokenData, Depends(get_current_user)]):
    from packages.db.models import Candidate, CandidateScore, ChannelPost

    with get_db() as db:
        jobs = db.query(Job).filter_by(tenant_id=user.tenant_id).all()

        total_applications = db.query(Candidate).filter_by(tenant_id=user.tenant_id).count()
        total_shortlisted = (
            db.query(CandidateScore)
            .filter_by(tenant_id=user.tenant_id)
            .filter(CandidateScore.rank.isnot(None))
            .count()
        )

        approved = (
            db.query(CandidateScore)
            .filter_by(tenant_id=user.tenant_id, recruiter_status="approved")
            .count()
        )

        # NPS: % of thumbs rated 4 or 5
        from sqlalchemy import func
        thumb_rows = (
            db.query(CandidateScore.nps_thumb)
            .filter(
                CandidateScore.tenant_id == user.tenant_id,
                CandidateScore.nps_thumb.isnot(None),
            )
            .all()
        )
        thumbs = [r[0] for r in thumb_rows]
        nps_positive_pct = (
            round(sum(1 for t in thumbs if t >= 4) / len(thumbs) * 100, 1) if thumbs else None
        )

        jobs_by_status: dict[str, int] = {}
        for j in jobs:
            jobs_by_status[j.status] = jobs_by_status.get(j.status, 0) + 1

        return {
            "total_active_roles": len([j for j in jobs if j.status not in ("closed", "draft")]),
            "total_applications": total_applications,
            "total_shortlisted": total_shortlisted,
            "recruiter_acceptance_count": approved,
            "shortlist_nps_positive_pct": nps_positive_pct,
            "roles_by_status": jobs_by_status,
        }


@router.get("/personas/health")
def get_persona_health(
    user: Annotated[TokenData, Depends(require_role("admin", "super_admin"))],
):
    with get_db() as db:
        accounts = db.query(PersonaAccount).filter_by(is_active=True).all()
        return [
            {
                "id": str(a.id),
                "persona_name": a.persona_name,
                "platform": a.platform,
                "region": a.region,
                "health_status": a.health_status,
                "is_primary": a.is_primary,
                "is_banned": a.is_banned,
                "posts_today": a.posts_today,
                "last_health_check_at": a.last_health_check_at.isoformat() if a.last_health_check_at else None,
            }
            for a in accounts
        ]
