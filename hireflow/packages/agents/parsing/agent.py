"""
Parsing Agent — RP-001 to RP-007.

For each received application:
  1. Download CV file from object storage
  2. Extract text (PDF → pdfplumber, DOCX → python-docx)
  3. Strip PII, call LLM for structured extraction (RP-005)
  4. Flag low-confidence parses (RP-004)
  5. Update Candidate record in DB
  6. Publish CV_PARSED event
"""

import uuid
from datetime import datetime, timezone

from packages.agents.parsing.docx_parser import parse_docx, parse_doc
from packages.agents.parsing.llm_extractor import extract_profile, is_low_confidence
from packages.agents.parsing.pdf_parser import parse_pdf
from packages.audit.logger import EventType, log_event
from packages.bus.publisher import publish
from packages.bus.topics import Topics
from packages.db.models import Candidate
from packages.db.session import get_db
from packages.storage import client as storage


def run(candidate_id: str, job_id: str, tenant_id: str, s3_key: str) -> dict:
    """Parse one candidate's CV.  Updates Candidate record; publishes CV_PARSED."""

    candidate_uuid = uuid.UUID(candidate_id)
    tenant_uuid = uuid.UUID(tenant_id)

    # ── Load candidate context ────────────────────────────────────────────────
    with get_db() as db:
        candidate = db.get(Candidate, candidate_uuid)
        if candidate is None:
            raise ValueError(f"Candidate {candidate_id} not found")
        if candidate.status == "parsed":
            return {"status": "already_parsed", "candidate_id": candidate_id}

        candidate_name = candidate.name
        candidate_email = candidate.email
        filename = candidate.cv_original_filename or ""

    # ── Download CV ───────────────────────────────────────────────────────────
    log_event(
        EventType.CV_PARSING_STARTED,
        tenant_id=tenant_uuid,
        entity_type="candidate",
        entity_id=candidate_uuid,
        data={"s3_key": s3_key},
    )

    cv_data = storage.download(s3_key)

    # ── Extract text ──────────────────────────────────────────────────────────
    if filename.lower().endswith(".pdf") or s3_key.endswith(".pdf"):
        raw_text = parse_pdf(cv_data)
    elif filename.lower().endswith(".docx") or s3_key.endswith(".docx"):
        raw_text = parse_docx(cv_data)
    elif filename.lower().endswith(".doc") or s3_key.endswith(".doc"):
        raw_text = parse_doc(cv_data)
    else:
        # Try PDF first
        raw_text = parse_pdf(cv_data) or parse_docx(cv_data)

    if not raw_text:
        with get_db() as db:
            c = db.get(Candidate, candidate_uuid)
            c.status = "parse_failed"
            c.parse_flagged = True
            c.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
        return {"status": "parse_failed", "reason": "empty_text"}

    # ── LLM structured extraction (RP-002, RP-005) ────────────────────────────
    profile = extract_profile(raw_text, candidate_name=candidate_name, candidate_email=candidate_email)
    flagged = is_low_confidence(profile)

    # ── Persist structured profile ────────────────────────────────────────────
    with get_db() as db:
        c = db.get(Candidate, candidate_uuid)
        c.experience = profile["experience"]
        c.education = profile["education"]
        c.skills_hard = profile["skills"].get("hard", [])
        c.skills_soft = profile["skills"].get("soft", [])
        c.certifications = profile["certifications"]
        c.languages = profile["languages"]
        c.parse_confidence = profile["confidence"]
        c.parse_flagged = flagged
        c.pii_anonymised = True
        c.status = "parsed"
        c.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)

    log_event(
        EventType.CV_PARSING_COMPLETE,
        tenant_id=tenant_uuid,
        entity_type="candidate",
        entity_id=candidate_uuid,
        data={"confidence": profile["confidence"], "flagged": flagged},
    )

    if flagged:
        log_event(
            EventType.CV_PARSE_FLAGGED,
            tenant_id=tenant_uuid,
            entity_type="candidate",
            entity_id=candidate_uuid,
            data={"confidence": profile["confidence"]},
        )

    publish(
        Topics.CV_PARSED,
        {"candidate_id": candidate_id, "job_id": job_id},
        tenant_id=tenant_id,
    )

    return {
        "status": "parsed",
        "candidate_id": candidate_id,
        "confidence": profile["confidence"],
        "flagged": flagged,
    }
