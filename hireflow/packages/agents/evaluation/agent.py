"""
Evaluation Agent — SL-001 to SL-004.

Reads scored candidates for a job, selects the top-N shortlist,
generates a hiring-manager justification document, persists it on the Job,
and publishes SHORTLIST_READY.

Flow:
  1. Load all CandidateScore records for the job (ranked)
  2. Load corresponding Candidate profiles (anonymised)
  3. Load bias audit status from scores
  4. Call shortlist_builder to select top-N and generate justification
  5. Persist justification_doc on Job.shortlist_justification
  6. Update Job.status = 'shortlisted'
  7. Publish SHORTLIST_READY
"""

import uuid
from datetime import datetime, timezone

from packages.agents.evaluation.shortlist_builder import build_shortlist
from packages.audit.logger import EventType, log_event
from packages.bus.publisher import publish
from packages.bus.topics import Topics
from packages.db.models import Candidate, CandidateScore, Job
from packages.db.session import get_db


def run(job_id: str, tenant_id: str, plan: str = "free", shortlist_size: int = 10) -> dict:
    """Evaluate scored candidates and produce a shortlist for the hiring manager."""

    job_uuid = uuid.UUID(job_id)
    tenant_uuid = uuid.UUID(tenant_id)

    # ── Load job ──────────────────────────────────────────────────────────────
    with get_db() as db:
        job = db.get(Job, job_uuid)
        if job is None:
            raise ValueError(f"Job {job_id} not found")

        job_dict = {
            "title": job.title,
            "must_haves": job.must_haves or [],
            "nice_to_haves": job.nice_to_haves or [],
            "responsibilities": job.responsibilities or [],
            "tech_stack": job.tech_stack or [],
        }

        # Load all scored records for this job, ranked
        score_records = (
            db.query(CandidateScore)
            .filter_by(job_id=job_uuid)
            .order_by(CandidateScore.rank)
            .all()
        )

        if not score_records:
            return {"job_id": job_id, "status": "no_scores", "shortlisted": 0}

        # Build candidate_id → score mapping for quick lookup
        score_by_cid = {str(s.candidate_id): s for s in score_records}
        candidate_ids = list(score_by_cid.keys())

        # Load candidate profiles
        candidates = (
            db.query(Candidate)
            .filter(Candidate.id.in_([uuid.UUID(cid) for cid in candidate_ids]))
            .all()
        )
        candidate_by_id = {str(c.id): c for c in candidates}

        # Extract bias audit status from shortlisted scores
        shortlisted_scores = [s for s in score_records if s.rank <= shortlist_size]
        bias_audit_passed = all(
            s.bias_audit_passed for s in shortlisted_scores
            if s.bias_audit_passed is not None
        ) if shortlisted_scores else True

    # ── Build scored_candidates list ──────────────────────────────────────────
    scored_candidates = []
    for score in score_records:
        cid = str(score.candidate_id)
        candidate = candidate_by_id.get(cid)
        scored_candidates.append({
            "rank": score.rank,
            "composite_score": score.composite_score,
            "dimension_scores": score.dimension_scores or {},
            "criteria_met": score.criteria_met or [],
            "justification": score.justification or "",
            "strengths": score.strengths or [],
            "risks": score.risks or [],
            "near_miss_flag": score.near_miss_flag or False,
            # Anonymised profile fields only
            "experience": candidate.experience if candidate else [],
            "education": candidate.education if candidate else [],
            "skills_hard": candidate.skills_hard if candidate else [],
            "skills_soft": candidate.skills_soft if candidate else [],
        })

    bias_audit_result = {"passed": bias_audit_passed}

    log_event(
        EventType.SCORING_COMPLETE,
        tenant_id=tenant_uuid,
        entity_type="job",
        entity_id=job_uuid,
        data={"stage": "evaluation_started", "candidates": len(scored_candidates)},
    )

    # ── Generate shortlist + justification ────────────────────────────────────
    result = build_shortlist(
        job=job_dict,
        scored_candidates=scored_candidates,
        bias_audit_result=bias_audit_result,
        plan=plan,
        shortlist_size=shortlist_size,
    )

    # ── Persist justification on Job ──────────────────────────────────────────
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    with get_db() as db:
        job = db.get(Job, job_uuid)
        if job:
            job.shortlist_justification = result["justification_doc"]
            job.status = "shortlisted"
            job.updated_at = now

    log_event(
        EventType.SHORTLIST_READY,
        tenant_id=tenant_uuid,
        entity_type="job",
        entity_id=job_uuid,
        data={
            "shortlisted": result["shortlist_size"],
            "bias_audit_passed": bias_audit_passed,
        },
    )

    publish(
        Topics.SHORTLIST_READY,
        {
            "job_id": job_id,
            "shortlist_size": result["shortlist_size"],
            "bias_audit_passed": bias_audit_passed,
        },
        tenant_id=tenant_id,
    )

    return {
        "job_id": job_id,
        "status": "shortlisted",
        "shortlisted": result["shortlist_size"],
        "bias_audit_passed": bias_audit_passed,
    }
