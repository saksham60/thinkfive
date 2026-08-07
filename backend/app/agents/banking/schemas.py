"""Banking Agent structured output schemas."""

from typing import Literal

from pydantic import BaseModel, Field


class BankingEvidence(BaseModel):
    """Banking evidence structure."""

    evidence_type: Literal["accounts", "transactions", "identity", "liabilities", "connection"]
    data: dict | list
    source: str = "Banking MCP"
    confidence: Literal["high", "medium", "low"] = "high"
    timestamp: str


class AccountSummary(BaseModel):
    """Account summary result."""

    total_accounts: int
    balance_by_currency: dict[str, float]
    account_types: list[str]


class TransactionSearchResult(BaseModel):
    """Transaction search result."""

    transaction_count: int
    transactions: list[dict]
    search_criteria: dict


class BankingAgentOutput(BaseModel):
    """Banking Agent structured output."""

    goal_completed: bool = Field(description="Whether the banking goal was achieved")
    evidence: list[BankingEvidence] = Field(description="Banking evidence collected")
    findings: str = Field(description="Natural language summary of findings")
    requires_clarification: bool = Field(
        default=False,
        description="True if user clarification is needed",
    )
    clarification_question: str | None = Field(
        default=None,
        description="Question to ask user if clarification needed",
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Any warnings about data quality or limitations",
    )
