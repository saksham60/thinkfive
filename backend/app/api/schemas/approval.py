"""Approval API schemas."""

from pydantic import BaseModel


class ApproveRequest(BaseModel):
    """Approval request - NOTE: no reviewed_by/role/action fields accepted from client.

    Actor identity and role come exclusively from the authenticated session.
    """

    note: str | None = None


class RejectRequest(BaseModel):
    note: str | None = None


class ApprovalActionResponse(BaseModel):
    approval_id: str
    decision: str
    action_result: dict
