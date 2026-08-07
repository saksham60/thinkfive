"""Banking Agent LangGraph node."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig

from app.agents.tool_loop import run_grounded_tool_loop

if TYPE_CHECKING:
    from app.agents.graph.state import GraphState

logger = logging.getLogger(__name__)


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

    try:
        # Invoke agent with tool calling
        configurable = config.get("configurable", {})
        grounded = await run_grounded_tool_loop(
            llm, output_llm, toolset, agent_messages, agent_name="banking",
            event_publisher=configurable.get("event_publisher"), run_id=state.get("run_id"),
            conversation_id=state.get("conversation_id"), customer_id=state.get("customer_id", ""),
        )
        banking_output = grounded.output

        if banking_output:
            # Update state with banking evidence
            banking_evidence = {
                "goal_completed": banking_output.goal_completed,
                "evidence": grounded.tool_results,
                "findings": banking_output.findings,
                "warnings": banking_output.warnings,
            }

            return {
                "banking_evidence": banking_evidence,
                "warnings": state.get("warnings", []) + banking_output.warnings,
            }
        else:
            logger.warning("No structured output from Banking Agent")
            return {
                "warnings": state.get("warnings", []) + ["Banking Agent did not return structured output"]
            }

    except Exception as e:
        logger.error(f"Banking Agent execution failed: {e}")
        return {
            "errors": state.get("errors", []) + [f"Banking Agent failed: {str(e)}"],
        }
