"""Supervisor Agent LangGraph node."""

from __future__ import annotations

import json
import logging
from decimal import Decimal, InvalidOperation
from typing import TYPE_CHECKING, Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langsmith import trace

from app.observability.langsmith import llm_trace_config

if TYPE_CHECKING:
    from app.agents.graph.state import GraphState

logger = logging.getLogger(__name__)

MAX_ITERATIONS_DEFAULT = 15


def _summarize_evidence(state: GraphState) -> str:
    """Build a compact evidence summary string for the supervisor prompt."""
    parts = []
    for key in ("banking_evidence", "fraud_evidence", "policy_evidence", "case_evidence"):
        evidence: dict[str, Any] | None = state.get(key)  # type: ignore[assignment]
        if evidence:
            detail = f"- {key}: {evidence.get('findings', 'present')}"
            if key == "banking_evidence":
                detail += (
                    f"; attempt_status={evidence.get('attempt_status', 'unknown')}"
                    f"; transaction_resolution_status="
                    f"{evidence.get('transaction_resolution_status', 'unknown')}"
                    f"; requires_clarification={evidence.get('requires_clarification', False)}"
                )
            parts.append(detail)
    if not parts:
        memory = state.get("memory_context") or {}
        parts.append("- no live evidence collected yet")
        if memory:
            parts.append(f"- customer_memory (non-authoritative): {memory}")
    memory = state.get("memory_context") or {}
    if memory and "- no live evidence collected yet" not in parts:
        parts.append(f"- customer_memory (non-authoritative): {memory}")
    if state.get("active_transaction_id"):
        parts.append(f"- verified_active_transaction_id: {state['active_transaction_id']}")
    elif state.get("requested_transaction_id"):
        parts.append("- untrusted_requested_transaction_id: present but not validated")
    if state.get("errors"):
        parts.append(f"- errors: {state['errors']}")
    if state.get("warnings"):
        parts.append(f"- warnings: {state['warnings']}")
    return "\n".join(parts)


def _banking_retry_blocked(state: GraphState) -> bool:
    evidence = state.get("banking_evidence") or {}
    current_run_id = state.get("run_id")
    if current_run_id and evidence.get("run_id") != current_run_id:
        return False
    if evidence.get("attempt_status") == "failed":
        return True
    return bool(evidence.get("transaction_lookup_attempted")) and evidence.get(
        "transaction_resolution_status"
    ) in {"unresolved", "ambiguous", "failed"}


def _conversation_context(state: GraphState, limit: int = 8) -> str:
    turns: list[str] = []
    for msg in state.get("messages", [])[-limit:]:
        role = getattr(msg, "type", None) or (
            msg.get("role") if isinstance(msg, dict) else "unknown"
        )
        content = getattr(msg, "content", None) or (
            msg.get("content", "") if isinstance(msg, dict) else ""
        )
        if role in {"human", "user", "ai", "assistant"}:
            turns.append(f"{role}: {content}")
    return "\n".join(turns) or "(no conversation turns)"


def _candidate_at(state: GraphState, position: int | None) -> Any:
    if position is None:
        return None
    return next(
        (
            candidate
            for candidate in state.get("recent_transaction_candidates", [])
            if candidate.get("position") == position
        ),
        None,
    )


def _matching_candidates(
    state: GraphState,
    merchant: str | None,
    amount: float | None,
    transaction_date: str | None,
) -> list[Any]:
    """Filter grounded candidates using only attributes extracted by the Supervisor."""
    matches: list[Any] = []
    expected_merchant = merchant.strip().casefold() if merchant else None
    expected_amount = Decimal(str(amount)) if amount is not None else None
    for candidate in state.get("recent_transaction_candidates", []):
        if expected_merchant:
            text = " ".join(
                str(candidate.get(key) or "") for key in ("merchant_name", "description")
            ).casefold()
            if expected_merchant not in text:
                continue
        if expected_amount is not None:
            try:
                if Decimal(str(candidate.get("amount"))) != expected_amount:
                    continue
            except (InvalidOperation, TypeError, ValueError):
                continue
        if transaction_date and str(candidate.get("transaction_date")) != transaction_date:
            continue
        matches.append(candidate)
    return matches


async def supervisor_node(state: GraphState, config: RunnableConfig) -> dict[str, Any]:
    """Supervisor node - decides routing via structured LLM output only."""
    logger.info("Supervisor Agent node executing")

    supervisor_agent = config.get("configurable", {}).get("supervisor_agent")
    if not supervisor_agent:
        raise ValueError("Supervisor Agent not configured")

    iteration_count = state.get("iteration_count", 0) + 1
    max_iterations = config.get("configurable", {}).get("max_iterations", MAX_ITERATIONS_DEFAULT)

    # Force synthesis if max iterations reached (bounded graph execution)
    if iteration_count >= max_iterations:
        logger.warning(f"Max iterations ({max_iterations}) reached, forcing synthesis")
        return {
            "next_agent": "synthesis",
            "iteration_count": iteration_count,
            "warnings": state.get("warnings", []) + ["Max iterations reached - forcing synthesis"],
        }

    evidence_summary = _summarize_evidence(state)
    agent_config = supervisor_agent.create_agent(evidence_summary, iteration_count, max_iterations)
    llm = agent_config["llm"]
    prompt = agent_config["prompt"]

    messages = state.get("messages", [])
    latest_user_message = ""
    for msg in reversed(messages):
        role = getattr(msg, "type", None) or (msg.get("role") if isinstance(msg, dict) else None)
        if role in ("human", "user"):
            latest_user_message = getattr(msg, "content", None) or msg.get("content", "")
            break

    candidates = state.get("recent_transaction_candidates", [])
    reference_state = {
        "verified_active_transaction": state.get("active_transaction"),
        "recent_transaction_candidates": candidates,
        "pending_confirmation": state.get("pending_confirmation"),
        "conversation_summary": state.get("conversation_summary"),
        "primary_user_goal": state.get("primary_user_goal"),
    }
    prompt_messages = [
        SystemMessage(content=prompt),
        HumanMessage(
            content=(
                f"Bounded conversation:\n{_conversation_context(state)}\n\n"
                f"Latest customer message: {latest_user_message}\n\n"
                f"Structured reference state:\n{json.dumps(reference_state, default=str)}\n\n"
                "Decide the next routing step and resolve only the semantic reference shape."
            )
        ),
    ]

    try:
        conversation_turn = sum(
            1 for message in messages if getattr(message, "type", None) == "human"
        )
        safe_trace_metadata = {
            "conversation_turn": conversation_turn,
            "active_transaction_present": bool(state.get("active_transaction_id")),
            "recent_transaction_candidate_count": len(candidates),
            "pending_confirmation_type": (state.get("pending_confirmation") or {}).get("type"),
        }
        with trace(
            "agent.supervisor",
            run_type="chain",
            inputs=safe_trace_metadata,
            tags=["thinkfive", "agent", "agent:supervisor"],
            metadata=safe_trace_metadata,
        ) as supervisor_span:
            decision = await llm.ainvoke(
                prompt_messages,
                config=llm_trace_config("supervisor", "routing", agent_config.get("version")),
            )
            supervisor_span.end(
                outputs={
                    "next_agent": decision.next_agent,
                    "needs_clarification": decision.needs_clarification,
                    "reference_type": decision.reference_type,
                }
            )

        next_agent = decision.next_agent
        pending_confirmation = state.get("pending_confirmation")
        if decision.clear_pending_confirmation:
            pending_confirmation = None
        requested_transaction_id = state.get("requested_transaction_id")
        selected_candidate: Any = None

        if decision.reference_type == "ordinal":
            selected_candidate = _candidate_at(state, decision.candidate_position)
            if selected_candidate is None:
                next_agent = "synthesis"
                pending_confirmation = {
                    "type": "transaction_details",
                    "candidate": None,
                    "question": (
                        decision.clarification_question
                        or "That number is not in the displayed transaction list. Which transaction did you mean?"
                    ),
                }
        elif decision.reference_type == "merchant_amount":
            matches = _matching_candidates(
                state,
                decision.reference_merchant,
                decision.reference_amount,
                decision.reference_date,
            )
            if len(matches) == 1:
                selected_candidate = matches[0]
                next_agent = "banking"
            elif len(matches) > 1:
                next_agent = "synthesis"
                pending_confirmation = {
                    "type": "transaction_selection",
                    "candidate": None,
                    "candidates": matches,
                    "question": decision.clarification_question,
                }
        elif decision.reference_type == "pending_confirmation":
            pending_candidate = (pending_confirmation or {}).get("candidate")
            if decision.confirmation == "accept" and isinstance(pending_candidate, dict):
                selected_candidate = pending_candidate
                pending_confirmation = None
            elif decision.confirmation == "reject":
                pending_confirmation = None

        requires_confirmation = bool(
            decision.needs_clarification
            and selected_candidate
            and decision.reference_type != "merchant_amount"
        )
        if requires_confirmation:
            pending_confirmation = {
                "type": "transaction_selection",
                "candidate": selected_candidate,
                "question": decision.clarification_question,
            }
            next_agent = "synthesis"
        elif selected_candidate and selected_candidate.get("transaction_id"):
            requested_transaction_id = str(selected_candidate["transaction_id"])

        routing_reason = decision.reason
        warnings = state.get("warnings", [])
        current_goal = decision.goal
        if decision.reference_type == "merchant_amount":
            constraints = {
                "merchant_or_description": decision.reference_merchant,
                "amount": decision.reference_amount,
                "date": decision.reference_date,
            }
            current_goal = (
                f"{current_goal}\nUse these customer-provided search constraints: "
                f"{json.dumps(constraints)}"
            )

        new_reference_evidence = bool(
            selected_candidate
            or decision.reference_type in {"merchant_amount", "active_transaction"}
        )
        resolution_status = (
            "resolved"
            if selected_candidate or decision.reference_type == "active_transaction"
            else (
                "ambiguous"
                if (pending_confirmation or {}).get("type") == "transaction_selection"
                else "unresolved"
            )
        )
        with trace(
            "reference.resolve",
            run_type="chain",
            inputs={
                "reference_type": decision.reference_type,
                "candidate_count": len(candidates),
            },
            tags=["thinkfive", "reference-resolution"],
            metadata={
                "reference_type": decision.reference_type,
                "candidate_count": len(candidates),
                "resolution_status": resolution_status,
            },
        ) as reference_span:
            reference_span.end(outputs={"resolution_status": resolution_status})
        if next_agent == "banking" and _banking_retry_blocked(state) and not new_reference_evidence:
            banking_evidence = state.get("banking_evidence") or {}
            question = banking_evidence.get("clarification_question") or (
                "Please provide more transaction details, such as the merchant, amount, or date."
            )
            next_agent = "synthesis"
            pending_confirmation = {
                "type": "transaction_details",
                "candidate": None,
                "question": question,
            }
            routing_reason = (
                "Banking already attempted this lookup without resolving a verified transaction; "
                "the same route will not be repeated without new customer evidence."
            )
            warnings = [*warnings, "Repeated unresolved Banking route prevented"]

        return {
            "next_agent": next_agent,
            "current_goal": current_goal,
            "primary_user_goal": (
                state.get("primary_user_goal")
                or decision.primary_user_goal
                or decision.goal
            ),
            "routing_reason": routing_reason,
            "iteration_count": iteration_count,
            "requested_transaction_id": requested_transaction_id,
            "pending_confirmation": pending_confirmation,
            "warnings": warnings,
        }

    except Exception as e:
        logger.error(f"Supervisor Agent execution failed: {e}")
        return {
            "next_agent": "synthesis",
            "iteration_count": iteration_count,
            "errors": state.get("errors", []) + [f"Supervisor failed: {str(e)}"],
        }
