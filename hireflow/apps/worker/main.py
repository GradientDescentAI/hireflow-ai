"""
HireFlow AI worker — LangGraph agent runner.

Subscribes to Redis Streams bus topics and dispatches to the appropriate
agent or graph node.  One worker process handles all topics; scale by running
multiple worker processes (each gets a unique consumer name within the group).
"""

import os
import signal
import sys
import uuid

import structlog

from packages.bus.consumer import ack, consume, ensure_group, nack_to_dead_letter
from packages.bus.topics import Topics
from packages.db.session import check_connection

log = structlog.get_logger()

_CONSUMER_NAME = f"worker-{uuid.uuid4().hex[:8]}"
_SHUTDOWN = False


def _handle_signal(sig, frame):
    global _SHUTDOWN
    log.info("shutdown_signal_received", signal=sig)
    _SHUTDOWN = True


signal.signal(signal.SIGTERM, _handle_signal)
signal.signal(signal.SIGINT, _handle_signal)


# ── Topic handlers ────────────────────────────────────────────────────────────

def process_jd_approved(payload: dict, tenant_id: str) -> None:
    """JD_APPROVED → run JD Intake + Distribution via the hiring graph."""
    from apps.worker.graph import hiring_graph

    job_id = payload.get("job_id")
    if not job_id:
        log.error("jd_approved_missing_job_id", payload=payload)
        return

    log.info("pipeline_start", job_id=job_id, tenant_id=tenant_id)

    initial_state = {
        "job_id": job_id,
        "tenant_id": tenant_id,
        "plan": payload.get("plan", "free"),
        "company_name": payload.get("company_name", ""),
        "channels": payload.get("channels", ["linkedin"]),
        "channel_config": payload.get("channel_config", {}),
        "jd_confirmed": False,
        "scoring_errors": [],
        "pipeline_error": None,
        "status": "started",
    }

    result = hiring_graph.invoke(
        initial_state,
        config={"configurable": {"thread_id": job_id}},
    )
    log.info("pipeline_jd_phase_complete", job_id=job_id, status=result.get("status"))


def process_distribution_started(payload: dict, tenant_id: str) -> None:
    """DISTRIBUTION_STARTED → fan out to channel agents via the orchestrator."""
    from packages.agents.distribution import orchestrator as distribution_agent

    job_id = payload.get("job_id")
    channels = payload.get("channels", ["linkedin"])
    channel_config = payload.get("channel_config", {})

    if not job_id:
        log.error("distribution_started_missing_job_id", payload=payload)
        return

    log.info("distribution_start", job_id=job_id, channels=channels, tenant_id=tenant_id)

    result = distribution_agent.run(
        job_id=job_id,
        tenant_id=tenant_id,
        channels=channels,
        channel_config=channel_config,
    )
    log.info("distribution_complete", job_id=job_id, result=result)


def process_application_received(payload: dict, tenant_id: str) -> None:
    """APPLICATION_RECEIVED → parse the candidate's CV."""
    from packages.agents.parsing import agent as parsing_agent

    candidate_id = payload.get("candidate_id")
    job_id = payload.get("job_id")
    # cv_file_key is published by the upload-cv endpoint; s3_key is the legacy field name
    s3_key = payload.get("s3_key") or payload.get("cv_file_key")

    if not all([candidate_id, job_id, s3_key]):
        log.error("application_received_missing_fields", payload=payload)
        return

    log.info("parsing_start", candidate_id=candidate_id, job_id=job_id)

    result = parsing_agent.run(
        candidate_id=candidate_id,
        job_id=job_id,
        tenant_id=tenant_id,
        s3_key=s3_key,
    )
    log.info(
        "parsing_complete",
        candidate_id=candidate_id,
        status=result.get("status"),
        confidence=result.get("confidence"),
    )


def process_cv_parsed(payload: dict, tenant_id: str) -> None:
    """CV_PARSED — ack each parse; if trigger=manual_score_request, run batch scoring."""
    job_id = payload.get("job_id")
    candidate_id = payload.get("candidate_id")
    trigger = payload.get("trigger", "")

    log.info(
        "cv_parsed_ack",
        candidate_id=candidate_id,
        job_id=job_id,
        tenant_id=tenant_id,
    )

    if trigger == "manual_score_request" and job_id:
        from packages.agents.scoring import agent as scoring_agent
        log.info("scoring_start", job_id=job_id, tenant_id=tenant_id)
        result = scoring_agent.run(job_id=job_id, tenant_id=tenant_id)
        log.info("scoring_complete", job_id=job_id, scored=result.get("scored"), tenant_id=tenant_id)


def process_scoring_complete(payload: dict, tenant_id: str) -> None:
    """SCORING_COMPLETE → run Evaluation + Delivery via the hiring graph."""
    from apps.worker.graph import hiring_graph

    job_id = payload.get("job_id")
    if not job_id:
        log.error("scoring_complete_missing_job_id", payload=payload)
        return

    log.info("evaluation_start", job_id=job_id, tenant_id=tenant_id)

    state = {
        "job_id": job_id,
        "tenant_id": tenant_id,
        "plan": payload.get("plan", "free"),
        "scored_count": payload.get("scored_count", 0),
        "scoring_errors": [],
        "pipeline_error": None,
        "status": "scoring_complete",
    }

    result = hiring_graph.invoke(
        state,
        config={"configurable": {"thread_id": f"{job_id}-eval"}},
    )
    log.info("delivery_complete", job_id=job_id, status=result.get("status"))


_TOPIC_HANDLERS = {
    Topics.JD_APPROVED: process_jd_approved,
    Topics.DISTRIBUTION_STARTED: process_distribution_started,
    Topics.APPLICATION_RECEIVED: process_application_received,
    Topics.CV_PARSED: process_cv_parsed,
    Topics.SCORING_COMPLETE: process_scoring_complete,
}


# ── Startup ───────────────────────────────────────────────────────────────────

def _startup_check() -> None:
    log.info("worker_startup")

    if not check_connection():
        log.error("db_connection_failed")
        sys.exit(1)
    log.info("db_connected")

    import redis as redis_lib
    r = redis_lib.from_url(os.environ["REDIS_URL"])
    r.ping()
    log.info("redis_connected")

    for topic in _TOPIC_HANDLERS:
        ensure_group(topic, Topics.GROUP_WORKER)
    log.info("consumer_groups_ready", topics=list(_TOPIC_HANDLERS.keys()))

    log.info("worker_ready", consumer=_CONSUMER_NAME)


def run() -> None:
    _startup_check()

    while not _SHUTDOWN:
        for topic, handler in _TOPIC_HANDLERS.items():
            try:
                for msg in consume(topic, Topics.GROUP_WORKER, _CONSUMER_NAME, count=5, block_ms=200):
                    try:
                        handler(msg.payload, msg.tenant_id)
                        ack(topic, Topics.GROUP_WORKER, msg.entry_id)
                    except Exception as exc:
                        log.error(
                            "message_processing_error",
                            topic=topic,
                            entry_id=msg.entry_id,
                            error=str(exc),
                        )
                        nack_to_dead_letter(topic, Topics.GROUP_WORKER, msg.entry_id, str(exc))
                    if _SHUTDOWN:
                        break
            except Exception as exc:
                log.error("consumer_error", topic=topic, error=str(exc))

    log.info("worker_shutdown")


if __name__ == "__main__":
    run()
