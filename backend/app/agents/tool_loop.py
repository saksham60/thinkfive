"""Small bounded LangChain tool loop shared by MCP-backed specialists."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from langchain_core.messages import BaseMessage, ToolMessage

from app.core.constants import EventType


@dataclass
class GroundedAgentResult:
    output: Any
    tool_results: list[dict[str, Any]]


async def run_grounded_tool_loop(
    tool_llm: Any,
    output_llm: Any,
    toolset: Any,
    messages: list[BaseMessage],
    *,
    max_rounds: int = 4,
    agent_name: str | None = None,
    event_publisher: Any = None,
    run_id: str | None = None,
    conversation_id: str | None = None,
    customer_id: str = "",
) -> GroundedAgentResult:
    """Execute tool calls, return their data to the model, then request structured output."""
    loop_started = time.perf_counter()
    transcript = list(messages)
    evidence: list[dict[str, Any]] = []
    if event_publisher and run_id and conversation_id:
        await event_publisher.publish(
            UUID(conversation_id), EventType.AGENT_STARTED,
            {"run_id": run_id, "conversation_id": conversation_id,
             "customer_id": customer_id, "agent": agent_name},
            run_id=UUID(run_id), customer_id=customer_id, agent_name=agent_name, status="started",
        )
    for _ in range(max_rounds):
        response = await tool_llm.ainvoke(transcript)
        transcript.append(response)
        tool_calls = getattr(response, "tool_calls", None) or []
        if not tool_calls:
            break
        for call in tool_calls:
            name = call["name"]
            started = time.perf_counter()
            if event_publisher and run_id and conversation_id:
                await event_publisher.publish(
                    UUID(conversation_id), EventType.AGENT_TOOL_STARTED,
                    {"run_id": run_id, "conversation_id": conversation_id,
                     "customer_id": customer_id, "agent": agent_name, "tool": name},
                    run_id=UUID(run_id), customer_id=customer_id,
                    agent_name=agent_name, tool_name=name, status="started",
                )
            try:
                result = await toolset.execute_tool(name, call.get("args") or {})
            except Exception as exc:
                duration_ms = (time.perf_counter() - started) * 1000
                if event_publisher and run_id and conversation_id:
                    await event_publisher.publish(
                        UUID(conversation_id), EventType.AGENT_TOOL_FAILED,
                        {"run_id": run_id, "conversation_id": conversation_id,
                         "customer_id": customer_id, "agent": agent_name, "tool": name,
                         "duration_ms": duration_ms, "error_code": getattr(exc, "code", type(exc).__name__)},
                        run_id=UUID(run_id), customer_id=customer_id, agent_name=agent_name,
                        tool_name=name, status="failed", duration_ms=duration_ms,
                    )
                raise
            duration_ms = (time.perf_counter() - started) * 1000
            if event_publisher and run_id and conversation_id:
                await event_publisher.publish(
                    UUID(conversation_id), EventType.AGENT_TOOL_COMPLETED,
                    {"run_id": run_id, "conversation_id": conversation_id,
                     "customer_id": customer_id, "agent": agent_name, "tool": name,
                     "duration_ms": duration_ms},
                    run_id=UUID(run_id), customer_id=customer_id, agent_name=agent_name,
                    tool_name=name, status="completed", duration_ms=duration_ms,
                )
                domain_event = {
                    "create_fraud_alert": EventType.FRAUD_ALERT_CREATED,
                    "create_case": EventType.CASE_CREATED,
                    "create_case_from_fraud_alert": EventType.CASE_CREATED,
                }.get(name)
                if domain_event:
                    await event_publisher.publish(
                        UUID(conversation_id), domain_event,
                        {"run_id": run_id, "conversation_id": conversation_id,
                         "customer_id": customer_id,
                         "alert_id": find_grounded_value([{"data": result}], "alert_id"),
                         "case_id": find_grounded_value([{"data": result}], "case_id")},
                        run_id=UUID(run_id), customer_id=customer_id,
                        agent_name=agent_name, tool_name=name, status="completed",
                    )
            evidence.append({"tool": name, "data": result})
            transcript.append(
                ToolMessage(
                    content=json.dumps(result, default=str),
                    tool_call_id=call.get("id") or name,
                    name=name,
                )
            )
    else:
        raise RuntimeError(f"Agent exceeded maximum tool rounds ({max_rounds})")

    output = await output_llm.ainvoke(transcript)
    if event_publisher and run_id and conversation_id:
        duration_ms = (time.perf_counter() - loop_started) * 1000
        await event_publisher.publish(
            UUID(conversation_id), EventType.AGENT_COMPLETED,
            {"run_id": run_id, "conversation_id": conversation_id,
             "customer_id": customer_id, "agent": agent_name, "duration_ms": duration_ms},
            run_id=UUID(run_id), customer_id=customer_id, agent_name=agent_name,
            status="completed", duration_ms=duration_ms,
        )
    return GroundedAgentResult(output=output, tool_results=evidence)


def find_grounded_value(tool_results: list[dict[str, Any]], key: str) -> Any:
    """Find a returned business identifier/value without trusting model-generated fields."""
    def visit(value: Any) -> Any:
        if isinstance(value, dict):
            if key in value and value[key] is not None:
                return value[key]
            for child in value.values():
                found = visit(child)
                if found is not None:
                    return found
        elif isinstance(value, list):
            for child in value:
                found = visit(child)
                if found is not None:
                    return found
        return None

    return visit(tool_results)
