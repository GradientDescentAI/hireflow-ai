"""
Acknowledgement emails — AC-007, AC-008, PE-003.

Every valid application gets an ack within 5 minutes.
Missing-attachment emails get a polite resubmission request.
Both emails carry the mandatory AI disclosure footer (PE-003).
"""

import os
from datetime import datetime

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from packages.persona.disclosure import email_footer
from packages.persona.identity import get_persona


_FROM_EMAIL = os.environ.get("SENDGRID_FROM_EMAIL", "riya@hireflow.in")
_FROM_NAME = os.environ.get("SENDGRID_FROM_NAME", "Riya (HireFlow AI)")


def _send(to_email: str, subject: str, body: str) -> None:
    sg = SendGridAPIClient(os.environ["SENDGRID_API_KEY"])
    msg = Mail(
        from_email=(_FROM_EMAIL, _FROM_NAME),
        to_emails=to_email,
        subject=subject,
        plain_text_content=body,
    )
    sg.send(msg)


def send_ack(
    to_email: str,
    candidate_name: str | None,
    job_title: str,
    role_id: str,
    company_name: str,
    persona_name: str = "riya",
) -> None:
    """Send acknowledgement email for a valid application (AC-007)."""
    persona = get_persona(persona_name)
    salutation = f"Hi {candidate_name}," if candidate_name else "Hello,"
    footer = email_footer(company_name, persona)

    body = f"""{salutation}

Thank you for applying for the {job_title} position at {company_name}.

We've received your application (reference: APPLY-{role_id}). Our recruiter will review your profile and reach out if you're shortlisted. This typically takes 7-10 business days.

Please don't reply to this email — applications are processed via our system.

Best regards,
{persona.name}
AI Hiring Assistant, {company_name}

{footer}
"""

    _send(to_email, f"Application received: {job_title} at {company_name}", body)


def send_missing_attachment_request(
    to_email: str,
    candidate_name: str | None,
    job_title: str,
    role_id: str,
    company_name: str,
    persona_name: str = "riya",
) -> None:
    """Send a resubmission request when no CV was attached (AC-008)."""
    persona = get_persona(persona_name)
    salutation = f"Hi {candidate_name}," if candidate_name else "Hello,"
    footer = email_footer(company_name, persona)

    body = f"""{salutation}

Thank you for your interest in the {job_title} position at {company_name}.

We received your email but could not find a CV attachment. To complete your application, please reply to this email with your CV attached (PDF or Word format, max 10MB).

Use the subject line: APPLY-{role_id}
Send to: apply-{role_id}@hireflow.in

Best regards,
{persona.name}
AI Hiring Assistant, {company_name}

{footer}
"""

    _send(to_email, f"Action needed: please attach your CV — {job_title}", body)
