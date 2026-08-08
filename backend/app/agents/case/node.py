"""Case Agent LangGraph node."""

from __future__ import annotations

import json
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
    case_context = {
        "primary_user_goal": state.get("primary_user_goal"),
        "customer_requested_formal_case": state.get(
            "customer_requested_formal_case", False
        ),
        "verified_transaction_id": state.get("active_transaction_id"),
        "assessment_id": fraud_evidence.get("assessment_id"),
        "fraud_alert_id": fraud_evidence.get("alert_id"),
        "risk_score": fraud_evidence.get("risk_score"),
        "severity": fraud_evidence.get("severity"),
        "fraud_findings": fraud_evidence.get("findings"),
    }

    messages = [
        SystemMessage(content=prompt),
        HumanMessage(
            content=(
                f"Goal: {current_goal}\n\n"
                f"Grounded workflow context: {json.dumps(case_context, default=str)}"
            )
        ),
    ]

    try:
        configurable = config.get("configurable", {})
        grounded = await run_grounded_tool_loop(
            llm, output_llm, toolset, messages, agent_name="case",
            event_publisher=configurable.get("event_publisher"), run_id=state.get("run_id"),
            conversation_id=state.get("conversation_id"), customer_id=state.get("customer_id", ""),
            prompt_version=agent_config.get("version"),
        )
        case_output = grounded.output

        if case_output:
            case_evidence = {
                "goal_completed": case_output.goal_completed,
                "evidence": grounded.tool_results,
                "findings": case_output.findings,
                "case_id": find_grounded_value(grounded.tool_results, "case_id"),
                "approval_id": find_grounded_value(grounded.tool_results, "approval_id"),
                "transaction_id": find_grounded_value(
                    grounded.tool_results, "transaction_id"
                ),
                "assessment_id": find_grounded_value(
                    grounded.tool_results, "assessment_id"
                ),
                "fraud_alert_id": find_grounded_value(
                    grounded.tool_results, "fraud_alert_id"
                ),
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
