"""Synthesis Agent LangGraph node - terminal node producing final_response."""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig

from app.observability.langsmith import llm_trace_config

if TYPE_CHECKING:
    from app.agents.graph.state import GraphState

logger = logging.getLogger(__name__)


def _build_evidence_bundle(state: GraphState) -> str:
    """Serialize all evidence buckets for the synthesis prompt."""
    bundle: dict[str, Any] = {}
    for key in ("banking_evidence", "fraud_evidence", "policy_evidence", "case_evidence"):
        value = state.get(key)  # type: ignore[assignment]
        if value:
            bundle[key] = value

    if state.get("active_transaction_id"):
        bundle["active_transaction_id"] = state["active_transaction_id"]
    if state.get("active_transaction"):
        bundle["active_transaction"] = state["active_transaction"]
    if state.get("recent_transaction_candidates"):
        bundle["recent_transaction_candidates_in_display_order"] = state[
            "recent_transaction_candidates"
        ]
    if state.get("active_alert_id"):
        bundle["active_alert_id"] = state["active_alert_id"]
    if state.get("active_case_id"):
        bundle["active_case_id"] = state["active_case_id"]
    if state.get("active_approval_id"):
        bundle["active_approval_id"] = state["active_approval_id"]
    if state.get("pending_human_action"):
        bundle["pending_human_action"] = state["pending_human_action"]
    if state.get("pending_confirmation"):
        bundle["pending_confirmation"] = state["pending_confirmation"]
    if state.get("primary_user_goal"):
        bundle["primary_user_goal"] = state["primary_user_goal"]
    if state.get("customer_requested_formal_case"):
        bundle["customer_requested_formal_case"] = True
    if state.get("conversation_summary"):
        bundle["conversation_summary"] = state["conversation_summary"]
    recent_turns: list[dict[str, Any]] = []
    for message in state.get("messages", [])[-8:]:
        role = getattr(message, "type", None)
        content = getattr(message, "content", None)
        if role in {"human", "ai"} and content:
            recent_turns.append({"role": role, "content": content})
    if recent_turns:
        bundle["bounded_conversation"] = recent_turns
    if state.get("memory_context"):
        bundle["customer_memory_non_authoritative"] = state["memory_context"]

    return json.dumps(bundle, indent=2, default=str) if bundle else "(no evidence collected)"


async def synthesis_node(state: GraphState, config: RunnableConfig) -> dict[str, Any]:
    """Synthesis node - combines evidence into the final grounded response."""
    logger.info("Synthesis Agent node executing")

    synthesis_agent = config.get("configurable", {}).get("synthesis_agent")
    if not synthesis_agent:
        raise ValueError("Synthesis Agent not configured")

    evidence_bundle = _build_evidence_bundle(state)
    agent_config = synthesis_agent.create_agent(evidence_bundle)
    llm = agent_config["llm"]
    prompt = agent_config["prompt"]

    messages = [
        SystemMessage(content=prompt),
        HumanMessage(
            content=(
                "Respond to the latest customer turn using the bounded conversation and grounded "
                "evidence above. Preserve conversational continuity."
            )
        ),
    ]

    try:
        response = await llm.ainvoke(
            messages,
            config=llm_trace_config("synthesis", "response", agent_config.get("version")),
        )

        return {
            "final_response": response.final_response,
            "messages": [
                AIMessage(
                    content=response.final_response,
                    id=f"assistant:{state.get('run_id', 'unknown')}",
                )
            ],
            "warnings": state.get("warnings", []) + response.warnings,
        }

    except Exception as e:
        logger.error(f"Synthesis Agent execution failed: {e}")
        fallback = "I'm sorry, I encountered an issue completing your request. Please try again or contact support."
        return {
            "final_response": fallback,
            "messages": [
                AIMessage(content=fallback, id=f"assistant:{state.get('run_id', 'unknown')}")
            ],
            "errors": state.get("errors", []) + [f"Synthesis Agent failed: {str(e)}"],
        }
