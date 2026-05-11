"""
Scoring rubric generation — JD-004.

Default weights from PRD §7.5.  Recruiter can adjust within bounds
before distribution (enforced at the API layer).
"""

_DEFAULT_RUBRIC = {
    "must_have": 0.40,
    "experience": 0.25,
    "skills": 0.20,
    "nice_to_have": 0.10,
    "trajectory": 0.05,
}

_MIN_WEIGHT = 0.0
_MAX_WEIGHT = 0.80


def default_rubric() -> dict:
    return dict(_DEFAULT_RUBRIC)


def validate_rubric(rubric: dict) -> list[str]:
    """Return a list of validation errors.  Empty list means rubric is valid."""
    errors: list[str] = []
    required_keys = set(_DEFAULT_RUBRIC.keys())

    missing = required_keys - set(rubric.keys())
    if missing:
        errors.append(f"Missing rubric dimensions: {missing}")
        return errors

    for dim, weight in rubric.items():
        if not isinstance(weight, (int, float)):
            errors.append(f"Weight for '{dim}' must be a number, got {type(weight).__name__}")
        elif weight < _MIN_WEIGHT or weight > _MAX_WEIGHT:
            errors.append(f"Weight for '{dim}' out of bounds: {weight} (must be {_MIN_WEIGHT}–{_MAX_WEIGHT})")

    total = sum(rubric[k] for k in required_keys if isinstance(rubric.get(k), (int, float)))
    if abs(total - 1.0) > 0.01:
        errors.append(f"Rubric weights must sum to 1.0, got {total:.3f}")

    return errors


def apply_rubric(rubric: dict, dimension_scores: dict) -> float:
    """Compute composite score from dimension scores and rubric weights.

    All dimension scores are expected to be in the range 0–100.
    Returns composite score in 0–100.
    """
    return sum(rubric.get(dim, 0) * score for dim, score in dimension_scores.items())
