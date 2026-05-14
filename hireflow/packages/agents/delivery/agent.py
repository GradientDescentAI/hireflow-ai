"""
Delivery Agent — SL-003, SL-004, PE-003.

Notifies the recruiter that their shortlist is ready and updates job status.

Flow:
  1. Load job + recruiter contact details
  2. Send shortlist notification email (PE-003: AI disclosure in footer)
  3. Update Job.status = 'shortlisted' (idempotent — may already be set by evaluation agent)
  4. Log SHORTLIST_READY
  5. Publish SHORTLIST_READY (if not already published by evaluation agent)
"""

import os
import uuid
from datetime import datetime, timezone

from packages.agents.delivery.email_sender import send_shortlist_notification
from packages.audit.logger import EventType, log_event
from packages.bus.publisher import publish
from packages.bus.topics import Topics
from packages.db.models import CandidateScore, Job, Recruiter
from packages.db.session import get_db


def run(job_id: str, tenant_id: str) -> dict:
    """Deliver shortlist notification to the recruiter."""

    job_uuid = uuid.UUID(job_id)
    tenant_uuid = uuid.UUID(tenant_id)

    with get_db() as db:
        job = db.get(Job, job_uuid)
        if job is None:
            raise ValueError(f"Job {job_id} not found")

        if job.status not in ("shortlisted", "scoring"):
            return {
                "job_id": job_id,
                "status": "skipped",
                "reason": f"job.status is '{job.status}', expected shortlisted/scoring",
            }

        recruiter = db.get(Recruiter, job.created_by)
        if recruiter is None:
            raise ValueError(f"Recruiter {job.created_by} not found for job {job_id}")

        shortlist_count = (
            db.query(CandidateScore)
            .filter_by(job_id=job_uuid)
            .filter(CandidateScore.rank <= 10)
            .count()
        )

        bias_audit_passed = True
        shortlisted_scores = (
            db.query(CandidateScore)
            .filter_by(job_id=job_uuid)
            .filter(CandidateScore.rank <= 10)
            .all()
        )
        if shortlisted_scores:
            bias_audit_passed = all(
                s.bias_audit_passed for s in shortlisted_scores
                if s.bias_audit_passed is not None
            )

        recruiter_email = recruiter.email
        recruiter_name = recruiter.name or recruiter.email.split("@")[0]
        job_title = job.title

    # ── Send notification email ───────────────────────────────────────────────
    app_base_url = os.environ.get("APP_BASE_URL", "https://app.hireflow.in")
    email_sent = send_shortlist_notification(
        recruiter_email=recruiter_email,
        recruiter_name=recruiter_name,
        job_title=job_title,
        job_id=job_id,
        shortlist_size=shortlist_count,
        bias_audit_passed=bias_audit_passed,
        app_base_url=app_base_url,
    )

    # ── Ensure job status is shortlisted ─────────────────────────────────────
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    with get_db() as db:
        job = db.get(Job, job_uuid)
        if job and job.status != "shortlisted":
            job.status = "shortlisted"
            job.updated_at = now

    log_event(
        EventType.SHORTLIST_READY,
        tenant_id=tenant_uuid,
        entity_type="job",
        entity_id=job_uuid,
        data={
            "shortlist_size": shortlist_count,
            "recruiter_notified": email_sent,
            "bias_audit_passed": bias_audit_passed,
        },
    )

    if not email_sent:
        log_event(
            EventType.AGENT_ERROR,
            tenant_id=tenant_uuid,
            entity_type="job",
            entity_id=job_uuid,
            data={"error": "SendGrid delivery failed", "stage": "delivery"},
        )

    publish(
        Topics.SHORTLIST_READY,
        {
            "job_id": job_id,
            "shortlist_size": shortlist_count,
            "recruiter_notified": email_sent,
        },
        tenant_id=tenant_id,
    )

    return {
        "job_id": job_id,
        "status": "delivered",
        "shortlist_size": shortlist_count,
        "recruiter_notified": email_sent,
        "bias_audit_passed": bias_audit_passed,
    }
