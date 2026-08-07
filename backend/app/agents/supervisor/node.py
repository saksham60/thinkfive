"""Supervisor Agent LangGraph node."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig

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
            parts.append(f"- {key}: {evidence.get('findings', 'present')}")
    if not parts:
        return "(no evidence collected yet)"
    return "\n".join(parts)


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
        decision = await llm.ainvoke(prompt_messages)

        return {
            "next_agent": decision.next_agent,
            "current_goal": decision.goal,
            "routing_reason": decision.reason,
            "iteration_count": iteration_count,
            "pending_human_action": (
                {"type": "clarification", "question": decision.clarification_question}
                if decision.needs_clarification
                else state.get("pending_human_action")
            ),
        }

    except Exception as e:
        logger.error(f"Supervisor Agent execution failed: {e}")
        return {
            "next_agent": "synthesis",
            "iteration_count": iteration_count,
            "errors": state.get("errors", []) + [f"Supervisor failed: {str(e)}"],
        }
