"""Case Agent LangGraph node."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig

from app.agents.tool_loop import find_grounded_value, run_grounded_tool_loop

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
    output_llm = agent_config["output_llm"]
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
        configurable = config.get("configurable", {})
        grounded = await run_grounded_tool_loop(
            llm, output_llm, toolset, messages, agent_name="case",
            event_publisher=configurable.get("event_publisher"), run_id=state.get("run_id"),
            conversation_id=state.get("conversation_id"), customer_id=state.get("customer_id", ""),
        )
        case_output = grounded.output

        if case_output:
            case_evidence = {
                "goal_completed": case_output.goal_completed,
                "evidence": grounded.tool_results,
                "findings": case_output.findings,
                "case_id": find_grounded_value(grounded.tool_results, "case_id"),
                "approval_id": find_grounded_value(grounded.tool_results, "approval_id"),
            }

            update: dict[str, Any] = {
                "case_evidence": case_evidence,
                "warnings": state.get("warnings", []) + case_output.warnings,
            }
            if case_evidence["case_id"]:
                update["active_case_id"] = case_evidence["case_id"]
            if case_evidence["approval_id"]:
                update["active_approval_id"] = case_evidence["approval_id"]
                # Signal that a human decision is now required - graph will interrupt.
                update["pending_human_action"] = {
                    "type": "approval",
                    "approval_id": case_evidence["approval_id"],
                    "case_id": case_evidence["case_id"],
                }
            return update

        return {"warnings": state.get("warnings", []) + ["Case Agent did not return structured output"]}

    except Exception as e:
        logger.error(f"Case Agent execution failed: {e}")
        return {"errors": state.get("errors", []) + [f"Case Agent failed: {str(e)}"]}
