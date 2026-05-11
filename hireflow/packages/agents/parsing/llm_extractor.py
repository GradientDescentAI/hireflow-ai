"""
CV → CandidateProfile JSON via LLM.

PII is stripped before this call via pii_guard.  The LLM never sees
the candidate's name, email, or phone number.  The structured result
is stored in DB; the raw PII remains only in the encrypted Candidate record.
"""

import json

from packages.llm.client import call_llm
from packages.llm.pii_guard import strip_pii
from packages.llm.prompt_registry import get_system_prompt, get_user_prompt

_LOW_CONFIDENCE_THRESHOLD = 0.6


def extract_profile(
    cv_text: str,
    candidate_name: str | None = None,
    candidate_email: str | None = None,
) -> dict:
    """Extract structured profile from CV text.

    Returns dict with keys: experience, education, skills, certifications,
    languages, confidence.

    Raises ValueError on unparseable LLM response.
    """
    # ── Strip PII before sending to LLM (RP-005) ─────────────────────────────
    guard_result = strip_pii(cv_text, name=candidate_name)
    if candidate_email:
        guard_result = strip_pii(guard_result.text, name=candidate_email)
    clean_text = guard_result.text

    system = get_system_prompt("cv_extraction")
    user = get_user_prompt("cv_extraction", {"cv_text": clean_text})

    resp = call_llm(
        "cv_extraction",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        response_format={"type": "json_object"},
    )

    try:
        profile = json.loads(resp.content)
    except json.JSONDecodeError as exc:
        raise ValueError(f"LLM returned invalid JSON during CV extraction: {exc}") from exc

    return _normalise(profile)


def _normalise(raw: dict) -> dict:
    return {
        "experience": raw.get("experience") or [],
        "education": raw.get("education") or [],
        "skills": raw.get("skills") or {"hard": [], "soft": []},
        "certifications": raw.get("certifications") or [],
        "languages": raw.get("languages") or [],
        "confidence": float(raw.get("confidence", 0.5)),
    }


def is_low_confidence(profile: dict) -> bool:
    return profile.get("confidence", 0) < _LOW_CONFIDENCE_THRESHOLD
