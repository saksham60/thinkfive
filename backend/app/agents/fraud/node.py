"""Fraud Agent LangGraph node."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig

from app.agents.tool_loop import find_grounded_value, run_grounded_tool_loop

if TYPE_CHECKING:
    from app.agents.graph.state import GraphState

logger = logging.getLogger(__name__)


async def fraud_node(state: GraphState, config: RunnableConfig) -> dict[str, Any]:
    """Fraud Agent node - assesses transaction risk and manages alerts."""
    logger.info("Fraud Agent node executing")

    current_goal = state.get("current_goal", "")
    active_transaction_id = state.get("active_transaction_id")
    banking_evidence = state.get("banking_evidence", {})

    fraud_agent = config.get("configurable", {}).get("fraud_agent")
    if not fraud_agent:
        raise ValueError("Fraud Agent not configured")

    transaction_context = None
    if active_transaction_id:
        transaction_context = f"Transaction ID: {active_transaction_id}"
    elif banking_evidence:
        transaction_context = f"Banking evidence available: {banking_evidence.get('findings', '')}"

    agent_config = fraud_agent.create_agent(transaction_context)
    llm = agent_config["llm"]
    output_llm = agent_config["output_llm"]
    prompt = agent_config["prompt"]
    toolset = agent_config["toolset"]

    messages = [
        SystemMessage(content=prompt),
        HumanMessage(content=f"Goal: {current_goal}\n\nAssess fraud risk using available evidence."),
    ]

    try:
        configurable = config.get("configurable", {})
        grounded = await run_grounded_tool_loop(
            llm, output_llm, toolset, messages, agent_name="fraud",
            event_publisher=configurable.get("event_publisher"), run_id=state.get("run_id"),
            conversation_id=state.get("conversation_id"), customer_id=state.get("customer_id", ""),
        )
        fraud_output = grounded.output

        if fraud_output:
            fraud_evidence = {
                "goal_completed": fraud_output.goal_completed,
                "evidence": grounded.tool_results,
                "findings": fraud_output.findings,
                "assessment_id": find_grounded_value(grounded.tool_results, "assessment_id"),
                "alert_id": find_grounded_value(grounded.tool_results, "alert_id"),
                "risk_score": find_grounded_value(grounded.tool_results, "risk_score"),
                "severity": find_grounded_value(grounded.tool_results, "severity"),
                "requires_case": fraud_output.requires_case,
            }

            update: dict[str, Any] = {
                "fraud_evidence": fraud_evidence,
                "warnings": state.get("warnings", []) + fraud_output.warnings,
            }
            if fraud_evidence["alert_id"]:
                update["active_alert_id"] = fraud_evidence["alert_id"]
            return update

        return {"warnings": state.get("warnings", []) + ["Fraud Agent did not return structured output"]}

    except Exception as e:
        logger.error(f"Fraud Agent execution failed: {e}")
        return {"errors": state.get("errors", []) + [f"Fraud Agent failed: {str(e)}"]}
