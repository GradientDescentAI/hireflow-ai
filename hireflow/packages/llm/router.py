"""
Stage → (provider, model, default params) routing.

All stages currently route to Gemini:
  - gemini-2.0-flash  : high-volume / cheap stages (parsing, post drafts)
  - gemini-2.5-pro    : reasoning-heavy stages (scoring, bias audit, justifications)

Temperature = 0 on all scoring calls (SC-001 reproducibility requirement).
"""

from dataclasses import dataclass
from typing import Literal

Provider = Literal["openai", "anthropic", "gemini"]


@dataclass(frozen=True)
class RouteConfig:
    provider: Provider
    model: str
    temperature: float
    max_tokens: int


# Gemini model IDs
_FLASH = "gemini-2.5-flash"   # fast, cheap stages
_PRO   = "gemini-2.5-pro"     # reasoning-heavy stages (scoring, audit, justification)

STAGE_ROUTES: dict[str, RouteConfig] = {
    # JD processing
    "jd_extraction":  RouteConfig("gemini", _FLASH, temperature=0.0, max_tokens=2048),
    "jd_bias_check":  RouteConfig("gemini", _FLASH, temperature=0.0, max_tokens=512),

    # Distribution copy — slight creativity OK
    "post_draft_linkedin":   RouteConfig("gemini", _FLASH, temperature=0.6, max_tokens=1024),
    "post_draft_whatsapp":   RouteConfig("gemini", _FLASH, temperature=0.6, max_tokens=512),
    "post_draft_telegram":   RouteConfig("gemini", _FLASH, temperature=0.6, max_tokens=1024),
    "college_email_draft":   RouteConfig("gemini", _FLASH, temperature=0.5, max_tokens=512),

    # CV parsing — high volume, must be cheap
    "cv_extraction":  RouteConfig("gemini", _FLASH, temperature=0.0, max_tokens=3000),

    # Scoring — temperature MUST be 0 (SC-001)
    # gemini-2.5-pro reserves thinking tokens from max_tokens budget; use flash for predictable output
    "candidate_scoring": RouteConfig("gemini", _FLASH, temperature=0.0, max_tokens=4096),
    "bias_audit":        RouteConfig("gemini", _FLASH, temperature=0.0, max_tokens=2048),

    # Shortlist justifications — quality matters
    "shortlist_justification_standard": RouteConfig("gemini", _FLASH, temperature=0.3, max_tokens=2048),
    "shortlist_justification_pro":      RouteConfig("gemini", _PRO,   temperature=0.3, max_tokens=8192),
}


def get_route(stage: str, plan: str = "free") -> RouteConfig:
    """Return the RouteConfig for a pipeline stage.

    plan="pro" unlocks the pro justification variant.
    """
    if stage == "shortlist_justification":
        stage = "shortlist_justification_pro" if plan == "pro" else "shortlist_justification_standard"
    config = STAGE_ROUTES.get(stage)
    if config is None:
        raise ValueError(f"Unknown pipeline stage: {stage!r}")
    return config
