from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from case.app.container import Container

from .common import response


def register(m: FastMCP, c: Container) -> None:
    @m.tool(description="Add a bounded, attributed note to an existing case for investigation, communication, approval or resolution context.")
    async def add_case_note(case_id: str, content: str, note_type: str = "GENERAL", author_type: str = "AGENT", author_id: str | None = None) -> dict[str, Any]:
        return await response(lambda: c.case.note(case_id, content, note_type, author_type, author_id))

    @m.tool(description="Retrieve chronological immutable case history for compliance, explainability and supervisor review.")
    async def get_case_history(case_id: str, limit: int = 200) -> dict[str, Any]:
        return await response(lambda: c.case.history(case_id, limit))

    @m.tool(
        description="Request human authorization for a sensitive card action. Use before any freeze, unfreeze or block; fraud score alone can never authorize it."
    )
    async def request_approval(
        case_id: str, action_type: str, action_payload: dict[str, Any], requested_by: str = "agent", idempotency_key: str | None = None
    ) -> dict[str, Any]:
        return await response(lambda: c.approval.request(case_id, action_type, action_payload, requested_by, idempotency_key))

    @m.tool(
        description="Record an authorized human approval and execute only the action payload stored with that approval. The caller cannot swap the approved payload."
    )
    async def approve_action(approval_id: str, reviewed_by: str, note: str | None = None, reviewer_role: str = "HUMAN_REVIEWER") -> dict[str, Any]:
        return await response(lambda: c.approval.approve(approval_id, reviewed_by, note, reviewer_role))

    @m.tool(description="Reject a pending sensitive action without executing it and return the case to investigation.")
    async def reject_action(approval_id: str, reviewed_by: str, note: str | None = None, reviewer_role: str = "HUMAN_REVIEWER") -> dict[str, Any]:
        return await response(lambda: c.approval.reject(approval_id, reviewed_by, note, reviewer_role))

    @m.tool(description="Read synthetic demo bank card control state. This is Case MCP state and is not supplied by Plaid.")
    async def get_card_status(customer_id: str, card_id: str) -> dict[str, Any]:
        async def run() -> Any:
            card = await c.cards.get(card_id)
            if card.customer_id != customer_id:
                raise ValueError("card does not belong to customer")
            return card

        return await response(run)

    @m.tool(description="Apply an approved demo bank action from ACTIVE to FROZEN. Requires a matching approved approval and does not call Plaid.")
    async def freeze_card(case_id: str, approval_id: str, card_id: str) -> dict[str, Any]:
        return await response(lambda: c.actions.execute(case_id, approval_id, card_id, "FREEZE_CARD"))

    @m.tool(description="Apply an approved demo bank action from FROZEN to ACTIVE. BLOCKED remains terminal and this does not call Plaid.")
    async def unfreeze_card(case_id: str, approval_id: str, card_id: str) -> dict[str, Any]:
        return await response(lambda: c.actions.execute(case_id, approval_id, card_id, "UNFREEZE_CARD"))

    @m.tool(description="Apply an approved demo bank action to make a synthetic card BLOCKED. BLOCKED is terminal in Phase 3.")
    async def block_card(case_id: str, approval_id: str, card_id: str) -> dict[str, Any]:
        return await response(lambda: c.actions.execute(case_id, approval_id, card_id, "BLOCK_CARD"))
