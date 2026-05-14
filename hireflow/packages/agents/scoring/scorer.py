"""
5-dimension LLM candidate scorer — SC-001 to SC-003.

Temperature is locked to 0.  Model version is pinned per tenant.
Same input always yields the same output (SC-001).
Every score includes per-criterion explanations (SC-002).
Anonymised profile is used when tenant has enabled anonymous mode (SC-003).
"""

import json

from packages.agents.jd_intake.rubric import apply_rubric
from packages.llm.client import call_llm
from packages.llm.pii_guard import strip_pii
from packages.llm.prompt_registry import get_system_prompt, get_user_prompt


def score_candidate(job: dict, candidate: dict, plan: str = "free") -> dict:
    """Score a candidate against a job.

    Args:
        job: dict with title, must_haves, nice_to_haves, responsibilities,
             tech_stack, scoring_rubric fields.
        candidate: dict with experience, education, skills_hard, skills_soft,
                   certifications, languages fields.  PII must already be absent.
        plan: tenant plan — used to select model tier.

    Returns:
        dict matching CandidateScore schema (without DB ids).
    """
    # Double-check: strip any stray PII just in case
    candidate_text = json.dumps(candidate, ensure_ascii=False)
    candidate_text = strip_pii(candidate_text).text

    jd_summary = {
        "title": job.get("title"),
        "responsibilities": job.get("responsibilities", []),
        "must_haves": [mh.get("criterion", str(mh)) for mh in job.get("must_haves", [])],
        "nice_to_haves": [nh.get("criterion", str(nh)) for nh in job.get("nice_to_haves", [])],
        "tech_stack": job.get("tech_stack", []),
    }

    system = get_system_prompt("candidate_scoring")
    user = get_user_prompt(
        "candidate_scoring",
        {
            "jd_json": json.dumps(jd_summary, ensure_ascii=False),
            "candidate_json": candidate_text,
        },
    )

    resp = call_llm(
        "candidate_scoring",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        response_format={"type": "json_object"},
    )

    # Log the raw response if it looks empty/short for debugging
    if not resp.content or len(resp.content) < 50:
        import structlog as _sl
        _sl.get_logger().warning(
            "scoring_llm_short_response",
            content_len=len(resp.content or ""),
            content_preview=(resp.content or "")[:200],
            model=resp.model,
            input_tokens=resp.input_tokens,
            output_tokens=resp.output_tokens,
        )

    # Strip markdown fences if present (Gemini sometimes wraps JSON in ```json ... ```)
    content = resp.content.strip()
    if content.startswith("```"):
        content = content.split("\n", 1)[1] if "\n" in content else content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()

    try:
        raw = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"LLM returned invalid JSON during scoring: {exc} (len={len(resp.content or '')}, preview={resp.content[:120]!r})"
        ) from exc

    return _normalise(raw, job.get("scoring_rubric", {}))


def _normalise(raw: dict, rubric: dict) -> dict:
    dims = raw.get("dimension_scores", {})
    composite = raw.get("composite_score")

    # Recalculate composite from rubric + dimension scores for consistency
    if rubric and dims:
        computed = apply_rubric(rubric, {
            "must_have": dims.get("must_have", 0),
            "experience": dims.get("experience", 0),
            "skills": dims.get("skills", 0),
            "nice_to_have": dims.get("nice_to_have", 0),
            "trajectory": dims.get("trajectory", 0),
        })
        composite = round(computed, 2)

    near_miss = composite is not None and composite >= 70 and any(
        not c.get("met", True) for c in raw.get("criteria_met", [])
    )

    return {
        "composite_score": composite or 0.0,
        "dimension_scores": dims,
        "criteria_met": raw.get("criteria_met", []),
        "justification": raw.get("justification", ""),
        "strengths": raw.get("strengths", []),
        "risks": raw.get("risks", []),
        "near_miss_flag": raw.get("near_miss_flag", near_miss),
    }
