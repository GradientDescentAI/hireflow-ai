"""
Idempotent seed: creates demo tenant/recruiter and persona accounts.
Called from start.sh at every container startup — safe to run repeatedly.
"""
import sys
import os
import uuid

sys.path.insert(0, "/app")

# pylint: disable=wrong-import-position
from packages.db.session import get_db  # noqa: E402
from packages.db.models import Tenant, Recruiter, PersonaAccount  # noqa: E402
import bcrypt  # noqa: E402

DEMO_TENANT_ID = "00000000-0000-0000-0000-000000000010"
DEMO_EMAIL = os.environ.get("DEMO_EMAIL", "demo@hireflow.in")
DEMO_PASSWORD = os.environ.get("DEMO_PASSWORD", "demo1234")


def _seed_demo_tenant() -> None:
    with get_db() as db:
        if db.query(Tenant).filter_by(id=DEMO_TENANT_ID).first():
            print(f"[seed] Tenant {DEMO_TENANT_ID} already exists — skipping.")
            return

        tenant = Tenant(
            id=DEMO_TENANT_ID,
            name="Demo Company",
            domain="demo.hireflow.in",
            status="active",
            plan="pro",
        )
        db.add(tenant)

        pw_hash = bcrypt.hashpw(DEMO_PASSWORD.encode(), bcrypt.gensalt()).decode()
        recruiter = Recruiter(
            id=str(uuid.uuid4()),
            tenant_id=DEMO_TENANT_ID,
            email=DEMO_EMAIL,
            password_hash=pw_hash,
            name="Demo Recruiter",
            role="admin",
            is_active=True,
        )
        db.add(recruiter)
        db.commit()
        print(f"[seed] Created demo tenant + recruiter ({DEMO_EMAIL})")


def _seed_linkedin_persona() -> None:
    """Create the Riya LinkedIn persona account used by the distribution agent.

    The vault_secret_key 'linkedin/riya' maps to env var LINKEDIN_RIYA
    (EnvVaultBackend: uppercases + replaces / with _).
    Set LINKEDIN_RIYA on the worker service to a JSON string:
      {"username": "...", "password": "...", "proxy_url": null, "cookies": null}
    """
    with get_db() as db:
        if db.query(PersonaAccount).filter_by(
            persona_name="riya", platform="linkedin"
        ).first():
            print("[seed] LinkedIn persona (riya) already exists — skipping.")
            return

        account = PersonaAccount(
            id=uuid.uuid4(),
            persona_name="riya",
            platform="linkedin",
            region="india",
            vault_secret_key="linkedin/riya",
            is_primary=True,
            is_active=True,
            is_banned=False,
            health_status="green",
        )
        db.add(account)
        db.commit()
        print("[seed] Created LinkedIn persona account (riya)")


def seed() -> None:
    _seed_demo_tenant()
    _seed_linkedin_persona()


if __name__ == "__main__":
    seed()
