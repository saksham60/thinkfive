"""Banking Agent LangGraph node."""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig

from app.agents.tool_loop import run_grounded_tool_loop

if TYPE_CHECKING:
    from app.agents.graph.state import GraphState

logger = logging.getLogger(__name__)

_TRANSACTION_TOOLS = frozenset({"get_transaction", "get_recent_transactions", "search_transactions"})


def _transaction_ids(value: Any) -> set[str]:
    """Collect transaction IDs only from structured Banking MCP values."""
    found: set[str] = set()
    if isinstance(value, dict):
        transaction_id = value.get("transaction_id")
        if transaction_id:
            found.add(str(transaction_id))
        for child in value.values():
            found.update(_transaction_ids(child))
    elif isinstance(value, list):
        for child in value:
            found.update(_transaction_ids(child))
    return found


def find_grounded_transaction_id(
    tool_results: list[dict[str, Any]],
    requested_transaction_id: str | None = None,
) -> str | None:
    """Resolve one transaction ID from structured Banking MCP tool results.

    A client reference is accepted only from an exact ``get_transaction``
    validation result. Without a client reference, only a tool result containing
    one transaction is specific enough to promote; multi-result collections are
    never resolved through model prose.
    """
    if requested_transaction_id:
        for result in tool_results:
            if result.get("tool") != "get_transaction":
                continue
            arguments = result.get("arguments") or {}
            if arguments.get("transaction_id") != requested_transaction_id:
                continue
            if _transaction_ids(result.get("data")) == {requested_transaction_id}:
                return requested_transaction_id
        return None

    candidates: set[str] = set()
    for result in tool_results:
        if result.get("tool") not in _TRANSACTION_TOOLS:
            continue
        result_ids = _transaction_ids(result.get("data"))
        if len(result_ids) == 1:
            candidates.update(result_ids)
    return next(iter(candidates)) if len(candidates) == 1 else None


def _transaction_resolution_status(
    tool_results: list[dict[str, Any]], resolved_transaction_id: str | None
) -> str:
    if resolved_transaction_id:
        return "resolved"
    transaction_results = [item for item in tool_results if item.get("tool") in _TRANSACTION_TOOLS]
    if not transaction_results:
        return "not_attempted"
    candidate_ids: set[str] = set()
    for result in transaction_results:
        candidate_ids.update(_transaction_ids(result.get("data")))
    return "ambiguous" if len(candidate_ids) > 1 else "unresolved"


async def banking_node(state: GraphState, config: RunnableConfig) -> dict[str, Any]:
    """Banking Agent node - retrieves banking data.

    This node:
    1. Extracts current goal from state
    2. Builds message history
    3. Invokes Banking Agent
    4. Executes any tool calls
    5. Updates state with banking evidence
    """
    logger.info("Banking Agent node executing")

    # Extract from state
    current_goal = state.get("current_goal", "")
    messages = state.get("messages", [])
    requested_transaction_id = state.get("requested_transaction_id")

    # Get Banking Agent from config
    banking_agent = config.get("configurable", {}).get("banking_agent")
    if not banking_agent:
        raise ValueError("Banking Agent not configured")

    agent_config = banking_agent.create_agent()
    llm = agent_config["llm"]
    output_llm = agent_config["output_llm"]
    prompt = agent_config["prompt"]
    toolset = agent_config["toolset"]

    # Build message history
    agent_messages: list[BaseMessage] = [SystemMessage(content=prompt)]

    # Add conversation context
    if messages:
        agent_messages.extend(msg for msg in messages[-5:] if isinstance(msg, BaseMessage))

    # Add current goal
    agent_messages.append(
        HumanMessage(content=f"Goal: {current_goal}\n\nPlease retrieve the necessary banking data.")
    )

    validation_results: list[dict[str, Any]] = []
    validated_transaction_id: str | None = None
    if requested_transaction_id:
        try:
            validated_transaction = await toolset.execute_tool(
                "get_transaction", {"transaction_id": requested_transaction_id}
            )
            validation_results.append(
                {
                    "tool": "get_transaction",
                    "arguments": {"transaction_id": requested_transaction_id},
                    "data": validated_transaction,
                }
            )
            validated_transaction_id = find_grounded_transaction_id(
                validation_results, requested_transaction_id
            )
        except Exception as exc:
            logger.info("Banking MCP rejected requested transaction reference: %s", exc)

        if validated_transaction_id is None:
            warning = "The requested transaction was not validated for this customer by Banking MCP."
            return {
                "banking_evidence": {
                    "goal_completed": False,
                    "evidence": validation_results,
                    "findings": warning,
                    "warnings": [warning],
                    "attempt_status": "completed",
                    "transaction_lookup_attempted": True,
                    "transaction_resolution_status": "unresolved",
                    "resolved_transaction_id": None,
                    "requires_clarification": True,
                    "clarification_question": (
                        "Please select a transaction that is visible in your current transaction history."
                    ),
                },
                "warnings": state.get("warnings", []) + [warning],
            }

        agent_messages.append(
            HumanMessage(
                content=(
                    "The client supplied an untrusted transaction reference. Banking MCP has now "
                    "validated the exact transaction for this customer. Use this structured result "
                    f"as the transaction context: {json.dumps(validation_results[0]['data'], default=str)}"
                )
            )
        )

    try:
        # Invoke agent with tool calling
        configurable = config.get("configurable", {})
        grounded = await run_grounded_tool_loop(
            llm, output_llm, toolset, agent_messages, agent_name="banking",
            event_publisher=configurable.get("event_publisher"), run_id=state.get("run_id"),
            conversation_id=state.get("conversation_id"), customer_id=state.get("customer_id", ""),
            prompt_version=agent_config.get("version"),
        )
        banking_output = grounded.output
        tool_results = [*validation_results, *grounded.tool_results]
        resolved_transaction_id = find_grounded_transaction_id(
            tool_results, requested_transaction_id
        )
        resolution_status = _transaction_resolution_status(tool_results, resolved_transaction_id)

        if banking_output:
            # Update state with banking evidence
            banking_evidence = {
                "goal_completed": banking_output.goal_completed,
                "evidence": tool_results,
                "findings": banking_output.findings,
                "warnings": banking_output.warnings,
                "attempt_status": "completed",
                "transaction_lookup_attempted": resolution_status != "not_attempted",
                "transaction_resolution_status": resolution_status,
                "resolved_transaction_id": resolved_transaction_id,
                "requires_clarification": banking_output.requires_clarification,
                "clarification_question": banking_output.clarification_question,
            }

            update: dict[str, Any] = {
                "banking_evidence": banking_evidence,
                "warnings": state.get("warnings", []) + banking_output.warnings,
            }
            if resolved_transaction_id:
                update["active_transaction_id"] = resolved_transaction_id
            return update
        else:
            logger.warning("No structured output from Banking Agent")
            update = {
                "banking_evidence": {
                    "goal_completed": False,
                    "evidence": tool_results,
                    "findings": "Banking Agent did not return structured output.",
                    "warnings": ["Banking Agent did not return structured output"],
                    "attempt_status": "failed",
                    "transaction_lookup_attempted": bool(requested_transaction_id),
                    "transaction_resolution_status": (
                        "resolved" if validated_transaction_id else "failed"
                    ),
                    "resolved_transaction_id": validated_transaction_id,
                },
                "warnings": state.get("warnings", []) + ["Banking Agent did not return structured output"]
            }
            if validated_transaction_id:
                update["active_transaction_id"] = validated_transaction_id
            return update

    except Exception as e:
        logger.error(f"Banking Agent execution failed: {e}")
        failure = f"Banking Agent failed: {str(e)}"
        update = {
            "banking_evidence": {
                "goal_completed": False,
                "evidence": validation_results,
                "findings": failure,
                "warnings": [failure],
                "attempt_status": "failed",
                "transaction_lookup_attempted": bool(requested_transaction_id),
                "transaction_resolution_status": (
                    "resolved" if validated_transaction_id else "failed"
                ),
                "resolved_transaction_id": validated_transaction_id,
            },
            "errors": state.get("errors", []) + [f"Banking Agent failed: {str(e)}"],
        }
        if validated_transaction_id:
            update["active_transaction_id"] = validated_transaction_id
        return update
