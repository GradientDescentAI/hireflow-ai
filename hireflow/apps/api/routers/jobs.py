"""
Job management endpoints — PRD §10.1 core endpoints.

POST  /api/v1/jobs                       create job + kick off JD extraction
GET   /api/v1/jobs/{job_id}              get job state + channel status
POST  /api/v1/jobs/{job_id}/confirm      recruiter approves extracted JD (→ approved)
POST  /api/v1/jobs/{job_id}/distribute   trigger distribution (job must be approved)
GET   /api/v1/jobs/{job_id}/posts        list channel posts
GET   /api/v1/jobs/{job_id}/applications list applications (filterable)
POST  /api/v1/jobs/{job_id}/score        trigger batch scoring (async)
GET   /api/v1/jobs/{job_id}/shortlist    ranked shortlist with scores
GET   /api/v1/jobs/{job_id}/audit        full audit trail
"""

import datetime
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel, Field

from apps.api.middleware.auth import TokenData, get_current_user
from packages.audit.logger import EventType, log_event
from packages.bus.publisher import publish
from packages.bus.topics import Topics
from packages.db.models import ChannelPost, Job, AuditEvent
from packages.db.session import get_db

router = APIRouter(prefix="/api/v1", tags=["jobs"])


# ── Request / Response models ─────────────────────────────────────────────────

class CreateJobRequest(BaseModel):
    raw_jd_text: str | None = None
    raw_jd_url: str | None = None


class DistributeRequest(BaseModel):
    channels: list[str] = Field(default_factory=list)
    channel_config: dict = Field(default_factory=dict)


class JobResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    title: str
    status: str
    collection_email: str | None
    created_at: str
    posted_at: str | None

    class Config:
        from_attributes = True


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/jobs", status_code=status.HTTP_202_ACCEPTED)
def create_job(
    body: CreateJobRequest,
    user: Annotated[TokenData, Depends(get_current_user)],
):
    """Create a job and kick off JD extraction. Returns job_id immediately."""
    if not body.raw_jd_text and not body.raw_jd_url:
        raise HTTPException(status_code=400, detail="Provide raw_jd_text or raw_jd_url")

    job_id = uuid.uuid4()

    with get_db() as db:
        job = Job(
            id=job_id,
            tenant_id=user.tenant_id,
            created_by=user.recruiter_id,
            title="Pending extraction",
            location={},
            status="draft",
            raw_jd_text=body.raw_jd_text,
        )
        db.add(job)

    log_event(
        EventType.JD_CREATED,
        tenant_id=user.tenant_id,
        user_id=user.recruiter_id,
        entity_type="job",
        entity_id=job_id,
        data={"source": "text" if body.raw_jd_text else "url"},
    )

    publish(
        Topics.JD_APPROVED,
        {"job_id": str(job_id), "raw_jd_text": body.raw_jd_text, "raw_jd_url": body.raw_jd_url},
        tenant_id=user.tenant_id,
    )

    return {"job_id": str(job_id), "status": "draft", "message": "JD extraction started"}


@router.get("/jobs/{job_id}")
def get_job(
    job_id: uuid.UUID,
    user: Annotated[TokenData, Depends(get_current_user)],
):
    with get_db() as db:
        job = db.query(Job).filter_by(id=job_id, tenant_id=user.tenant_id).first()
        if job is None:
            raise HTTPException(status_code=404, detail="Job not found")

        posts = db.query(ChannelPost).filter_by(job_id=job_id).all()
        channel_status = {
            p.channel: {"status": p.delivery_status, "post_url": p.post_url}
            for p in posts
        }

        # Karnataka salary-disclosure warning (PE-001)
        state = str((job.location or {}).get("state") or "")
        karnataka_salary_warning = (
            state.lower() == "karnataka"
            and not job.salary_disclosed
            and not job.salary_min
        )

        return {
            "id": str(job.id),
            "title": job.title,
            "status": job.status,
            "department": job.department,
            "seniority": job.seniority,
            "location": job.location,
            "must_haves": job.must_haves,
            "nice_to_haves": job.nice_to_haves,
            "responsibilities": job.responsibilities,
            "tech_stack": job.tech_stack,
            "salary_min": job.salary_min,
            "salary_max": job.salary_max,
            "salary_currency": job.salary_currency,
            "salary_disclosed": job.salary_disclosed,
            "bias_flags": job.bias_flags,
            "scoring_rubric": job.scoring_rubric,
            "shortlist_size": job.shortlist_size,
            "collection_email": job.collection_email,
            "channel_status": channel_status,
            "karnataka_salary_warning": karnataka_salary_warning,
            "created_at": job.created_at.isoformat(),
            "posted_at": job.posted_at.isoformat() if job.posted_at else None,
        }


@router.patch("/jobs/{job_id}", status_code=status.HTTP_200_OK)
def update_job(
    job_id: uuid.UUID,
    body: dict,
    user: Annotated[TokenData, Depends(get_current_user)],
):
    """Partial update for job fields (status, title, etc.)."""
    UPDATABLE = {"status", "title", "department", "seniority", "location", "must_haves",
                 "nice_to_haves", "responsibilities", "tech_stack", "salary_min", "salary_max",
                 "salary_currency", "salary_disclosed", "scoring_rubric", "shortlist_size"}
    with get_db() as db:
        job = db.query(Job).filter_by(id=job_id, tenant_id=user.tenant_id).first()
        if job is None:
            raise HTTPException(status_code=404, detail="Job not found")
        for key, value in body.items():
            if key in UPDATABLE:
                setattr(job, key, value)
    return {"job_id": str(job_id), "updated": list(body.keys())}


@router.post("/jobs/{job_id}/confirm", status_code=status.HTTP_200_OK)
def confirm_job(
    job_id: uuid.UUID,
    user: Annotated[TokenData, Depends(get_current_user)],
):
    """Recruiter confirms the AI-extracted JD.  Transitions job to 'approved'
    so the Distribute button becomes available in the UI."""
    with get_db() as db:
        job = db.query(Job).filter_by(id=job_id, tenant_id=user.tenant_id).first()
        if job is None:
            raise HTTPException(status_code=404, detail="Job not found")
        if job.status not in ("draft", "extraction_complete"):
            raise HTTPException(
                status_code=400,
                detail=f"Job cannot be confirmed from status '{job.status}'",
            )
        job.status = "approved"

    log_event(
        EventType.JD_CONFIRMED,
        tenant_id=user.tenant_id,
        user_id=user.recruiter_id,
        entity_type="job",
        entity_id=job_id,
        data={"confirmed_by": str(user.recruiter_id)},
    )

    return {"job_id": str(job_id), "status": "approved"}


@router.post("/jobs/{job_id}/distribute", status_code=status.HTTP_202_ACCEPTED)
def distribute_job(
    job_id: uuid.UUID,
    body: DistributeRequest,
    user: Annotated[TokenData, Depends(get_current_user)],
):
    """Trigger Distribution Orchestrator. Job must be in 'approved' status."""
    with get_db() as db:
        job = db.query(Job).filter_by(id=job_id, tenant_id=user.tenant_id).first()
        if job is None:
            raise HTTPException(status_code=404, detail="Job not found")
        if job.status != "approved":
            raise HTTPException(
                status_code=400,
                detail=f"Job must be in 'approved' status to distribute. Current: {job.status}",
            )
        job.status = "posted"
        job.distribution_channels = body.channels
        job.channel_config = body.channel_config

    log_event(
        EventType.DISTRIBUTION_STARTED,
        tenant_id=user.tenant_id,
        user_id=user.recruiter_id,
        entity_type="job",
        entity_id=job_id,
        data={"channels": body.channels},
    )

    publish(
        Topics.DISTRIBUTION_STARTED,
        {"job_id": str(job_id), "channels": body.channels, "channel_config": body.channel_config},
        tenant_id=user.tenant_id,
    )

    return {"job_id": str(job_id), "status": "posted", "channels_queued": body.channels}


@router.get("/jobs/{job_id}/posts")
def list_posts(
    job_id: uuid.UUID,
    user: Annotated[TokenData, Depends(get_current_user)],
):
    with get_db() as db:
        posts = db.query(ChannelPost).filter_by(job_id=job_id, tenant_id=user.tenant_id).all()
        return [
            {
                "id": str(p.id),
                "channel": p.channel,
                "delivery_status": p.delivery_status,
                "post_url": p.post_url,
                "posted_at": p.posted_at.isoformat() if p.posted_at else None,
                "disclosure_included": p.disclosure_included,
                "metrics": p.metrics,
            }
            for p in posts
        ]


@router.get("/jobs/{job_id}/applications")
def list_applications(
    job_id: uuid.UUID,
    user: Annotated[TokenData, Depends(get_current_user)],
    channel: str | None = None,
    status: str | None = None,
):
    from packages.db.models import Candidate

    with get_db() as db:
        q = db.query(Candidate).filter_by(job_id=job_id, tenant_id=user.tenant_id)
        if channel:
            q = q.filter_by(source_channel=channel)
        if status:
            q = q.filter_by(status=status)
        candidates = q.order_by(Candidate.applied_at.desc()).all()

        return [
            {
                "id": str(c.id),
                "name": c.name,
                "email": c.email,
                "source_channel": c.source_channel,
                "status": c.status,
                "applied_at": c.applied_at.isoformat(),
                "parse_confidence": c.parse_confidence,
                "parse_flagged": c.parse_flagged,
            }
            for c in candidates
        ]


@router.post("/jobs/{job_id}/score", status_code=status.HTTP_202_ACCEPTED)
def trigger_scoring(
    job_id: uuid.UUID,
    user: Annotated[TokenData, Depends(get_current_user)],
):
    """Queue all parsed candidates for scoring. Async — check /shortlist for results."""
    with get_db() as db:
        job = db.query(Job).filter_by(id=job_id, tenant_id=user.tenant_id).first()
        if job is None:
            raise HTTPException(status_code=404, detail="Job not found")
        job.status = "scoring"

    # Publish CV_PARSED with job-level trigger so the worker runs batch scoring
    publish(
        Topics.CV_PARSED,
        {"job_id": str(job_id), "trigger": "manual_score_request"},
        tenant_id=user.tenant_id,
    )

    return {"job_id": str(job_id), "status": "scoring", "message": "Scoring queued"}


@router.get("/jobs/{job_id}/shortlist")
def get_shortlist(
    job_id: uuid.UUID,
    user: Annotated[TokenData, Depends(get_current_user)],
):
    from packages.db.models import CandidateScore, Candidate

    with get_db() as db:
        scores = (
            db.query(CandidateScore)
            .filter_by(job_id=job_id, tenant_id=user.tenant_id)
            .order_by(CandidateScore.rank)
            .all()
        )
        result = []
        for s in scores:
            c = db.get(Candidate, s.candidate_id)
            result.append({
                "score_id": str(s.id),
                "candidate_id": str(s.candidate_id),
                "name": c.name if c else None,
                "rank": s.rank,
                "composite_score": s.composite_score,
                "dimension_scores": s.dimension_scores,
                "justification": s.justification,
                "strengths": s.strengths,
                "risks": s.risks,
                "near_miss_flag": s.near_miss_flag,
                "recruiter_status": s.recruiter_status,
                "nps_thumb": (s.nps_thumb == 1) if s.nps_thumb is not None else None,
                "source_channel": c.source_channel if c else None,
            })
        return result


@router.get("/jobs/{job_id}/linkedin-draft")
def get_linkedin_draft(
    job_id: uuid.UUID,
    user: Annotated[TokenData, Depends(get_current_user)],
):
    """Generate a LinkedIn post draft via LLM from the real job data.
    Non-destructive — no DB writes. Requires job to be in approved/posted/collecting status."""
    from packages.db.models import Tenant as TenantModel
    from packages.agents.distribution.linkedin.post_builder import build_post

    with get_db() as db:
        job = db.query(Job).filter_by(id=job_id, tenant_id=user.tenant_id).first()
        if job is None:
            raise HTTPException(status_code=404, detail="Job not found")
        if job.status not in ("approved", "posted", "collecting", "shortlisted", "closed"):
            raise HTTPException(
                status_code=400,
                detail=f"Job must be approved before generating a post draft (current: {job.status})",
            )

        tenant = db.get(TenantModel, user.tenant_id)
        company_name = tenant.name if tenant else "the company"

        role_id = str(job_id)[:8].upper()
        job_dict = {
            "title": job.title,
            "location": job.location,
            "responsibilities": job.responsibilities,
            "must_haves": job.must_haves,
            "tech_stack": job.tech_stack,
            "salary_min": job.salary_min,
            "salary_max": job.salary_max,
        }

    try:
        post_body = build_post(job_dict, company_name, role_id)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Post generation failed: {exc}") from exc

    return {"post_body": post_body, "character_count": len(post_body)}


@router.post("/jobs/{job_id}/upload-cv", status_code=status.HTTP_202_ACCEPTED)
async def upload_cv(
    job_id: uuid.UUID,
    user: Annotated[TokenData, Depends(get_current_user)],
    file: UploadFile = File(...),
    email: str = Form(...),
    name: str = Form(""),
    source_channel: str = Form("direct"),
):
    """Upload a CV file for a job. Creates a Candidate record and queues parsing."""
    from packages.db.models import Candidate
    from packages.storage import client as storage

    # Verify job exists and belongs to this tenant
    with get_db() as db:
        job = db.query(Job).filter_by(id=job_id, tenant_id=user.tenant_id).first()
        if job is None:
            raise HTTPException(status_code=404, detail="Job not found")

    # Read and validate file
    data = await file.read()
    if len(data) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")
    if len(data) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large (max 10 MB)")

    filename = file.filename or "cv.pdf"
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "pdf"
    if ext not in {"pdf", "doc", "docx"}:
        raise HTTPException(status_code=415, detail="Only PDF, DOC, and DOCX files are accepted")

    # Upload to object storage
    ts = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%S")
    key = storage.cv_key(str(user.tenant_id), str(job_id), email, ts, ext)
    try:
        storage.upload(key, data, content_type=file.content_type or "application/octet-stream")
    except KeyError:
        raise HTTPException(
            status_code=503,
            detail="Object storage not configured. Set MINIO_ENDPOINT, MINIO_ACCESS_KEY, MINIO_SECRET_KEY.",
        )
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Storage unavailable: {exc}") from exc

    # Upsert candidate record
    with get_db() as db:
        existing = db.query(Candidate).filter_by(
            job_id=job_id, tenant_id=user.tenant_id, email=email
        ).first()

        if existing:
            existing.cv_file_key = key
            existing.cv_original_filename = filename
            existing.status = "received"
            candidate_id = existing.id
        else:
            candidate_id = uuid.uuid4()
            candidate = Candidate(
                id=candidate_id,
                tenant_id=user.tenant_id,
                job_id=job_id,
                email=email,
                name=name or None,
                source_channel=source_channel,
                cv_file_key=key,
                cv_original_filename=filename,
                status="received",
                dpdp_consent=True,
                consent_ts=datetime.datetime.utcnow(),
            )
            db.add(candidate)

    log_event(
        EventType.APPLICATION_RECEIVED,
        tenant_id=user.tenant_id,
        entity_type="candidate",
        entity_id=candidate_id,
        data={"email": email, "source_channel": source_channel, "filename": filename},
    )

    publish(
        Topics.APPLICATION_RECEIVED,
        {
            "candidate_id": str(candidate_id),
            "job_id": str(job_id),
            "cv_file_key": key,
            "email": email,
        },
        tenant_id=user.tenant_id,
    )

    return {
        "candidate_id": str(candidate_id),
        "status": "received",
        "message": "CV received and queued for parsing",
    }


@router.get("/_diag/screenshot")
def get_diag_screenshot(
    key: str,
    user: Annotated[TokenData, Depends(get_current_user)],
):
    """Return a presigned URL for a diagnostic screenshot in object storage.

    Only allows keys under the `diag/` prefix.
    """
    if not key.startswith("diag/"):
        raise HTTPException(status_code=400, detail="key must start with diag/")
    from packages.storage import client as storage
    try:
        url = storage.presigned_url(key, expires_hours=1)
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"key": key, "url": url}


@router.get("/jobs/{job_id}/audit")
def get_audit_trail(
    job_id: uuid.UUID,
    user: Annotated[TokenData, Depends(get_current_user)],
):
    with get_db() as db:
        events = (
            db.query(AuditEvent)
            .filter_by(tenant_id=user.tenant_id, entity_id=job_id)
            .order_by(AuditEvent.created_at)
            .all()
        )
        return [
            {
                "id": str(e.id),
                "event_type": e.event_type,
                "entity_type": e.entity_type,
                "channel": e.channel,
                "content_hash": e.content_hash,
                "data": e.data,
                "created_at": e.created_at.isoformat(),
            }
            for e in events
        ]
