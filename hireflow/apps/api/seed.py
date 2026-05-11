"""
One-time seed: creates the demo tenant and recruiter if they don't exist.
Called from start.sh at container startup (idempotent).
"""
import sys
import os
import uuid

sys.path.insert(0, "/app")

# pylint: disable=wrong-import-position
from packages.db.session import get_db  # noqa: E402
from packages.db.models import Tenant, Recruiter  # noqa: E402
import bcrypt  # noqa: E402

DEMO_TENANT_ID = "00000000-0000-0000-0000-000000000010"
DEMO_EMAIL = os.environ.get("DEMO_EMAIL", "demo@hireflow.in")
DEMO_PASSWORD = os.environ.get("DEMO_PASSWORD", "demo1234")


def seed() -> None:
    with get_db() as db:
        existing = db.query(Tenant).filter_by(id=DEMO_TENANT_ID).first()
        if existing:
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


if __name__ == "__main__":
    seed()
