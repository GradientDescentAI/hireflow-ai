"""
Email attachment extractor — AC-003 to AC-006.

Validates attachments (PDF / DOCX / DOC, ≤10MB, ≤3 per email),
stores them in object storage, and creates the Candidate record in DB.
"""

import re
import uuid
from datetime import datetime, timedelta, timezone

from packages.agents.collection.imap_listener import RawEmail
from packages.audit.logger import EventType, log_event
from packages.db.models import Candidate
from packages.db.session import get_db
from packages.storage import client as storage

_ALLOWED_TYPES = {
    "application/pdf": "pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "application/msword": "doc",
}
_MAX_SIZE_BYTES = 10 * 1024 * 1024   # 10MB
_MAX_ATTACHMENTS = 3
_RETENTION_DAYS = 365                 # DPDP: 12 months default


def _infer_ext(filename: str, content_type: str) -> str:
    for suffix in (".pdf", ".docx", ".doc"):
        if filename.lower().endswith(suffix):
            return suffix.lstrip(".")
    return _ALLOWED_TYPES.get(content_type, "bin")


def process_email(
    raw: "RawEmail",
    job_id: str,
    tenant_id: str,
    role_id: str,
) -> dict:
    """Process one inbound email.  Returns a result dict."""

    job_uuid = uuid.UUID(job_id)
    tenant_uuid = uuid.UUID(tenant_id)

    # ── Subject match ─────────────────────────────────────────────────────────
    if not re.search(rf"APPLY[-_]{re.escape(role_id)}", raw.subject, re.IGNORECASE):
        _quarantine(raw, job_uuid, tenant_uuid, "subject_mismatch")
        log_event(
            EventType.APPLICATION_QUARANTINED,
            tenant_id=tenant_uuid,
            entity_type="job",
            entity_id=job_uuid,
            data={"sender": raw.sender_email, "subject": raw.subject, "reason": "subject_mismatch"},
        )
        return {"status": "quarantined", "reason": "subject_mismatch"}

    # ── Deduplication (AC-006) ────────────────────────────────────────────────
    with get_db() as db:
        existing = db.query(Candidate).filter_by(job_id=job_uuid, email=raw.sender_email).first()
        if existing:
            existing.is_duplicate = True
            log_event(
                EventType.APPLICATION_DUPLICATE,
                tenant_id=tenant_uuid,
                entity_type="candidate",
                entity_id=existing.id,
                data={"sender": raw.sender_email},
            )
            return {"status": "duplicate", "candidate_id": str(existing.id)}

    # ── Validate attachments ──────────────────────────────────────────────────
    valid_attachments = []
    for att in raw.attachments[:_MAX_ATTACHMENTS]:
        if len(att["data"]) > _MAX_SIZE_BYTES:
            continue
        if att["content_type"] not in _ALLOWED_TYPES and not any(
            att["filename"].lower().endswith(ext) for ext in (".pdf", ".docx", ".doc")
        ):
            continue
        valid_attachments.append(att)

    if not valid_attachments:
        return {"status": "missing_attachment", "sender": raw.sender_email}

    # ── Store first CV in object storage (AC-004) ─────────────────────────────
    att = valid_attachments[0]
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    ext = _infer_ext(att["filename"], att["content_type"])
    s3_key = storage.cv_key(tenant_id, job_id, raw.sender_email, ts, ext)
    storage.upload(s3_key, att["data"], att["content_type"])

    # ── Create Candidate record ───────────────────────────────────────────────
    candidate_id = uuid.uuid4()
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    retention = now + timedelta(days=_RETENTION_DAYS)

    with get_db() as db:
        candidate = Candidate(
            id=candidate_id,
            tenant_id=tenant_uuid,
            job_id=job_uuid,
            email=raw.sender_email,
            name=raw.sender_name or None,
            source_channel=_infer_channel(raw),
            applied_at=now,
            cv_file_key=s3_key,
            cv_original_filename=att["filename"],
            cover_letter_text=raw.body_text[:5000] if raw.body_text else None,
            dpdp_consent=True,              # applying constitutes consent under DPDP
            consent_ts=now,
            retention_until=retention,
            status="received",
        )
        db.add(candidate)

    log_event(
        EventType.APPLICATION_RECEIVED,
        tenant_id=tenant_uuid,
        entity_type="candidate",
        entity_id=candidate_id,
        data={"email": raw.sender_email, "s3_key": s3_key, "source_channel": candidate.source_channel},
    )

    return {
        "status": "received",
        "candidate_id": str(candidate_id),
        "s3_key": s3_key,
    }


def _quarantine(raw: "RawEmail", job_id: uuid.UUID, tenant_id: uuid.UUID, reason: str) -> None:
    pass  # In production: write to a quarantine table for recruiter review


def _infer_channel(raw: "RawEmail") -> str:
    """Heuristically tag the source channel from email content."""
    body = (raw.body_text or "").lower()
    if "linkedin" in body:
        return "linkedin"
    if "naukri" in body:
        return "naukri"
    if "indeed" in body:
        return "indeed"
    if "whatsapp" in body:
        return "whatsapp"
    if "telegram" in body:
        return "telegram"
    return "direct"
