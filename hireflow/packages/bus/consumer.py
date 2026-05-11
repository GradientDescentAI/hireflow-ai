"""
Redis Streams consumer.

Workers call consume() in a loop to receive messages from a stream.
Uses consumer groups so that multiple worker replicas share the load
without duplicate processing.

Idempotency is the responsibility of the agent that handles each message —
if a message is re-delivered after a crash, the agent must detect and skip
duplicate work (e.g. check if the DB record already exists).
"""

import json
import os
import time
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any

import redis


@dataclass
class Message:
    stream: str
    entry_id: str
    tenant_id: str
    published_at: str
    payload: dict[str, Any]
    raw: dict


def _get_redis() -> redis.Redis:
    return redis.from_url(os.environ["REDIS_URL"], decode_responses=True)


def ensure_group(stream: str, group: str) -> None:
    """Create the consumer group if it doesn't exist (idempotent)."""
    r = _get_redis()
    try:
        r.xgroup_create(stream, group, id="0", mkstream=True)
    except redis.exceptions.ResponseError as e:
        if "BUSYGROUP" not in str(e):
            raise


def consume(
    stream: str,
    group: str,
    consumer_name: str,
    *,
    count: int = 10,
    block_ms: int = 2000,
) -> Iterator[Message]:
    """Yield messages from a stream consumer group.

    Caller is responsible for calling ack() on each message after processing.
    """
    r = _get_redis()
    ensure_group(stream, group)

    while True:
        entries = r.xreadgroup(
            group, consumer_name, {stream: ">"}, count=count, block=block_ms
        )
        if not entries:
            continue

        for _stream, messages in entries:
            for entry_id, fields in messages:
                try:
                    payload = json.loads(fields.get("payload", "{}"))
                except json.JSONDecodeError:
                    payload = {}

                yield Message(
                    stream=stream,
                    entry_id=entry_id,
                    tenant_id=fields.get("tenant_id", ""),
                    published_at=fields.get("published_at", ""),
                    payload=payload,
                    raw=fields,
                )


def ack(stream: str, group: str, entry_id: str) -> None:
    _get_redis().xack(stream, group, entry_id)


def nack_to_dead_letter(stream: str, group: str, entry_id: str, error: str) -> None:
    """Acknowledge the message (remove from PEL) and write to dead-letter stream."""
    from packages.bus.topics import Topics

    r = _get_redis()
    r.xack(stream, group, entry_id)
    r.xadd(
        Topics.AGENT_ERROR,
        {"source_stream": stream, "entry_id": entry_id, "error": error},
        maxlen=5_000,
        approximate=True,
    )
