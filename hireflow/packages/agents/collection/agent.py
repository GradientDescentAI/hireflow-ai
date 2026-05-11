"""
Application Collection Agent — AC-001 to AC-012.

Runs as a long-lived thread per active job.  Starts IMAP IDLE for the
role's inbox, processes each inbound email, sends acks, and publishes
APPLICATION_RECEIVED events to the bus.

Called from the worker main loop:
  - start_collection(job_id, tenant_id) → spawns thread
  - stop_collection(job_id) → signals thread to exit
"""

import threading
import uuid
from datetime import datetime, timezone

from packages.agents.collection.acknowledger import send_ack, send_missing_attachment_request
from packages.agents.collection.extractor import process_email
from packages.agents.collection.imap_listener import listen, RawEmail
from packages.audit.logger import EventType, log_event
from packages.bus.publisher import publish
from packages.bus.topics import Topics
from packages.db.models import Job
from packages.db.session import get_db

_active_threads: dict[str, threading.Thread] = {}
_stop_events: dict[str, threading.Event] = {}


def start_collection(job_id: str, tenant_id: str) -> None:
    """Start IMAP collection for a job in a background thread."""
    if job_id in _active_threads and _active_threads[job_id].is_alive():
        return  # Already running

    stop_event = threading.Event()
    _stop_events[job_id] = stop_event

    thread = threading.Thread(
        target=_collection_loop,
        args=(job_id, tenant_id, stop_event),
        name=f"collection-{job_id[:8]}",
        daemon=True,
    )
    _active_threads[job_id] = thread
    thread.start()


def stop_collection(job_id: str) -> None:
    """Stop the collection thread for a job."""
    if job_id in _stop_events:
        _stop_events[job_id].set()


def _collection_loop(job_id: str, tenant_id: str, stop_event: threading.Event) -> None:
    """Main loop: listens for emails and processes them."""
    role_id = job_id[:8].upper()

    # Load job context
    with get_db() as db:
        job = db.get(Job, uuid.UUID(job_id))
        if job is None:
            return
        job_title = job.title
        collection_open_until = job.collection_open_until

    # Get company name
    with get_db() as db:
        from packages.db.models import Tenant
        tenant = db.get(Tenant, uuid.UUID(tenant_id))
        company_name = tenant.name if tenant else "the company"

    def on_email_received(raw: RawEmail) -> None:
        # Check collection window (AC-012)
        if collection_open_until:
            now = datetime.now(timezone.utc).replace(tzinfo=None)
            if now > collection_open_until:
                # Auto-respond after close
                _send_closed_response(raw.sender_email, job_title, company_name)
                return

        result = process_email(raw, job_id, tenant_id, role_id)
        status = result.get("status")

        if status == "received":
            # Send ack (AC-007)
            try:
                send_ack(
                    to_email=raw.sender_email,
                    candidate_name=raw.sender_name or None,
                    job_title=job_title,
                    role_id=role_id,
                    company_name=company_name,
                )
                log_event(
                    EventType.ACKNOWLEDGEMENT_SENT,
                    tenant_id=uuid.UUID(tenant_id),
                    entity_type="candidate",
                    entity_id=uuid.UUID(result["candidate_id"]),
                    data={"to": raw.sender_email},
                )
            except Exception:
                pass  # ack failure is non-fatal

            # Publish to bus so Parsing Agent picks it up
            publish(
                Topics.APPLICATION_RECEIVED,
                {
                    "candidate_id": result["candidate_id"],
                    "job_id": job_id,
                    "s3_key": result["s3_key"],
                },
                tenant_id=tenant_id,
            )

        elif status == "missing_attachment":
            try:
                send_missing_attachment_request(
                    to_email=raw.sender_email,
                    candidate_name=raw.sender_name or None,
                    job_title=job_title,
                    role_id=role_id,
                    company_name=company_name,
                )
            except Exception:
                pass

    listen(role_id, stop_event, on_email_received)


def _send_closed_response(to_email: str, job_title: str, company_name: str) -> None:
    try:
        from packages.agents.collection.acknowledger import _send
        _send(
            to_email,
            f"Re: {job_title} application",
            f"Thank you for your interest. Applications for {job_title} at {company_name} are now closed.",
        )
    except Exception:
        pass
