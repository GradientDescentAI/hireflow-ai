"""
Riya persona identity constants.

Every LLM call and every customer-facing template must pull values from here —
never hardcode the persona name, designation, or tagline in agent code.
This is what makes white-labelling (v2.1 "Anjali" persona) a config change,
not a code change.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class PersonaConfig:
    name: str
    designation: str            # shown to candidates
    pronouns: str
    tagline: str
    region: str
    platform_suffix: str        # "- Riya, AI assistant for {company}"


# Default persona — pan-India
RIYA = PersonaConfig(
    name="Riya",
    designation="AI Junior Recruiter",
    pronouns="she/her",
    tagline="I'm Riya, an AI assistant. I help recruiters at small companies find great candidates faster.",
    region="india",
    platform_suffix="- Riya, AI assistant for {company}",
)

# South India persona (v2.1)
ANJALI = PersonaConfig(
    name="Anjali",
    designation="AI Junior Recruiter",
    pronouns="she/her",
    tagline="I'm Anjali, an AI assistant. I help recruiters at small companies find great candidates faster.",
    region="south_india",
    platform_suffix="- Anjali, AI assistant for {company}",
)

_PERSONAS: dict[str, PersonaConfig] = {
    "riya": RIYA,
    "anjali": ANJALI,
}


def get_persona(name: str) -> PersonaConfig:
    config = _PERSONAS.get(name.lower())
    if config is None:
        raise ValueError(f"Unknown persona: {name!r}. Valid: {list(_PERSONAS)}")
    return config


# Names must be culturally Indian, female, linguistically neutral.
APPROVED_NAMES = {"riya", "anjali", "priya", "meera"}
