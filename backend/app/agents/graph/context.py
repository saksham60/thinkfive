"""Shared agent runtime context (composition, not inheritance)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class AgentRuntimeContext:
    """Runtime dependencies shared across all agent nodes.

    Composed into the LangGraph ``config["configurable"]`` dict so each
    node can access agents, adapters, and services without global state.
    """

    customer_id: str
    supervisor_agent: Any = None
    banking_agent: Any = None
    fraud_agent: Any = None
    knowledge_agent: Any = None
    case_agent: Any = None
    synthesis_agent: Any = None
    memory_service: Any = None
    hitl_service: Any = None
    event_publisher: Any = None


@dataclass
class ToolExecutionContext:
    """Context passed to a toolset when executing a tool call."""

    customer_id: str
    run_id: str
    conversation_id: str
    correlation_id: str


@dataclass
class AgentResult:
    """Uniform result wrapper returned by agent node executions."""

    success: bool
    state_update: dict[str, Any]
    error: str | None = None
