"""LangGraph graph state definition.

A single strongly-typed state shared across all agent nodes. Keeps
structured evidence buckets instead of one giant arbitrary dict.
"""

from __future__ import annotations

from typing import Annotated, Any, TypedDict

from langgraph.graph.message import add_messages


class TransactionReference(TypedDict, total=False):
    """A customer-visible transaction reference grounded in Banking MCP data."""

    position: int
    transaction_id: str
    merchant_name: str | None
    description: str | None
    amount: Any
    currency: str | None
    transaction_date: str | None
    account_id: str | None


class GraphState(TypedDict, total=False):
    """LangGraph state for the ThinkFive multi-agent workflow."""

    # Conversation transcript (LangChain message objects)
    messages: Annotated[list[Any], add_messages]

    # Identity / correlation
    conversation_id: str
    run_id: str
    thread_id: str
    authenticated_user_id: str
    customer_id: str

    # Supervisor routing
    current_goal: str
    primary_user_goal: str
    next_agent: str
    routing_reason: str
    conversation_summary: str | None

    # Evidence buckets (never a giant arbitrary dict)
    banking_evidence: dict[str, Any]
    fraud_evidence: dict[str, Any]
    policy_evidence: dict[str, Any]
    case_evidence: dict[str, Any]

    # Active entity references
    requested_transaction_id: str | None
    active_transaction_id: str | None
    active_transaction: TransactionReference | None
    recent_transaction_candidates: list[TransactionReference]
    active_alert_id: str | None
    active_case_id: str | None
    active_approval_id: str | None

    # HITL
    pending_human_action: dict[str, Any] | None

    # Conversational disambiguation (not an operational HITL approval)
    pending_confirmation: dict[str, Any] | None

    # Memory
    memory_context: dict[str, Any]

    # Control
    iteration_count: int

    # Diagnostics
    warnings: list[str]
    errors: list[str]

    # Final response
    final_response: str | None
