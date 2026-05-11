from fastapi import APIRouter
from packages.db.session import check_connection
import redis
import os

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check():
    db_ok = check_connection()

    redis_ok = False
    try:
        r = redis.from_url(os.environ.get("REDIS_URL", "redis://localhost:6379/0"))
        r.ping()
        redis_ok = True
    except Exception:
        pass

    status = "ok" if (db_ok and redis_ok) else "degraded"
    return {
        "status": status,
        "db": "ok" if db_ok else "error",
        "redis": "ok" if redis_ok else "error",
    }
