"""Case Agent LangGraph node."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig

if TYPE_CHECKING:
    from app.agents.graph.state import GraphState

logger = logging.getLogger(__name__)


async def case_node(state: GraphState, config: RunnableConfig) -> dict[str, Any]:
    """Case Agent node - case management + approval requests only (never approvals)."""
    logger.info("Case Agent node executing")

    current_goal = state.get("current_goal", "")
    case_agent = config.get("configurable", {}).get("case_agent")
    if not case_agent:
        raise ValueError("Case Agent not configured")

    agent_config = case_agent.create_agent()
    llm = agent_config["llm"]
    prompt = agent_config["prompt"]
    toolset = agent_config["toolset"]

    fraud_evidence = state.get("fraud_evidence", {})
    context_note = ""
    if fraud_evidence:
        context_note = f"\nFraud evidence: {fraud_evidence.get('findings', '')}"

    messages = [
        SystemMessage(content=prompt),
        HumanMessage(content=f"Goal: {current_goal}{context_note}"),
    ]

    try:
        response = await llm.ainvoke(messages)

        if hasattr(response, "tool_calls") and response.tool_calls:
            for tool_call in response.tool_calls:
                await toolset.execute_tool(tool_call["name"], tool_call["args"])

        case_output = response if hasattr(response, "goal_completed") else None

        if case_output:
            case_evidence = {
                "goal_completed": case_output.goal_completed,
                "evidence": [e.model_dump() for e in case_output.evidence],
                "findings": case_output.findings,
                "case_id": case_output.case_id,
                "approval_id": case_output.approval_id,
            }

            update: dict[str, Any] = {
                "case_evidence": case_evidence,
                "warnings": state.get("warnings", []) + case_output.warnings,
            }
            if case_output.case_id:
                update["active_case_id"] = case_output.case_id
            if case_output.approval_id:
                update["active_approval_id"] = case_output.approval_id
                # Signal that a human decision is now required - graph will interrupt.
                update["pending_human_action"] = {
                    "type": "approval",
                    "approval_id": case_output.approval_id,
                    "case_id": case_output.case_id,
                }
            return update

        return {"warnings": state.get("warnings", []) + ["Case Agent did not return structured output"]}

    except Exception as e:
        logger.error(f"Case Agent execution failed: {e}")
        return {"errors": state.get("errors", []) + [f"Case Agent failed: {str(e)}"]}
