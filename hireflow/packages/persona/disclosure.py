"""
Disclosure enforcement — PE-001 to PE-007.

Every channel has a required disclosure string. These functions return the
exact text that agents must include. They are called by channel agents —
never skipped, never made optional by configuration.

PE-006: Disabling disclosure is not configurable.
"""

from packages.persona.identity import PersonaConfig, get_persona


def linkedin_post_disclosure(company_name: str, persona: PersonaConfig | str = "riya") -> str:
    """PE-001: Must appear within first 200 characters of every LinkedIn post."""
    p = persona if isinstance(persona, PersonaConfig) else get_persona(persona)
    return f"Posted by {p.name}, an AI hiring assistant for {company_name}."


def linkedin_post_signoff(company_name: str, persona: PersonaConfig | str = "riya") -> str:
    """PE-001: Sign-off at end of LinkedIn post."""
    p = persona if isinstance(persona, PersonaConfig) else get_persona(persona)
    return f"- {p.name}, AI assistant for {company_name}"


def email_footer(company_name: str, persona: PersonaConfig | str = "riya") -> str:
    """PE-003: Footer on every outbound email (ack, outreach, follow-up)."""
    p = persona if isinstance(persona, PersonaConfig) else get_persona(persona)
    return (
        f"──────────────────────────────────────────────\n"
        f"This email was sent by {p.name}, an AI assistant. "
        f"Replies are read by a human recruiter at {company_name}."
    )


def whatsapp_disclosure(company_name: str, persona: PersonaConfig | str = "riya") -> str:
    """PE-004: Same disclosure as LinkedIn but for WhatsApp/Telegram posts."""
    p = persona if isinstance(persona, PersonaConfig) else get_persona(persona)
    return f"Posted by {p.name}, an AI hiring assistant for {company_name}."


def ai_human_question_response(company_name: str, persona: PersonaConfig | str = "riya") -> str:
    """PE-005: Response when candidate asks 'Are you human or AI?'
    Must be truthful and immediate, without deflection.
    """
    p = persona if isinstance(persona, PersonaConfig) else get_persona(persona)
    return (
        f"I'm {p.name}, an AI assistant. Your application will be reviewed by a human recruiter "
        f"from {company_name}. They will reach out if you're shortlisted."
    )


def validate_linkedin_post_disclosure(post_body: str, company_name: str, persona: PersonaConfig | str = "riya") -> bool:
    """Assert PE-001: disclosure appears within the first 200 characters."""
    p = persona if isinstance(persona, PersonaConfig) else get_persona(persona)
    expected_fragment = f"Posted by {p.name}"
    return expected_fragment.lower() in post_body[:200].lower()


def assert_linkedin_post_disclosure(post_body: str, company_name: str, persona: PersonaConfig | str = "riya") -> None:
    """Raise if PE-001 is violated. Called before any LinkedIn post is submitted."""
    if not validate_linkedin_post_disclosure(post_body, company_name, persona):
        p = persona if isinstance(persona, PersonaConfig) else get_persona(persona)
        raise ValueError(
            f"PE-001 violation: LinkedIn post must contain disclosure within first 200 chars. "
            f"Expected 'Posted by {p.name}' near the start of the post body."
        )
