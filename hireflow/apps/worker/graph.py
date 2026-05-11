"""
LangGraph hiring pipeline — agent DAG definition.

Each node calls the corresponding Phase 1 agent. Nodes communicate through
pipeline state; cross-service coordination uses the Redis Streams bus.
Collection → parsing and scoring are bus-driven, not graph edges.
"""

import operator
from typing import Annotated, Any, Optional, TypedDict

from langgraph.graph import END, StateGraph

from packages.agents.collection import agent as collection_agent
from packages.agents.delivery import agent as delivery_agent
from packages.agents.distribution import orchestrator as distribution_agent
from packages.agents.evaluation import agent as evaluation_agent
from packages.agents.jd_intake import agent as jd_intake_agent
from packages.agents.parsing import agent as parsing_agent
from packages.agents.scoring import agent as scoring_agent


# ── Pipeline state ────────────────────────────────────────────────────────────

class HireFlowState(TypedDict, total=False):
    # Identifiers
    job_id: str
    tenant_id: str
    candidate_id: str          # set for per-candidate parsing runs
    s3_key: str                # set for per-candidate parsing runs

    # Tenant / plan context
    plan: str
    company_name: str
    channels: list[str]
    channel_config: dict[str, Any]

    # JD Intake outputs
    jd_confirmed: bool
    jd_bias_flags: list[str]
    karnataka_salary_warning: bool

    # Distribution outputs
    distribution_result: dict[str, Any]
    collection_email: str

    # Parsing outputs (per-candidate)
    parse_confidence: float
    parse_flagged: bool

    # Scoring outputs
    scored_count: int
    scoring_errors: Annotated[list, operator.add]
    bias_audit_passed: bool

    # Evaluation + Delivery outputs
    shortlist_size: int
    recruiter_notified: bool

    # Pipeline control
    pipeline_error: Optional[str]
    status: str


# ── Node implementations ──────────────────────────────────────────────────────

def jd_intake_node(state: HireFlowState) -> dict:
    result = jd_intake_agent.run(
        job_id=state["job_id"],
        tenant_id=state["tenant_id"],
    )
    return {
        "jd_confirmed": result.get("status") in ("extraction_complete", "cached"),
        "jd_bias_flags": result.get("bias_flags", []),
        "karnataka_salary_warning": result.get("karnataka_salary_warning", False),
        "status": "jd_intake_complete",
    }


def distribution_node(state: HireFlowState) -> dict:
    result = distribution_agent.run(
        job_id=state["job_id"],
        tenant_id=state["tenant_id"],
        channels=state.get("channels", ["linkedin"]),
        channel_config=state.get("channel_config", {}),
    )
    return {
        "distribution_result": result,
        "collection_email": result.get("collection_email", ""),
        "status": "distribution_complete",
    }


def collection_node(state: HireFlowState) -> dict:
    """Start IMAP listener for this job.  Applications arrive via bus events."""
    collection_agent.start_collection(
        job_id=state["job_id"],
        tenant_id=state["tenant_id"],
    )
    return {"status": "collecting"}


def parsing_node(state: HireFlowState) -> dict:
    """Parse a single candidate CV — invoked per APPLICATION_RECEIVED bus event."""
    result = parsing_agent.run(
        candidate_id=state["candidate_id"],
        job_id=state["job_id"],
        tenant_id=state["tenant_id"],
        s3_key=state["s3_key"],
    )
    return {
        "parse_confidence": result.get("confidence", 0.0),
        "parse_flagged": result.get("flagged", False),
        "status": "parsed",
    }


def scoring_node(state: HireFlowState) -> dict:
    result = scoring_agent.run(
        job_id=state["job_id"],
        tenant_id=state["tenant_id"],
        plan=state.get("plan", "free"),
    )
    return {
        "scored_count": result.get("scored", 0),
        "bias_audit_passed": result.get("bias_audit_passed", True),
        "status": "scoring_complete",
    }


def evaluation_node(state: HireFlowState) -> dict:
    result = evaluation_agent.run(
        job_id=state["job_id"],
        tenant_id=state["tenant_id"],
        plan=state.get("plan", "free"),
    )
    return {
        "shortlist_size": result.get("shortlisted", 0),
        "bias_audit_passed": result.get("bias_audit_passed", True),
        "status": "evaluated",
    }


def delivery_node(state: HireFlowState) -> dict:
    result = delivery_agent.run(
        job_id=state["job_id"],
        tenant_id=state["tenant_id"],
    )
    return {
        "recruiter_notified": result.get("recruiter_notified", False),
        "status": "delivered",
    }


def error_node(state: HireFlowState) -> dict:
    return {"status": "error"}


# ── Routing ───────────────────────────────────────────────────────────────────

def route_after_intake(state: HireFlowState) -> str:
    if state.get("pipeline_error"):
        return "error"
    if not state.get("jd_confirmed"):
        return END          # pause — recruiter must confirm via POST /jobs/{id}/confirm
    return "distribution"


def route_after_scoring(state: HireFlowState) -> str:
    if state.get("pipeline_error") or not state.get("scored_count", 0):
        return "error"
    return "evaluation"


# ── Graph assembly ────────────────────────────────────────────────────────────

def build_hiring_graph():
    g = StateGraph(HireFlowState)

    g.add_node("jd_intake", jd_intake_node)
    g.add_node("distribution", distribution_node)
    g.add_node("collection", collection_node)
    g.add_node("parsing", parsing_node)
    g.add_node("scoring", scoring_node)
    g.add_node("evaluation", evaluation_node)
    g.add_node("delivery", delivery_node)
    g.add_node("error", error_node)

    g.set_entry_point("jd_intake")

    g.add_conditional_edges("jd_intake", route_after_intake, {
        "distribution": "distribution",
        "error": "error",
        END: END,
    })
    # Distribution starts collection listener; subsequent parsing is bus-driven
    g.add_edge("distribution", "collection")
    g.add_edge("collection", END)

    # Scoring → Evaluation → Delivery chain (triggered by POST /jobs/{id}/score)
    g.add_conditional_edges("scoring", route_after_scoring, {
        "evaluation": "evaluation",
        "error": "error",
    })
    g.add_edge("evaluation", "delivery")
    g.add_edge("delivery", END)
    g.add_edge("error", END)

    return g.compile()


hiring_graph = build_hiring_graph()
