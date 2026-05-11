"""
Immutable audit logger.

Every agent action, scoring decision, disclosure event, and override is
written here. The audit_events table has a WORM trigger — no UPDATE or DELETE
is permitted at the database level.

Callers always use log_event(); they never write to audit_events directly.
"""

import hashlib
import uuid
from datetime import datetime, timezone
from typing import Any

from packages.db.models import AuditEvent
from packages.db.session import SessionLocal


# ── Event type constants ──────────────────────────────────────────────────────

class EventType:
    # JD lifecycle
    JD_CREATED = "jd.created"
    JD_EXTRACTION_COMPLETE = "jd.extraction.complete"
    JD_CONFIRMED = "jd.confirmed"

    # Distribution
    DISTRIBUTION_STARTED = "distribution.started"
    CHANNEL_POST_CREATED = "channel_post.created"
    CHANNEL_POST_FAILED = "channel_post.failed"
    CHANNEL_POST_DELIVERED = "channel_post.delivered"

    # Disclosure (PE-007: every disclosure-bearing message must be logged)
    DISCLOSURE_SENT = "disclosure.sent"

    # Application collection
    APPLICATION_RECEIVED = "application.received"
    APPLICATION_QUARANTINED = "application.quarantined"
    APPLICATION_DUPLICATE = "application.duplicate"
    ACKNOWLEDGEMENT_SENT = "acknowledgement.sent"

    # Parsing
    CV_PARSING_STARTED = "cv.parsing.started"
    CV_PARSING_COMPLETE = "cv.parsing.complete"
    CV_PARSE_FLAGGED = "cv.parse.flagged"

    # Scoring
    SCORING_STARTED = "scoring.started"
    SCORING_COMPLETE = "scoring.complete"
    SCORE_OVERRIDE = "score.override"
    BIAS_AUDIT_RUN = "bias_audit.run"
    BIAS_AUDIT_FLAGGED = "bias_audit.flagged"

    # Shortlist
    SHORTLIST_GENERATED = "shortlist.generated"
    SHORTLIST_DELIVERED = "shortlist.delivered"
    CANDIDATE_APPROVED = "candidate.approved"
    CANDIDATE_REJECTED = "candidate.rejected"
    CANDIDATE_HELD = "candidate.held"
    NPS_THUMB_RECORDED = "nps.thumb.recorded"

    # Persona / account
    PERSONA_HEALTH_CHECK = "persona.health_check"
    PERSONA_ACCOUNT_WARNING = "persona.account.warning"
    PERSONA_ACCOUNT_BANNED = "persona.account.banned"
    PERSONA_FAILOVER_INITIATED = "persona.failover.initiated"

    # System
    AGENT_ERROR = "agent.error"


def _content_hash(content: str) -> str:
    return hashlib.sha256(content.encode()).hexdigest()


def log_event(
    event_type: str,
    *,
    tenant_id: uuid.UUID | str | None = None,
    user_id: uuid.UUID | str | None = None,
    entity_type: str | None = None,
    entity_id: uuid.UUID | str | None = None,
    channel: str | None = None,
    disclosure_content: str | None = None,
    data: dict[str, Any] | None = None,
) -> AuditEvent:
    """Write one immutable audit event. Returns the persisted record."""

    def _to_uuid(val: uuid.UUID | str | None) -> uuid.UUID | None:
        if val is None:
            return None
        return val if isinstance(val, uuid.UUID) else uuid.UUID(str(val))

    event = AuditEvent(
        id=uuid.uuid4(),
        tenant_id=_to_uuid(tenant_id),
        user_id=_to_uuid(user_id),
        event_type=event_type,
        entity_type=entity_type,
        entity_id=_to_uuid(entity_id),
        channel=channel,
        content_hash=_content_hash(disclosure_content) if disclosure_content else None,
        data=data or {},
        created_at=datetime.now(timezone.utc).replace(tzinfo=None),
    )

    db = SessionLocal()
    try:
        db.add(event)
        db.commit()
        db.refresh(event)
        return event
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def log_disclosure(
    channel: str,
    content: str,
    *,
    tenant_id: uuid.UUID | str | None = None,
    entity_id: uuid.UUID | str | None = None,
    entity_type: str = "channel_post",
    data: dict | None = None,
) -> AuditEvent:
    """Convenience wrapper for PE-007 — every disclosure-bearing message."""
    return log_event(
        EventType.DISCLOSURE_SENT,
        tenant_id=tenant_id,
        entity_type=entity_type,
        entity_id=entity_id,
        channel=channel,
        disclosure_content=content,
        data={"channel": channel, **(data or {})},
    )
