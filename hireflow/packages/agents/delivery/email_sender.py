"""
Delivery email sender — SL-003, PE-003.

Sends the shortlist notification to the recruiter via SendGrid.
Includes the Riya AI disclosure footer on every outbound message (PE-003).
"""

import os
from datetime import datetime, timezone

import sendgrid
from sendgrid.helpers.mail import Mail, To

from packages.persona.disclosure import email_footer

_FROM_EMAIL = os.environ.get("SENDGRID_FROM_EMAIL", "riya@hireflow.in")
_FROM_NAME = "Riya — HireFlow AI"


def send_shortlist_notification(
    recruiter_email: str,
    recruiter_name: str,
    job_title: str,
    job_id: str,
    shortlist_size: int,
    bias_audit_passed: bool,
    app_base_url: str = "https://app.hireflow.in",
) -> bool:
    """Send shortlist-ready email to the recruiter.

    Returns True on success, False on SendGrid error (logged by caller).
    """
    api_key = os.environ.get("SENDGRID_API_KEY")
    if not api_key:
        import structlog as _sl
        _sl.get_logger().warning(
            "sendgrid_not_configured",
            recruiter=recruiter_email,
            job=job_id,
            note="Skipping email delivery; shortlist available in UI",
        )
        return False

    sg = sendgrid.SendGridAPIClient(api_key=api_key)

    bias_note = (
        "Our AI bias audit passed for this shortlist."
        if bias_audit_passed
        else "Note: Our AI bias audit flagged a potential demographic disparity in this shortlist. "
             "We recommend reviewing candidates with additional care."
    )

    shortlist_url = f"{app_base_url}/jobs/{job_id}/shortlist"

    body = _build_html(
        recruiter_name=recruiter_name,
        job_title=job_title,
        shortlist_size=shortlist_size,
        bias_note=bias_note,
        shortlist_url=shortlist_url,
    )

    message = Mail(
        from_email=(_FROM_EMAIL, _FROM_NAME),
        to_emails=To(recruiter_email),
        subject=f"Your shortlist is ready: {job_title} ({shortlist_size} candidates)",
        html_content=body,
    )

    try:
        response = sg.send(message)
        return response.status_code in (200, 202)
    except Exception:
        return False


def send_candidate_rejection_notice(
    candidate_email: str,
    job_title: str,
    company_name: str,
) -> bool:
    """Send a respectful rejection notice to a candidate (optional, recruiter-triggered)."""
    sg = sendgrid.SendGridAPIClient(api_key=os.environ["SENDGRID_API_KEY"])

    body = _build_rejection_html(
        job_title=job_title,
        company_name=company_name,
    )

    message = Mail(
        from_email=(_FROM_EMAIL, _FROM_NAME),
        to_emails=To(candidate_email),
        subject=f"Update on your application — {job_title} at {company_name}",
        html_content=body,
    )

    try:
        response = sg.send(message)
        return response.status_code in (200, 202)
    except Exception:
        return False


def _build_html(
    recruiter_name: str,
    job_title: str,
    shortlist_size: int,
    bias_note: str,
    shortlist_url: str,
) -> str:
    footer = email_footer().replace("\n", "<br>")
    now_str = datetime.now(timezone.utc).strftime("%d %b %Y, %H:%M UTC")

    return f"""
<html><body style="font-family: Arial, sans-serif; color: #222; max-width: 600px; margin: auto;">
<h2 style="color: #1a56db;">Your shortlist is ready</h2>
<p>Hi {recruiter_name},</p>
<p>
  Riya has finished evaluating all applications for <strong>{job_title}</strong>.
  <strong>{shortlist_size} candidate{'' if shortlist_size == 1 else 's'}</strong>
  have been shortlisted based on your job requirements.
</p>
<p>{bias_note}</p>
<p>
  <a href="{shortlist_url}"
     style="display:inline-block;background:#1a56db;color:#fff;padding:12px 24px;
            border-radius:4px;text-decoration:none;font-weight:bold;">
    View Shortlist
  </a>
</p>
<p>You can approve, hold, or reject candidates and add notes directly in the platform.
   All decisions are logged for compliance.</p>
<hr style="border:none;border-top:1px solid #eee;margin:24px 0;">
<p style="font-size:12px;color:#666;">
  Generated: {now_str}<br><br>
  {footer}
</p>
</body></html>
"""


def _build_rejection_html(job_title: str, company_name: str) -> str:
    footer = email_footer().replace("\n", "<br>")

    return f"""
<html><body style="font-family: Arial, sans-serif; color: #222; max-width: 600px; margin: auto;">
<h2>Thank you for your application</h2>
<p>
  Thank you for applying for the <strong>{job_title}</strong> position at
  <strong>{company_name}</strong>.
</p>
<p>
  After careful consideration, we have decided to move forward with other candidates
  whose experience more closely matches our current requirements.
  We appreciate the time you invested and encourage you to apply for future openings.
</p>
<p>We wish you all the best in your job search.</p>
<hr style="border:none;border-top:1px solid #eee;margin:24px 0;">
<p style="font-size:12px;color:#666;">{footer}</p>
</body></html>
"""
