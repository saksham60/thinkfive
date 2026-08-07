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
    if state.get("active_alert_id"):
        bundle["active_alert_id"] = state["active_alert_id"]
    if state.get("active_case_id"):
        bundle["active_case_id"] = state["active_case_id"]
    if state.get("active_approval_id"):
        bundle["active_approval_id"] = state["active_approval_id"]
    if state.get("pending_human_action"):
        bundle["pending_human_action"] = state["pending_human_action"]
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
        HumanMessage(content="Produce the final customer-facing response grounded strictly in the evidence above."),
    ]

    try:
        response = await llm.ainvoke(
            messages,
            config=llm_trace_config("synthesis", "response", agent_config.get("version")),
        )

        return {
            "final_response": response.final_response,
            "messages": [AIMessage(content=response.final_response)],
            "warnings": state.get("warnings", []) + response.warnings,
        }

    except Exception as e:
        logger.error(f"Synthesis Agent execution failed: {e}")
        fallback = "I'm sorry, I encountered an issue completing your request. Please try again or contact support."
        return {
            "final_response": fallback,
            "messages": [AIMessage(content=fallback)],
            "errors": state.get("errors", []) + [f"Synthesis Agent failed: {str(e)}"],
        }
