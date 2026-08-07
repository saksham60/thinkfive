"""Fraud Agent LangGraph node."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig

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
    prompt = agent_config["prompt"]
    toolset = agent_config["toolset"]

    messages = [
        SystemMessage(content=prompt),
        HumanMessage(content=f"Goal: {current_goal}\n\nAssess fraud risk using available evidence."),
    ]

    try:
        response = await llm.ainvoke(messages)

        if hasattr(response, "tool_calls") and response.tool_calls:
            for tool_call in response.tool_calls:
                await toolset.execute_tool(tool_call["name"], tool_call["args"])

        fraud_output = response if hasattr(response, "goal_completed") else None

        if fraud_output:
            fraud_evidence = {
                "goal_completed": fraud_output.goal_completed,
                "evidence": [e.model_dump() for e in fraud_output.evidence],
                "findings": fraud_output.findings,
                "assessment_id": fraud_output.assessment_id,
                "alert_id": fraud_output.alert_id,
                "risk_score": fraud_output.risk_score,
                "severity": fraud_output.severity,
                "requires_case": fraud_output.requires_case,
            }

            update: dict[str, Any] = {
                "fraud_evidence": fraud_evidence,
                "warnings": state.get("warnings", []) + fraud_output.warnings,
            }
            if fraud_output.alert_id:
                update["active_alert_id"] = fraud_output.alert_id
            return update

        return {"warnings": state.get("warnings", []) + ["Fraud Agent did not return structured output"]}

    except Exception as e:
        logger.error(f"Fraud Agent execution failed: {e}")
        return {"errors": state.get("errors", []) + [f"Fraud Agent failed: {str(e)}"]}
