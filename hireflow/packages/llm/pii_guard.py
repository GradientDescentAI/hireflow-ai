"""
PII guard — strips personally identifiable information from candidate text
before it is sent to any external LLM API.

Called at the package boundary in Parsing Agent and Scoring Agent.
Tests assert that no PII pattern survives a guard call.

Stripped signals:
  - Full name (provided explicitly)
  - Email addresses
  - Phone numbers (Indian + international)
  - Photo / image references
  - Age / date-of-birth signals
  - Gender markers (Mr./Mrs./Miss/Ms. salutations)
"""

import re
from dataclasses import dataclass


@dataclass
class GuardResult:
    text: str
    redactions: int


_PATTERNS = [
    # Email
    (re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", re.I), "[EMAIL]"),
    # Indian mobile (10 digits, optional +91 / 0 prefix)
    (re.compile(r"(?:\+91[\s\-]?|0)?[6-9]\d{9}\b"), "[PHONE]"),
    # International phone (E.164-ish)
    (re.compile(r"\+\d{1,3}[\s\-]?\(?\d{1,4}\)?[\s\-]?\d{3,4}[\s\-]?\d{3,4}"), "[PHONE]"),
    # Date of birth / age signals
    (re.compile(r"\b(?:dob|date of birth|d\.o\.b\.?)\s*[:\-]?\s*\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}", re.I), "[DOB]"),
    (re.compile(r"\bage\s*[:\-]?\s*\d{2}\b", re.I), "[AGE]"),
    # Salutation gender markers
    (re.compile(r"\b(?:Mr\.|Mrs\.|Miss\.|Ms\.)\s+[A-Z][a-z]+", re.I), "[NAME]"),
    # Photo / passport photo references
    (re.compile(r"\b(?:passport[\s\-]?photo|photograph|profile[\s\-]?pic(?:ture)?)\b", re.I), "[PHOTO_REF]"),
]


def strip_pii(text: str, name: str | None = None) -> GuardResult:
    """Remove PII from candidate text before sending to an LLM.

    Args:
        text: Raw text extracted from CV or email body.
        name: Candidate's full name (from DB). If provided, occurrences are
              replaced. Always pass this when available.
    """
    redactions = 0
    result = text

    # Replace known name first (before generic patterns)
    if name and name.strip():
        name_pattern = re.compile(re.escape(name.strip()), re.I)
        new_result, n = name_pattern.subn("[NAME]", result)
        result = new_result
        redactions += n

    for pattern, placeholder in _PATTERNS:
        new_result, n = pattern.subn(placeholder, result)
        result = new_result
        redactions += n

    return GuardResult(text=result, redactions=redactions)


def assert_clean(text: str) -> None:
    """Raise if any PII pattern is still detectable. Used in tests."""
    for pattern, _ in _PATTERNS:
        if pattern.search(text):
            raise ValueError(f"PII detected in text after guard: pattern={pattern.pattern!r}")
