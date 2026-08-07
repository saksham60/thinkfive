from __future__ import annotations

from datetime import date as Date
from datetime import datetime as DateTime
from decimal import Decimal
from typing import Any

from pydantic import Field, field_validator

from .common import StrictModel


class Transaction(StrictModel):
    customer_id: str = Field(exclude=True)
    transaction_id: str
    account_id: str
    amount: Decimal
    currency: str | None = None
    merchant_name: str | None = None
    transaction_name: str
    date: Date
    authorized_date: Date | None = None
    datetime: DateTime | None = None
    pending: bool = False
    category: tuple[str, ...] = ()
    personal_finance_category: dict[str, Any] | None = None
    payment_channel: str | None = None
    location: dict[str, Any] | None = None
    website: str | None = None
    logo_url: str | None = None
    entity_id: str | None = None


class TransactionSearchFilters(StrictModel):
    account_id: str | None = None
    merchant: str | None = None
    min_amount: Decimal | None = None
    max_amount: Decimal | None = None
    start_date: Date | None = None
    end_date: Date | None = None
    category: str | None = None
    pending: bool | None = None
    limit: int = Field(default=100, ge=1, le=100)

    @field_validator("max_amount")
    @classmethod
    def validate_amount_range(cls, value: Decimal | None, info: Any) -> Decimal | None:
        minimum = info.data.get("min_amount")
        if value is not None and minimum is not None and value < minimum:
            raise ValueError("max_amount must be greater than or equal to min_amount")
        return value

    @field_validator("end_date")
    @classmethod
    def validate_date_range(cls, value: Date | None, info: Any) -> Date | None:
        start = info.data.get("start_date")
        if value is not None and start is not None and value < start:
            raise ValueError("end_date must be on or after start_date")
        return value


class SyncSummary(StrictModel):
    added_count: int = 0
    modified_count: int = 0
    removed_count: int = 0
    current_repository_count: int = 0
    sync_completed: bool = True
    pages_processed: int = 0
