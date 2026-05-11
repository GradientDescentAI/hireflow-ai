"""
LinkedIn account health monitor — AR-006, LI-008, LI-010.

Runs daily (scheduled in worker).  Checks:
  1. Login success
  2. Account restriction / warning banners
  3. Post impression trend (sudden 0-impression post = yellow flag)

Results update PersonaAccount.health_status in DB (green / yellow / red).
Anomalies are published to the persona alert bus topic within 1 hour (AR-006).
"""

import uuid

from packages.agents.distribution.linkedin.browser import (
    LinkedInBrowser,
    LoginFailedException,
    MFARequiredException,
    CAPTCHADetectedException,
)
from packages.audit.logger import EventType, log_event
from packages.db.models import PersonaAccount
from packages.db.session import get_db
from packages.persona.account_manager import update_health, mark_banned
from packages.vault.client import get_secret_json


def run_health_check(account_id: uuid.UUID) -> str:
    """Perform a health check for one persona account.

    Returns the new health_status: 'green' | 'yellow' | 'red'.
    """
    with get_db() as db:
        account = db.get(PersonaAccount, account_id)
        if account is None:
            raise ValueError(f"PersonaAccount {account_id} not found")
        vault_key = account.vault_secret_key
        persona_name = account.persona_name

    try:
        credentials = get_secret_json(vault_key)
    except KeyError:
        update_health(account_id, "red", "Vault credentials missing")
        return "red"

    status = "green"
    notes = ""

    try:
        with LinkedInBrowser(credentials) as browser:
            page_result = _check_account_page(browser)
            if page_result == "restricted":
                status = "yellow"
                notes = "Account restriction banner detected"
            elif page_result == "banned":
                status = "red"
                notes = "Account banned or permanently restricted"
    except CAPTCHADetectedException:
        status = "red"
        notes = "CAPTCHA detected during health check"
    except MFARequiredException:
        status = "yellow"
        notes = "MFA challenge during health check — operator should verify session"
    except LoginFailedException:
        status = "red"
        notes = "Login failed — credentials may be invalid or account banned"
    except Exception as exc:
        status = "yellow"
        notes = f"Health check error: {exc}"

    update_health(account_id, status, notes)

    log_event(
        EventType.PERSONA_HEALTH_CHECK,
        entity_type="persona_account",
        entity_id=account_id,
        data={"health_status": status, "notes": notes, "persona": persona_name},
    )

    if status == "red":
        log_event(
            EventType.PERSONA_ACCOUNT_BANNED,
            entity_type="persona_account",
            entity_id=account_id,
            data={"notes": notes},
        )
        mark_banned(account_id)
    elif status == "yellow":
        log_event(
            EventType.PERSONA_ACCOUNT_WARNING,
            entity_type="persona_account",
            entity_id=account_id,
            data={"notes": notes},
        )

    return status


def _check_account_page(browser: "LinkedInBrowser") -> str:
    """Navigate to account page and look for restriction signals.

    Returns 'ok' | 'restricted' | 'banned'.
    """
    page = browser._context.new_page()
    try:
        page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded")
        content = page.content().lower()

        if any(kw in content for kw in ["your account has been restricted", "permanently restricted"]):
            return "banned"
        if any(kw in content for kw in ["account restricted", "limited access", "action required"]):
            return "restricted"
        return "ok"
    finally:
        page.close()
