"""
Shortlist builder — SL-001, SL-002.

Selects top-N candidates by composite_score rank and generates an LLM-backed
justification document for the hiring manager.  Candidate profiles passed to the
LLM are already PII-stripped (name/email never included).
"""

import json

from packages.llm.client import call_llm
from packages.llm.prompt_registry import get_system_prompt, get_user_prompt

_DEFAULT_SHORTLIST_SIZE = 10


def build_shortlist(
    job: dict,
    scored_candidates: list[dict],
    bias_audit_result: dict,
    plan: str = "free",
    shortlist_size: int = _DEFAULT_SHORTLIST_SIZE,
) -> dict:
    """Select top-N candidates and generate hiring-manager justification.

    Args:
        job: dict with title, must_haves, nice_to_haves, responsibilities, tech_stack.
        scored_candidates: list of dicts, each with rank, composite_score,
            dimension_scores, criteria_met, strengths, risks, near_miss_flag,
            and anonymised profile fields (experience, education, skills_hard, etc.).
            Must be pre-sorted by rank ascending.
        bias_audit_result: result dict from run_bias_audit().
        plan: tenant plan — determines model tier.
        shortlist_size: number of candidates to shortlist (default 10).

    Returns:
        {
            "shortlisted": [<scored_candidate dicts, rank 1..N>],
            "shortlist_size": int,
            "justification_doc": {shortlist_summary, top_candidate_notes,
                                   panel_interview_questions, diversity_note,
                                   recommended_interview_format},
        }
    """
    top_n = [c for c in scored_candidates if c["rank"] <= shortlist_size]
    top_n.sort(key=lambda x: x["rank"])

    justification_doc = _generate_justification(job, top_n, bias_audit_result, plan, shortlist_size)

    return {
        "shortlisted": top_n,
        "shortlist_size": len(top_n),
        "justification_doc": justification_doc,
    }


def _generate_justification(
    job: dict,
    top_candidates: list[dict],
    bias_audit_result: dict,
    plan: str,
    shortlist_size: int,
) -> dict:
    """Call LLM to produce the shortlist justification document."""
    stage = "shortlist_justification_pro" if plan == "pro" else "shortlist_justification_standard"

    jd_summary = {
        "title": job.get("title"),
        "responsibilities": job.get("responsibilities", []),
        "must_haves": [mh.get("criterion", str(mh)) for mh in job.get("must_haves", [])],
        "nice_to_haves": [nh.get("criterion", str(nh)) for nh in job.get("nice_to_haves", [])],
        "tech_stack": job.get("tech_stack", []),
    }

    # Anonymised candidate summaries — no name/email
    candidate_summaries = [
        {
            "rank": c["rank"],
            "composite_score": c["composite_score"],
            "dimension_scores": c.get("dimension_scores", {}),
            "strengths": c.get("strengths", []),
            "risks": c.get("risks", []),
            "near_miss_flag": c.get("near_miss_flag", False),
            "criteria_met": c.get("criteria_met", []),
        }
        for c in top_candidates
    ]

    bias_status = (
        "PASSED — no significant demographic disparity detected."
        if bias_audit_result.get("passed")
        else f"FLAGGED — max disparity {bias_audit_result.get('max_disparity', 0):.0%}. "
             "Hiring manager should review with additional care."
    )

    system = get_system_prompt("shortlist_justification")
    user = get_user_prompt(
        "shortlist_justification",
        {
            "jd_json": json.dumps(jd_summary, ensure_ascii=False),
            "bias_audit_status": bias_status,
            "shortlist_size": shortlist_size,
            "candidates_json": json.dumps(candidate_summaries, ensure_ascii=False),
        },
    )

    resp = call_llm(
        stage,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        plan=plan,
        response_format={"type": "json_object"},
    )

    try:
        return json.loads(resp.content)
    except json.JSONDecodeError:
        return {
            "shortlist_summary": "Justification generation failed — LLM returned invalid JSON.",
            "top_candidate_notes": [],
            "panel_interview_questions": [],
            "diversity_note": bias_status,
            "recommended_interview_format": "Panel interview recommended.",
        }
