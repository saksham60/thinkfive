"""Knowledge Agent structured output schemas."""

from pydantic import BaseModel, Field


class Citation(BaseModel):
    """A grounded citation for a policy claim."""

    document_id: str
    title: str
    version: str | None = None
    jurisdiction: str | None = None
    page: int | None = None
    section: str | None = None


class KnowledgeAgentOutput(BaseModel):
    """Knowledge Agent structured output."""

    goal_completed: bool
    findings: str = Field(description="Answer grounded strictly in retrieved evidence")
    citations: list[Citation] = Field(default_factory=list)
    evidence_available: bool = Field(
        description="False if retrieval returned nothing relevant - triggers 'evidence unavailable' response"
    )
    warnings: list[str] = Field(default_factory=list)
