"""
JWT authentication middleware + RBAC helpers.

Every request to /api/v1/* must carry a valid Bearer JWT.
/health and /docs are excluded.

Token payload:
  sub       — recruiter_id (UUID string)
  tenant_id — UUID string
  role      — recruiter | hiring_manager | admin | super_admin
  exp       — expiry timestamp
"""

import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import bcrypt as _bcrypt
from jose import JWTError, jwt

JWT_SECRET = os.environ.get("JWT_SECRET", "insecure_dev_secret")
JWT_ALGORITHM = os.environ.get("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_MINUTES = int(os.environ.get("JWT_EXPIRE_MINUTES", "60"))
bearer_scheme = HTTPBearer(auto_error=False)

UNPROTECTED_PATHS = {"/health", "/docs", "/openapi.json", "/redoc"}


# ── Token creation ─────────────────────────────────────────────────────────────

def create_access_token(
    recruiter_id: uuid.UUID,
    tenant_id: uuid.UUID,
    role: str,
) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MINUTES)
    payload = {
        "sub": str(recruiter_id),
        "tenant_id": str(tenant_id),
        "role": role,
        "exp": expire,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


# ── Token validation ───────────────────────────────────────────────────────────

class TokenData:
    def __init__(self, payload: dict) -> None:
        self.recruiter_id = uuid.UUID(payload["sub"])
        self.tenant_id = uuid.UUID(payload["tenant_id"])
        self.role: str = payload["role"]


def _decode_token(token: str) -> TokenData:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return TokenData(payload)
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")


# ── FastAPI dependency ─────────────────────────────────────────────────────────

def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> TokenData:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return _decode_token(credentials.credentials)


def require_role(*allowed_roles: str):
    def dependency(user: Annotated[TokenData, Depends(get_current_user)]) -> TokenData:
        if user.role not in allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return user
    return dependency


# ── Password utilities ─────────────────────────────────────────────────────────

def hash_password(plain: str) -> str:
    return _bcrypt.hashpw(plain.encode(), _bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return _bcrypt.checkpw(plain.encode(), hashed.encode())
    except Exception:
        return False
