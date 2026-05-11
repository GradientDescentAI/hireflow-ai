"""
LinkedIn post builder — LI-002.

Generates the 8-section post body via LLM, then hard-validates PE-001
(disclosure within first 200 chars) before returning.  If the LLM
violates the structure, the disclosure is prepended as a fallback.
"""

from packages.llm.client import call_llm
from packages.llm.prompt_registry import get_system_prompt, get_user_prompt
from packages.persona.disclosure import assert_linkedin_post_disclosure, linkedin_post_disclosure


def build_post(
    job: dict,
    company_name: str,
    role_id: str,
    persona: str = "riya",
) -> str:
    """Generate a LinkedIn post for the given job dict.

    Args:
        job: dict with title, location, responsibilities, must_haves, tech_stack,
             salary_min, salary_max fields.
        company_name: recruiter's company name (from Tenant.name).
        role_id: short job identifier used in the apply email address.
        persona: persona name (default 'riya').

    Returns:
        Post body string (≤3000 chars) with disclosure in first 200 chars.
    """
    location = job.get("location", {})
    location_type = location.get("type", "onsite").capitalize()
    city = location.get("city") or "India"

    salary_min = job.get("salary_min")
    salary_max = job.get("salary_max")
    if salary_min and salary_max:
        salary_range = f"₹{salary_min // 100_000}–{salary_max // 100_000} LPA"
    elif salary_min:
        salary_range = f"₹{salary_min // 100_000}+ LPA"
    else:
        salary_range = "Not disclosed"

    responsibilities = job.get("responsibilities", [])[:3]
    must_haves = [mh.get("criterion", str(mh)) for mh in job.get("must_haves", [])[:3]]
    tech_stack = ", ".join(job.get("tech_stack", [])[:5]) or "Not specified"

    system = get_system_prompt("post_draft")
    user = get_user_prompt(
        "post_draft",
        {
            "company_name": company_name,
            "role_id": role_id,
            "title": job.get("title", ""),
            "location_type": location_type,
            "city": city,
            "salary_range": salary_range,
            "responsibilities": "\n".join(f"- {r}" for r in responsibilities),
            "must_haves": "\n".join(f"- {m}" for m in must_haves),
            "tech_stack": tech_stack,
        },
    )

    resp = call_llm(
        "post_draft_linkedin",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )

    post_body = resp.content.strip()

    # ── PE-001 hard enforcement ───────────────────────────────────────────────
    try:
        assert_linkedin_post_disclosure(post_body, company_name, persona)
    except ValueError:
        # LLM missed disclosure — prepend it (still within 200 chars)
        disclosure = linkedin_post_disclosure(company_name, persona)
        post_body = f"{disclosure}\n\n{post_body}"

    # Truncate to LinkedIn's 3,000-char limit
    if len(post_body) > 3000:
        post_body = post_body[:2997] + "..."

    return post_body
