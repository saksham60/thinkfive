"""Supervisor Agent LangGraph node."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig

from app.observability.langsmith import llm_trace_config

if TYPE_CHECKING:
    from app.agents.graph.state import GraphState

logger = logging.getLogger(__name__)

MAX_ITERATIONS_DEFAULT = 15


def _summarize_evidence(state: GraphState) -> str:
    """Build a compact evidence summary string for the supervisor prompt."""
    parts = []
    for key in ("banking_evidence", "fraud_evidence", "policy_evidence", "case_evidence"):
        evidence: dict[str, Any] | None = state.get(key)  # type: ignore[assignment]
        if evidence:
            detail = f"- {key}: {evidence.get('findings', 'present')}"
            if key == "banking_evidence":
                detail += (
                    f"; attempt_status={evidence.get('attempt_status', 'unknown')}"
                    f"; transaction_resolution_status="
                    f"{evidence.get('transaction_resolution_status', 'unknown')}"
                    f"; requires_clarification={evidence.get('requires_clarification', False)}"
                )
            parts.append(detail)
    if not parts:
        memory = state.get("memory_context") or {}
        parts.append("- no live evidence collected yet")
        if memory:
            parts.append(f"- customer_memory (non-authoritative): {memory}")
    memory = state.get("memory_context") or {}
    if memory and "- no live evidence collected yet" not in parts:
        parts.append(f"- customer_memory (non-authoritative): {memory}")
    if state.get("active_transaction_id"):
        parts.append(f"- verified_active_transaction_id: {state['active_transaction_id']}")
    elif state.get("requested_transaction_id"):
        parts.append("- untrusted_requested_transaction_id: present but not validated")
    if state.get("errors"):
        parts.append(f"- errors: {state['errors']}")
    if state.get("warnings"):
        parts.append(f"- warnings: {state['warnings']}")
    return "\n".join(parts)


def _banking_retry_blocked(state: GraphState) -> bool:
    evidence = state.get("banking_evidence") or {}
    if evidence.get("attempt_status") == "failed":
        return True
    return bool(evidence.get("transaction_lookup_attempted")) and evidence.get(
        "transaction_resolution_status"
    ) in {"unresolved", "ambiguous", "failed"}


async def supervisor_node(state: GraphState, config: RunnableConfig) -> dict[str, Any]:
    """Supervisor node - decides routing via structured LLM output only."""
    logger.info("Supervisor Agent node executing")

    supervisor_agent = config.get("configurable", {}).get("supervisor_agent")
    if not supervisor_agent:
        raise ValueError("Supervisor Agent not configured")

    iteration_count = state.get("iteration_count", 0) + 1
    max_iterations = config.get("configurable", {}).get("max_iterations", MAX_ITERATIONS_DEFAULT)

    # Force synthesis if max iterations reached (bounded graph execution)
    if iteration_count >= max_iterations:
        logger.warning(f"Max iterations ({max_iterations}) reached, forcing synthesis")
        return {
            "next_agent": "synthesis",
            "iteration_count": iteration_count,
            "warnings": state.get("warnings", []) + ["Max iterations reached - forcing synthesis"],
        }

    evidence_summary = _summarize_evidence(state)
    agent_config = supervisor_agent.create_agent(evidence_summary, iteration_count, max_iterations)
    llm = agent_config["llm"]
    prompt = agent_config["prompt"]

    messages = state.get("messages", [])
    latest_user_message = ""
    for msg in reversed(messages):
        role = getattr(msg, "type", None) or (msg.get("role") if isinstance(msg, dict) else None)
        if role in ("human", "user"):
            latest_user_message = getattr(msg, "content", None) or msg.get("content", "")
            break

    prompt_messages = [
        SystemMessage(content=prompt),
        HumanMessage(content=f"Customer message: {latest_user_message}\n\nDecide the next routing step."),
    ]

    try:
        decision = await llm.ainvoke(
            prompt_messages,
            config=llm_trace_config("supervisor", "routing", agent_config.get("version")),
        )

        next_agent = decision.next_agent
        pending_human_action = (
            {"type": "clarification", "question": decision.clarification_question}
            if decision.needs_clarification
            else state.get("pending_human_action")
        )
        routing_reason = decision.reason
        warnings = state.get("warnings", [])

        if next_agent == "banking" and _banking_retry_blocked(state):
            banking_evidence = state.get("banking_evidence") or {}
            question = banking_evidence.get("clarification_question") or (
                "Please provide more transaction details, such as the merchant, amount, or date."
            )
            next_agent = "synthesis"
            pending_human_action = {"type": "clarification", "question": question}
            routing_reason = (
                "Banking already attempted this lookup without resolving a verified transaction; "
                "the same route will not be repeated without new customer evidence."
            )
            warnings = [*warnings, "Repeated unresolved Banking route prevented"]

        return {
            "next_agent": next_agent,
            "current_goal": decision.goal,
            "routing_reason": routing_reason,
            "iteration_count": iteration_count,
            "pending_human_action": pending_human_action,
            "warnings": warnings,
        }

    except Exception as e:
        logger.error(f"Supervisor Agent execution failed: {e}")
        return {
            "next_agent": "synthesis",
            "iteration_count": iteration_count,
            "errors": state.get("errors", []) + [f"Supervisor failed: {str(e)}"],
        }
