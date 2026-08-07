"""Case API schemas."""

from typing import Any

from pydantic import BaseModel


class AddCaseNoteRequest(BaseModel):
    content: str
    note_type: str = "GENERAL"


class CaseListResponse(BaseModel):
    cases: list[dict[str, Any]]
