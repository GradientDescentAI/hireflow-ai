"""
Scoring Agent — SC-001 to SC-008.

Scores all parsed candidates for a job.
Runs as a batch: triggered by POST /jobs/{id}/score or on a bus event.

Flow:
  1. Load all candidates with status='parsed' for the job
  2. For each candidate: build anonymised profile, call scorer
  3. Save CandidateScore record
  4. Assign ranks by composite_score DESC
  5. Run bias audit across full pool
  6. Publish SCORING_COMPLETE
"""

import uuid
from datetime import datetime, timezone

from packages.agents.scoring.bias_audit import run_bias_audit
from packages.agents.scoring.scorer import score_candidate
from packages.audit.logger import EventType, log_event
from packages.bus.publisher import publish
from packages.bus.topics import Topics
from packages.db.models import Candidate, CandidateScore, Job
from packages.db.session import get_db
from packages.llm.router import STAGE_ROUTES   # model version string for pinning


def run(job_id: str, tenant_id: str, plan: str = "free") -> dict:
    """Score all parsed candidates for a job."""

    job_uuid = uuid.UUID(job_id)
    tenant_uuid = uuid.UUID(tenant_id)

    # ── Load job ──────────────────────────────────────────────────────────────
    with get_db() as db:
        job = db.get(Job, job_uuid)
        if job is None:
            raise ValueError(f"Job {job_id} not found")
        job_dict = {
            "title": job.title,
            "must_haves": job.must_haves,
            "nice_to_haves": job.nice_to_haves,
            "responsibilities": job.responsibilities,
            "tech_stack": job.tech_stack,
            "scoring_rubric": job.scoring_rubric,
        }

        # Extract all needed candidate data while inside the session (avoid detached-instance errors)
        candidate_rows = [
            {
                "id": c.id,
                "name": c.name,
                "experience": c.experience,
                "education": c.education,
                "skills_hard": c.skills_hard,
                "skills_soft": c.skills_soft,
                "certifications": c.certifications,
                "languages": c.languages,
            }
            for c in db.query(Candidate)
            .filter_by(job_id=job_uuid, status="parsed", is_duplicate=False, opted_out=False)
            .all()
        ]

    if not candidate_rows:
        return {"job_id": job_id, "scored": 0, "status": "no_candidates"}

    log_event(
        EventType.SCORING_STARTED,
        tenant_id=tenant_uuid,
        entity_type="job",
        entity_id=job_uuid,
        data={"candidate_count": len(candidate_rows)},
    )

    model_version = STAGE_ROUTES["candidate_scoring"].model

    scores: list[tuple[uuid.UUID, float, dict]] = []   # (candidate_id, composite, score_dict)

    for c in candidate_rows:
        candidate_profile = {
            "experience": c["experience"],
            "education": c["education"],
            "skills_hard": c["skills_hard"],
            "skills_soft": c["skills_soft"],
            "certifications": c["certifications"],
            "languages": c["languages"],
        }

        try:
            result = score_candidate(job_dict, candidate_profile, plan=plan)
        except Exception as exc:
            import structlog as _sl
            _sl.get_logger().error("scoring_candidate_error", candidate_id=str(c["id"]), error=str(exc))
            log_event(
                EventType.AGENT_ERROR,
                tenant_id=tenant_uuid,
                entity_type="candidate",
                entity_id=c["id"],
                data={"error": str(exc), "stage": "scoring"},
            )
            continue

        scores.append((c["id"], result["composite_score"], result))

    # ── Assign ranks (highest score = rank 1) ─────────────────────────────────
    scores.sort(key=lambda x: x[1], reverse=True)

    now = datetime.now(timezone.utc).replace(tzinfo=None)

    with get_db() as db:
        # Delete any existing scores for this job (idempotent re-score)
        db.query(CandidateScore).filter_by(job_id=job_uuid).delete()

        for rank, (cid, composite, result) in enumerate(scores, start=1):
            score_record = CandidateScore(
                id=uuid.uuid4(),
                candidate_id=cid,
                job_id=job_uuid,
                tenant_id=tenant_uuid,
                composite_score=result["composite_score"],
                rank=rank,
                dimension_scores=result["dimension_scores"],
                criteria_met=result["criteria_met"],
                justification=result["justification"],
                strengths=result["strengths"],
                risks=result["risks"],
                near_miss_flag=result["near_miss_flag"],
                scored_at=now,
                model_version=model_version,
            )
            db.add(score_record)

        job = db.get(Job, job_uuid)
        if job:
            job.status = "scoring"

    # ── Bias audit (SC-008) ───────────────────────────────────────────────────
    all_names = [c["name"] for c in candidate_rows]
    shortlist_size = 10

    with get_db() as db:
        shortlisted_names = [
            c.name
            for c in db.query(Candidate)
            .join(CandidateScore, Candidate.id == CandidateScore.candidate_id)
            .filter(CandidateScore.job_id == job_uuid, CandidateScore.rank <= shortlist_size)
            .all()
        ]

    audit_result = run_bias_audit(all_names, shortlisted_names)

    # Update bias_audit_passed on shortlisted scores
    with get_db() as db:
        for score in db.query(CandidateScore).filter_by(job_id=job_uuid).filter(CandidateScore.rank <= shortlist_size).all():
            score.bias_audit_passed = audit_result["passed"]

    log_event(
        EventType.BIAS_AUDIT_RUN,
        tenant_id=tenant_uuid,
        entity_type="job",
        entity_id=job_uuid,
        data=audit_result,
    )

    if not audit_result["passed"]:
        log_event(
            EventType.BIAS_AUDIT_FLAGGED,
            tenant_id=tenant_uuid,
            entity_type="job",
            entity_id=job_uuid,
            data=audit_result,
        )

    log_event(
        EventType.SCORING_COMPLETE,
        tenant_id=tenant_uuid,
        entity_type="job",
        entity_id=job_uuid,
        data={"scored": len(scores), "bias_audit_passed": audit_result["passed"]},
    )

    publish(
        Topics.SCORING_COMPLETE,
        {"job_id": job_id, "scored_count": len(scores)},
        tenant_id=tenant_id,
    )

    return {
        "job_id": job_id,
        "scored": len(scores),
        "bias_audit_passed": audit_result["passed"],
        "status": "scoring_complete",
    }
