"""
Redis Streams publisher.

All agent-to-agent messages are published via publish().
Messages are JSON-serialised and include a mandatory tenant_id field
so consumers can enforce multi-tenant isolation.
"""

import json
import os
import uuid
from datetime import datetime, timezone
from typing import Any

import redis


def _get_redis() -> redis.Redis:
    return redis.from_url(os.environ["REDIS_URL"], decode_responses=True)


def publish(
    topic: str,
    payload: dict[str, Any],
    *,
    tenant_id: str | uuid.UUID | None = None,
    maxlen: int = 10_000,
) -> str:
    """Publish a message to a Redis Stream.

    Returns the stream entry ID.
    """
    r = _get_redis()

    message = {
        "tenant_id": str(tenant_id) if tenant_id else "",
        "published_at": datetime.now(timezone.utc).isoformat(),
        "payload": json.dumps(payload, default=str),
    }

    entry_id = r.xadd(topic, message, maxlen=maxlen, approximate=True)
    return entry_id
