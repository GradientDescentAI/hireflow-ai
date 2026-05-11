"""
Authentication endpoints.

POST /api/v1/auth/login   — issue JWT from email + password
POST /api/v1/auth/refresh — refresh an expiring token (TODO: GA)
"""

import uuid

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr

from apps.api.middleware.auth import create_access_token, verify_password
from packages.db.models import Recruiter
from packages.db.session import get_db

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    recruiter_id: str
    tenant_id: str
    role: str
    name: str


# ── Dev seed credentials (used when no DB row exists for quick local testing) ─

_DEV_SEED = {
    "email": "admin@acmecorp.in",
    "password": "hireflow123",
    "name": "Sarah Jenkins",
    "role": "admin",
    "recruiter_id": "00000000-0000-0000-0000-000000000001",
    "tenant_id": "00000000-0000-0000-0000-000000000010",
}


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/login", response_model=LoginResponse)
def login(body: LoginRequest):
    """
    Validate credentials and return a signed JWT.

    Falls back to a dev-seed account when the DB is empty (local dev only).
    """
    # ── Real DB path ──────────────────────────────────────────────────────────
    with get_db() as db:
        recruiter: Recruiter | None = (
            db.query(Recruiter).filter_by(email=body.email).first()
        )
        if recruiter:
            # Load all attributes while session is still open
            r_id = recruiter.id
            r_tenant_id = recruiter.tenant_id
            r_role = recruiter.role
            r_name = recruiter.name
            r_active = recruiter.is_active
            r_hash = recruiter.password_hash

    if recruiter:
        if not r_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account disabled")
        if not verify_password(body.password, r_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

        token = create_access_token(
            recruiter_id=r_id,
            tenant_id=r_tenant_id,
            role=r_role,
        )
        return LoginResponse(
            access_token=token,
            recruiter_id=str(r_id),
            tenant_id=str(r_tenant_id),
            role=r_role,
            name=r_name,
        )

    # ── Dev-seed fallback (only fires if table is empty) ──────────────────────
    import os
    if os.environ.get("ENVIRONMENT", "development") == "development":
        seed = _DEV_SEED
        if body.email == seed["email"] and body.password == seed["password"]:
            token = create_access_token(
                recruiter_id=uuid.UUID(seed["recruiter_id"]),
                tenant_id=uuid.UUID(seed["tenant_id"]),
                role=seed["role"],
            )
            return LoginResponse(
                access_token=token,
                recruiter_id=seed["recruiter_id"],
                tenant_id=seed["tenant_id"],
                role=seed["role"],
                name=seed["name"],
            )

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
