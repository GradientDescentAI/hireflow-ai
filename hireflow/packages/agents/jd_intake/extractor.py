"""
JD extraction — raw text → structured JobDescription dict.

Uses the jd_extraction LLM stage (GPT-4o-mini, T=0, JSON output).
Raises ValueError if the LLM response cannot be parsed.
"""

import json

from packages.llm.client import call_llm
from packages.llm.prompt_registry import get_system_prompt, get_user_prompt

# States where salary disclosure is mandatory (JD-007)
MANDATORY_SALARY_STATES = {"karnataka"}


def extract_jd(text: str) -> dict:
    """Extract structured JD fields from raw text.

    Returns a dict with keys matching the JobDescription schema.
    The returned dict is NOT yet saved to the database — the caller does that.
    """
    system = get_system_prompt("jd_extraction")
    user = get_user_prompt("jd_extraction", {"jd_text": text})

    resp = call_llm(
        "jd_extraction",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        response_format={"type": "json_object"},
    )

    try:
        extracted = json.loads(resp.content)
    except json.JSONDecodeError as exc:
        raise ValueError(f"LLM returned invalid JSON during JD extraction: {exc}") from exc

    return _normalise(extracted)


def _normalise(raw: dict) -> dict:
    """Ensure all expected keys are present with correct types."""
    salary = raw.get("salary_range") or {}

    return {
        "title": raw.get("title") or "Untitled Role",
        "department": raw.get("department"),
        "location": raw.get("location") or {"type": "onsite", "city": None, "state": None, "country": "IN"},
        "seniority": raw.get("seniority"),
        "industry": raw.get("industry"),
        "responsibilities": raw.get("responsibilities") or [],
        "must_haves": raw.get("must_haves") or [],
        "nice_to_haves": raw.get("nice_to_haves") or [],
        "tech_stack": raw.get("tech_stack") or [],
        "salary_range": {
            "min": salary.get("min"),
            "max": salary.get("max"),
            "currency": salary.get("currency", "INR"),
        },
        "bias_flags": raw.get("bias_flags") or [],
    }


def requires_salary_disclosure(location: dict) -> bool:
    """Return True if the role's state mandates salary range disclosure (JD-007)."""
    state = (location.get("state") or "").lower().strip()
    return state in MANDATORY_SALARY_STATES
