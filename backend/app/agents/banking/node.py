"""Banking Agent LangGraph node."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig

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
    prompt = agent_config["prompt"]
    toolset = agent_config["toolset"]

    # Build message history
    agent_messages: list[BaseMessage] = [SystemMessage(content=prompt)]

    # Add conversation context
    if messages:
        for msg in messages[-5:]:  # Last 5 messages for context
            if msg["role"] == "user":
                agent_messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                agent_messages.append(AIMessage(content=msg["content"]))

    # Add current goal
    agent_messages.append(
        HumanMessage(content=f"Goal: {current_goal}\n\nPlease retrieve the necessary banking data.")
    )

    try:
        # Invoke agent with tool calling
        response = await llm.ainvoke(agent_messages)

        # Handle tool calls if present
        if hasattr(response, "tool_calls") and response.tool_calls:
            for tool_call in response.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]

                logger.info(f"Executing tool: {tool_name}")
                await toolset.execute_tool(tool_name, tool_args)
                # Tool results are fed back on the next supervisor iteration via evidence state.

        # Extract structured output
        banking_output = response if hasattr(response, "goal_completed") else None

        if banking_output:
            # Update state with banking evidence
            banking_evidence = {
                "goal_completed": banking_output.goal_completed,
                "evidence": [e.model_dump() for e in banking_output.evidence],
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
