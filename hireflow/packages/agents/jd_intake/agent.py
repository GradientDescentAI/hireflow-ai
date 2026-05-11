"""
JD Intake Agent — orchestrates the full JD intake flow.

Flow:
  1. Load raw text from source (text / pdf / docx / url)
  2. Extract structured JD via LLM
  3. Check Karnataka salary mandate (JD-007)
  4. Generate default scoring rubric
  5. Update Job record in DB (status → extraction_complete)
  6. Audit log extraction event

The agent is idempotent: re-running for a job that already has
status=extraction_complete is a no-op (returns cached result).
"""

import uuid
from datetime import datetime, timezone

from packages.agents.jd_intake.extractor import extract_jd, requires_salary_disclosure
from packages.agents.jd_intake.file_loader import load_text
from packages.agents.jd_intake.rubric import default_rubric
from packages.audit.logger import EventType, log_event
from packages.db.models import Job
from packages.db.session import get_db


def run(
    job_id: str,
    tenant_id: str,
    raw_jd_text: str | None = None,
    raw_jd_url: str | None = None,
) -> dict:
    """Run JD intake for a job.  Updates the Job row; returns a summary dict."""

    job_uuid = uuid.UUID(job_id)
    tenant_uuid = uuid.UUID(tenant_id)

    # ── Determine raw text ────────────────────────────────────────────────────
    if raw_jd_text:
        text = load_text(raw_jd_text, "text")
    elif raw_jd_url:
        text = load_text(raw_jd_url, "url")
    else:
        with get_db() as db:
            job = db.get(Job, job_uuid)
            if job is None:
                raise ValueError(f"Job {job_id} not found")
            if job.status == "extraction_complete":
                # Idempotent: already done
                return {"job_id": job_id, "status": "extraction_complete", "title": job.title, "cached": True}
            if not job.raw_jd_text:
                raise ValueError(f"Job {job_id} has no raw JD text and no URL was provided")
            text = job.raw_jd_text

    # ── Extract structured JD ─────────────────────────────────────────────────
    extracted = extract_jd(text)

    # ── Karnataka salary check (JD-007) ──────────────────────────────────────
    location = extracted["location"]
    salary = extracted["salary_range"]
    karnataka_warning = requires_salary_disclosure(location) and not salary.get("min")

    # ── Scoring rubric (JD-004) ───────────────────────────────────────────────
    rubric = default_rubric()

    # ── Persist to DB ─────────────────────────────────────────────────────────
    with get_db() as db:
        job = db.get(Job, job_uuid)
        if job is None:
            raise ValueError(f"Job {job_id} not found")

        job.title = extracted["title"]
        job.department = extracted.get("department")
        job.location = location
        job.seniority = extracted.get("seniority")
        job.industry = extracted.get("industry")
        job.responsibilities = extracted["responsibilities"]
        job.must_haves = extracted["must_haves"]
        job.nice_to_haves = extracted["nice_to_haves"]
        job.tech_stack = extracted["tech_stack"]
        job.salary_min = salary.get("min")
        job.salary_max = salary.get("max")
        job.bias_flags = extracted["bias_flags"]
        job.scoring_rubric = rubric
        job.raw_jd_text = text
        job.status = "extraction_complete"
        job.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)

    # ── Audit ─────────────────────────────────────────────────────────────────
    log_event(
        EventType.JD_EXTRACTION_COMPLETE,
        tenant_id=tenant_uuid,
        entity_type="job",
        entity_id=job_uuid,
        data={
            "title": extracted["title"],
            "must_have_count": len(extracted["must_haves"]),
            "nice_to_have_count": len(extracted["nice_to_haves"]),
            "bias_flags_count": len(extracted["bias_flags"]),
            "karnataka_salary_warning": karnataka_warning,
        },
    )

    return {
        "job_id": job_id,
        "status": "extraction_complete",
        "title": extracted["title"],
        "bias_flags": extracted["bias_flags"],
        "karnataka_salary_warning": karnataka_warning,
        "cached": False,
    }
