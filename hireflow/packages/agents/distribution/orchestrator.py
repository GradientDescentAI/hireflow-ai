"""
Distribution Orchestrator — coordinates all channel agents in parallel.

For MVP, only LinkedIn is active.  Each channel agent is called
in a thread pool so failures in one channel don't block others.

The orchestrator is idempotent per channel: if a ChannelPost record
already exists for (job_id, channel) with status='delivered', that channel
is skipped on retry.
"""

import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

from packages.audit.logger import EventType, log_event
from packages.bus.publisher import publish
from packages.bus.topics import Topics
from packages.db.models import ChannelPost, Job
from packages.db.session import get_db


def run(job_id: str, tenant_id: str, channels: list[str], channel_config: dict) -> dict:
    """Fan out to all requested channels. Returns aggregated results."""

    job_uuid = uuid.UUID(job_id)
    tenant_uuid = uuid.UUID(tenant_id)

    with get_db() as db:
        job = db.get(Job, job_uuid)
        if job is None:
            raise ValueError(f"Job {job_id} not found")
        company_name = _get_company_name(tenant_uuid, db)

        # Skip channels already successfully posted
        delivered = {
            cp.channel
            for cp in db.query(ChannelPost)
            .filter_by(job_id=job_uuid, delivery_status="delivered")
            .all()
        }

    pending_channels = [c for c in channels if c not in delivered]

    results: dict[str, dict] = {c: {"status": "skipped", "reason": "already_delivered"} for c in delivered}

    if not pending_channels:
        return {"job_id": job_id, "results": results}

    log_event(
        EventType.DISTRIBUTION_STARTED,
        tenant_id=tenant_uuid,
        entity_type="job",
        entity_id=job_uuid,
        data={"channels": pending_channels},
    )

    def _run_channel(channel: str) -> tuple[str, dict]:
        try:
            return channel, _dispatch_channel(channel, job_id, tenant_id, company_name, channel_config)
        except Exception as exc:
            log_event(
                EventType.CHANNEL_POST_FAILED,
                tenant_id=tenant_uuid,
                entity_type="job",
                entity_id=job_uuid,
                channel=channel,
                data={"error": str(exc)},
            )
            publish(Topics.CHANNEL_POSTED, {
                "job_id": job_id,
                "channel": channel,
                "status": "failed",
                "error": str(exc),
            }, tenant_id=tenant_id)
            return channel, {"status": "failed", "error": str(exc)}

    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = {pool.submit(_run_channel, ch): ch for ch in pending_channels}
        for future in as_completed(futures):
            channel, result = future.result()
            results[channel] = result

    # Update job status to "collecting" if at least one channel succeeded
    success_count = sum(1 for r in results.values() if r.get("status") == "delivered")
    if success_count > 0:
        with get_db() as db:
            job = db.get(Job, job_uuid)
            if job:
                job.status = "collecting"
                job.posted_at = datetime.now(timezone.utc).replace(tzinfo=None)
                # Provision the collection email address
                role_id = str(job_uuid)[:8].upper()
                job.collection_email = f"apply-{role_id}@hireflow.in"

    return {"job_id": job_id, "channels_attempted": len(pending_channels), "results": results}


def _dispatch_channel(
    channel: str, job_id: str, tenant_id: str, company_name: str, channel_config: dict
) -> dict:
    """Route to the appropriate channel agent."""
    if channel == "linkedin":
        from packages.agents.distribution.linkedin.agent import run as linkedin_run
        return linkedin_run(job_id, tenant_id, company_name)

    # Beta channels — stub for now
    if channel in ("whatsapp", "telegram", "naukri", "indeed", "internshala", "colleges", "referral"):
        return {"status": "skipped", "reason": f"{channel} not yet available in MVP"}

    return {"status": "skipped", "reason": f"Unknown channel: {channel}"}


def _get_company_name(tenant_id: uuid.UUID, db) -> str:
    from packages.db.models import Tenant
    tenant = db.get(Tenant, tenant_id)
    return tenant.name if tenant else "the company"
