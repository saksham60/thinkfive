"""LangGraph conditional routing logic."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.agents.graph.state import GraphState


def route_from_supervisor(state: GraphState) -> str:
    """Route from supervisor to the agent it selected."""
    pending = state.get("pending_human_action") or {}
    if pending.get("type") == "clarification":
        return "synthesis"
    next_agent = state.get("next_agent", "synthesis")
    if next_agent not in ("banking", "fraud", "knowledge", "case", "synthesis"):
        return "synthesis"
    return next_agent


def route_after_specialist(state: GraphState) -> str:
    """After a specialist agent runs, decide whether to interrupt for HITL or go back to supervisor."""
    pending = state.get("pending_human_action") or {}
    if pending.get("type") == "approval":
        return "hitl_interrupt"
    return "supervisor"
