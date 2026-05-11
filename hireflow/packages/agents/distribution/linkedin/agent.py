"""
LinkedIn Channel Agent — LI-001 through LI-009.

Orchestration flow:
  1. Check posting quota (AR-001: max 3-4 posts/day, 90-min spacing)
  2. Build post body via LLM (LI-002)
  3. Present draft to recruiter via API — wait for "Approve & Post" (LI-003)
  4. Load Riya account credentials from vault (LI-001)
  5. Post via Playwright (LI-006)
  6. Save screenshot + post URL to S3 + audit log (LI-006)
  7. Update cookies in vault

Recruiter approval is enforced at the API layer (POST /jobs/{id}/distribute
already requires approved status).  This agent receives posts that the
recruiter has approved and executes them.
"""

import hashlib
import uuid
from datetime import datetime, timezone

from packages.agents.distribution.linkedin.browser import (
    LinkedInBrowser,
    MFARequiredException,
    CAPTCHADetectedException,
    PostResult,
)
from packages.agents.distribution.linkedin.post_builder import build_post
from packages.audit.logger import EventType, log_event, log_disclosure
from packages.bus.publisher import publish
from packages.bus.topics import Topics
from packages.db.models import ChannelPost, Job, PersonaAccount
from packages.db.session import get_db
from packages.persona.account_manager import can_post, record_post, get_active_primary
from packages.storage import client as storage
from packages.vault.client import get_secret_json, put_secret
import json


def run(job_id: str, tenant_id: str, company_name: str) -> dict:
    """Post a job to LinkedIn.  Returns a result dict."""

    job_uuid = uuid.UUID(job_id)
    tenant_uuid = uuid.UUID(tenant_id)

    # ── Load job from DB ──────────────────────────────────────────────────────
    with get_db() as db:
        job = db.get(Job, job_uuid)
        if job is None:
            raise ValueError(f"Job {job_id} not found")
        job_dict = {
            "title": job.title,
            "location": job.location,
            "responsibilities": job.responsibilities,
            "must_haves": job.must_haves,
            "tech_stack": job.tech_stack,
            "salary_min": job.salary_min,
            "salary_max": job.salary_max,
        }

    # role_id is short string used in the apply email
    role_id = str(job_uuid)[:8].upper()

    # ── Get active Riya account ───────────────────────────────────────────────
    account = get_active_primary(platform="linkedin")
    if account is None:
        raise RuntimeError("No active LinkedIn persona account available")

    allowed, reason = can_post(account)
    if not allowed:
        # Queue for next day — create a deferred channel_post record
        _create_channel_post_record(
            job_uuid, tenant_uuid, account,
            delivery_status="quarantined",
            error_message=f"Post quota exceeded: {reason}",
        )
        return {"status": "queued", "reason": reason}

    # ── Build post body ───────────────────────────────────────────────────────
    post_body = build_post(job_dict, company_name, role_id)

    # ── Get credentials from vault ────────────────────────────────────────────
    credentials = get_secret_json(account.vault_secret_key)

    # ── Post via Playwright ───────────────────────────────────────────────────
    try:
        with LinkedInBrowser(credentials) as browser:
            result: PostResult = browser.post(post_body)

    except MFARequiredException as exc:
        log_event(
            EventType.AGENT_ERROR,
            tenant_id=tenant_uuid,
            entity_type="persona_account",
            entity_id=account.id,
            data={"error": "MFA_REQUIRED", "detail": str(exc)},
        )
        publish(Topics.PERSONA_ALERT, {
            "account_id": str(account.id),
            "severity": "yellow",
            "message": f"MFA challenge during posting for job {job_id}",
        }, tenant_id=tenant_id)
        raise

    except CAPTCHADetectedException as exc:
        log_event(
            EventType.AGENT_ERROR,
            tenant_id=tenant_uuid,
            entity_type="persona_account",
            entity_id=account.id,
            data={"error": "CAPTCHA_DETECTED", "detail": str(exc)},
        )
        publish(Topics.PERSONA_ALERT, {
            "account_id": str(account.id),
            "severity": "red",
            "message": f"CAPTCHA detected — initiating failover for job {job_id}",
        }, tenant_id=tenant_id)
        raise

    # ── Store screenshot in S3 ────────────────────────────────────────────────
    post_record_id = uuid.uuid4()
    screenshot_s3_key = storage.screenshot_key(job_id, str(post_record_id))
    storage.upload(screenshot_s3_key, result.screenshot_bytes, "image/png")

    # ── Save updated cookies back to vault ────────────────────────────────────
    credentials["cookies"] = result.updated_cookies
    put_secret(account.vault_secret_key, json.dumps(credentials))

    # ── Record post in DB ─────────────────────────────────────────────────────
    content_hash = hashlib.sha256(post_body.encode()).hexdigest()

    with get_db() as db:
        cp = ChannelPost(
            id=post_record_id,
            job_id=job_uuid,
            tenant_id=tenant_uuid,
            channel="linkedin",
            post_url=result.post_url,
            post_id=result.post_id,
            posted_at=datetime.now(timezone.utc).replace(tzinfo=None),
            posted_by_persona=account.persona_name,
            content_hash=content_hash,
            content_preview=post_body[:500],
            disclosure_included=True,
            delivery_status="delivered" if result.post_url else "sent",
            screenshot_key=screenshot_s3_key,
        )
        db.add(cp)

    # ── Increment post counter ────────────────────────────────────────────────
    record_post(account.id)

    # ── Audit: disclosure-bearing message (PE-007) ────────────────────────────
    log_disclosure(
        channel="linkedin",
        content=post_body,
        tenant_id=tenant_uuid,
        entity_id=post_record_id,
        entity_type="channel_post",
        data={"post_url": result.post_url, "post_id": result.post_id},
    )

    log_event(
        EventType.CHANNEL_POST_DELIVERED,
        tenant_id=tenant_uuid,
        entity_type="channel_post",
        entity_id=post_record_id,
        channel="linkedin",
        data={"post_url": result.post_url, "persona": account.persona_name},
    )

    publish(Topics.CHANNEL_POSTED, {
        "job_id": job_id,
        "channel": "linkedin",
        "post_id": str(post_record_id),
        "post_url": result.post_url,
        "status": "delivered",
    }, tenant_id=tenant_id)

    return {
        "status": "delivered",
        "post_url": result.post_url,
        "post_id": str(post_record_id),
        "channel": "linkedin",
    }


def _create_channel_post_record(
    job_id: uuid.UUID,
    tenant_id: uuid.UUID,
    account: PersonaAccount,
    delivery_status: str,
    error_message: str,
) -> None:
    with get_db() as db:
        cp = ChannelPost(
            id=uuid.uuid4(),
            job_id=job_id,
            tenant_id=tenant_id,
            channel="linkedin",
            posted_by_persona=account.persona_name,
            disclosure_included=False,
            delivery_status=delivery_status,
            error_message=error_message,
        )
        db.add(cp)
