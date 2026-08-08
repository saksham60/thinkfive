"""Small bounded LangChain tool loop shared by MCP-backed specialists."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from langchain_core.messages import BaseMessage, HumanMessage, ToolMessage
from langsmith import trace

from app.core.constants import EventType
from app.observability.langsmith import llm_trace_config, trace_messages, trace_value


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
    prompt_version: str | None = None,
) -> GroundedAgentResult:
    """Execute tool calls, return their data to the model, then request structured output."""
    traced_agent_name = agent_name or "specialist"
    with trace(
        f"agent.{traced_agent_name}",
        run_type="chain",
        inputs={"messages": trace_messages(messages)},
        tags=["thinkfive", "agent", f"agent:{traced_agent_name}"],
        metadata={"agent": traced_agent_name, "prompt_version": prompt_version},
    ) as agent_span:
        result = await _execute_grounded_tool_loop(
            tool_llm,
            output_llm,
            toolset,
            messages,
            max_rounds=max_rounds,
            agent_name=agent_name,
            event_publisher=event_publisher,
            run_id=run_id,
            conversation_id=conversation_id,
            customer_id=customer_id,
            prompt_version=prompt_version,
        )
        agent_span.end(
            outputs={
                "structured_output": trace_value(result.output),
                "tools_fired": [item["tool"] for item in result.tool_results],
                "tool_results": trace_value(result.tool_results),
            }
        )
        return result


async def _execute_grounded_tool_loop(
    tool_llm: Any,
    output_llm: Any,
    toolset: Any,
    messages: list[BaseMessage],
    *,
    max_rounds: int,
    agent_name: str | None,
    event_publisher: Any,
    run_id: str | None,
    conversation_id: str | None,
    customer_id: str,
    prompt_version: str | None,
) -> GroundedAgentResult:
    """Internal implementation kept below the named agent trace span."""
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
        response = await tool_llm.ainvoke(
            transcript,
            config=llm_trace_config(agent_name or "specialist", "tool_selection", prompt_version),
        )
        transcript.append(response)
        tool_calls = getattr(response, "tool_calls", None) or []
        if not tool_calls:
            break
        halt_after_tool_failure = False
        for call in tool_calls:
            name = call["name"]
            arguments = call.get("args") or {}
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
                with trace(
                    f"tool.{name}",
                    run_type="tool",
                    inputs={"arguments": trace_value(arguments)},
                    tags=["thinkfive", "mcp-tool", f"agent:{agent_name or 'specialist'}", f"tool:{name}"],
                    metadata={"agent": agent_name or "specialist", "tool": name, "transport": "mcp"},
                ) as tool_span:
                    result = await toolset.execute_tool(name, arguments)
                    tool_span.end(outputs={"result": trace_value(result)})
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
                # A specialist can already have useful grounded evidence when a later,
                # optional action fails (for example: risk assessment succeeds but an
                # alert is rejected by its threshold or uniqueness policy). Preserve
                # that evidence and let the structured output summarize the partial
                # result instead of throwing it away and restarting the whole agent.
                error_code = getattr(exc, "code", type(exc).__name__)
                safe_error = {
                    "success": False,
                    "error_code": str(error_code),
                    "message": (
                        "Tool execution failed. Preserve completed grounded evidence "
                        "and do not claim this action succeeded."
                    ),
                }
                evidence.append({"tool": name, "arguments": arguments, "error": safe_error})
                transcript.append(
                    ToolMessage(
                        content=json.dumps(safe_error),
                        tool_call_id=call.get("id") or name,
                        name=name,
                    )
                )
                halt_after_tool_failure = True
                continue
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
            evidence.append({"tool": name, "arguments": arguments, "data": result})
            transcript.append(
                ToolMessage(
                    content=json.dumps(result, default=str),
                    tool_call_id=call.get("id") or name,
                    name=name,
                )
            )
        if halt_after_tool_failure:
            break
    else:
        raise RuntimeError(f"Agent exceeded maximum tool rounds ({max_rounds})")

    # A completed tool-selection round can end with an assistant/model turn.
    # Gemini rejects a new generation from a transcript that ends that way, so
    # add an explicit, provider-neutral finalization turn for the schema-bound
    # output model. This also makes the two-stage intent unambiguous.
    output_transcript = [
        *transcript,
        HumanMessage(content="Using the evidence above, return the required structured output."),
    ]
    output = await output_llm.ainvoke(
        output_transcript,
        config=llm_trace_config(agent_name or "specialist", "structured_output", prompt_version),
    )
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
