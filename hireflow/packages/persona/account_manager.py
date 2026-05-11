"""
LinkedIn persona account health monitoring and failover.

AR-001 to AR-007 from PRD §4.4.

Health check runs daily (scheduled in worker cron).
On ban or restriction: freeze account, failover to backup, notify operator.
"""

import os
import uuid
from datetime import datetime, timedelta, timezone

from packages.db.models import PersonaAccount
from packages.db.session import SessionLocal

MAX_POSTS_PER_DAY = int(os.environ.get("LINKEDIN_MAX_POSTS_PER_DAY", "3"))   # AR-001 default
MIN_POST_SPACING_MINUTES = 90                                                  # AR-001
POSTING_WINDOW_START = 9                                                       # 09:00 IST
POSTING_WINDOW_END = 19                                                        # 19:00 IST


# ── Post rate enforcement ─────────────────────────────────────────────────────

def can_post(account: PersonaAccount) -> tuple[bool, str]:
    """Return (allowed, reason). Enforces AR-001."""
    now = datetime.now(timezone.utc)

    # Reset daily counter at midnight UTC (close enough for IST)
    if account.posts_today_reset_at and now.date() > account.posts_today_reset_at.date():
        return True, "counter will be reset"

    if account.posts_today >= MAX_POSTS_PER_DAY:
        return False, f"daily limit of {MAX_POSTS_PER_DAY} posts reached"

    if account.is_banned or not account.is_active:
        return False, "account is banned or inactive"

    return True, "ok"


def record_post(account_id: uuid.UUID) -> None:
    """Increment today's post count."""
    db = SessionLocal()
    try:
        account = db.get(PersonaAccount, account_id)
        if account is None:
            return
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        if account.posts_today_reset_at is None or now.date() > account.posts_today_reset_at.date():
            account.posts_today = 1
            account.posts_today_reset_at = now
        else:
            account.posts_today += 1
        account.updated_at = now
        db.commit()
    finally:
        db.close()


# ── Health status management ──────────────────────────────────────────────────

def update_health(account_id: uuid.UUID, status: str, notes: str | None = None) -> None:
    """Set health_status to green|yellow|red. Notify operator on yellow/red."""
    db = SessionLocal()
    try:
        account = db.get(PersonaAccount, account_id)
        if account is None:
            return
        account.health_status = status
        account.last_health_check_at = datetime.now(timezone.utc).replace(tzinfo=None)
        if notes:
            account.notes = notes
        account.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
        db.commit()
    finally:
        db.close()

    if status in ("yellow", "red"):
        _notify_operator(account_id, status, notes or "")


def mark_banned(account_id: uuid.UUID) -> None:
    db = SessionLocal()
    try:
        account = db.get(PersonaAccount, account_id)
        if account is None:
            return
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        account.is_banned = True
        account.is_active = False
        account.health_status = "red"
        account.last_ban_at = now
        account.updated_at = now
        db.commit()
    finally:
        db.close()

    _initiate_failover(account_id)


# ── Failover ──────────────────────────────────────────────────────────────────

def get_active_primary(platform: str = "linkedin", region: str = "india") -> PersonaAccount | None:
    db = SessionLocal()
    try:
        return (
            db.query(PersonaAccount)
            .filter_by(platform=platform, region=region, is_primary=True, is_active=True, is_banned=False)
            .first()
        )
    finally:
        db.close()


def get_backup_account(platform: str = "linkedin", region: str = "india") -> PersonaAccount | None:
    """Return an aged (≥30 days) backup account ready for activation. AR-004."""
    cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=30)
    db = SessionLocal()
    try:
        return (
            db.query(PersonaAccount)
            .filter(
                PersonaAccount.platform == platform,
                PersonaAccount.region == region,
                PersonaAccount.is_primary == False,
                PersonaAccount.is_active == True,
                PersonaAccount.is_banned == False,
                PersonaAccount.account_aged_since <= cutoff,
            )
            .first()
        )
    finally:
        db.close()


def _initiate_failover(banned_account_id: uuid.UUID) -> None:
    """AR-005: on ban, promote backup within 4 hours. Notify operator."""
    backup = get_backup_account()
    if backup is None:
        _notify_operator(banned_account_id, "red", "NO BACKUP ACCOUNT AVAILABLE — manual intervention required")
        return

    db = SessionLocal()
    try:
        backup.is_primary = True
        backup.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
        db.commit()
    finally:
        db.close()

    _notify_operator(
        banned_account_id,
        "red",
        f"Primary banned. Failover to backup account {backup.id} ({backup.persona_name}) initiated.",
    )


def _notify_operator(account_id: uuid.UUID, severity: str, message: str) -> None:
    """Send operator alert via the message bus (AR-006: within 1 hour)."""
    from packages.bus.publisher import publish
    from packages.bus.topics import Topics

    publish(
        Topics.PERSONA_ALERT,
        {
            "account_id": str(account_id),
            "severity": severity,
            "message": message,
        },
    )
