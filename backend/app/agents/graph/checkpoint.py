"""HITL interrupt node - pauses the graph pending a human decision."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from langchain_core.runnables import RunnableConfig
from langgraph.types import interrupt

if TYPE_CHECKING:
    from app.agents.graph.state import GraphState

logger = logging.getLogger(__name__)


async def hitl_interrupt_node(state: GraphState, config: RunnableConfig) -> dict[str, Any]:
    """Interrupt graph execution, persisting the checkpoint, until a human resumes it.

    Uses LangGraph's ``interrupt()`` so the checkpointer persists state and the
    process can be killed/restarted while waiting. Resume is provided via
    ``Command(resume=...)`` with the human decision payload.
    """
    pending = state.get("pending_human_action") or {}
    logger.info(f"Graph interrupting for human approval: {pending}")

    # This call raises a GraphInterrupt under the hood; LangGraph persists the
    # checkpoint and the invoking runner sees status=WAITING/interrupted.
    decision = interrupt(
        {
            "type": "approval_required",
            "approval_id": pending.get("approval_id"),
            "case_id": pending.get("case_id"),
        }
    )

    # Execution resumes here after Command(resume=decision) is supplied.
    return {
        "pending_human_action": None,
        "case_evidence": {
            **(state.get("case_evidence") or {}),
            "human_decision": decision,
        },
    }
