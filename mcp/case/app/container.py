from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from case.app.authorization import AuthorizationPolicy
from case.app.config import Settings
from case.app.database import create_supabase_client
from case.app.providers import (
    BankingDataProvider,
    FraudDataProvider,
    McpBankingDataProvider,
    McpFraudDataProvider,
    NullBankingProvider,
    NullFraudProvider,
    SupabaseNotificationProvider,
)
from case.app.repositories.interfaces import (
    ApprovalRepository,
    AuditRepository,
    CardStateRepository,
    CaseNoteRepository,
    CaseRepository,
    NotificationRepository,
)
from case.app.repositories.memory import (
    InMemoryApprovalRepository,
    InMemoryAuditRepository,
    InMemoryCardStateRepository,
    InMemoryCaseNoteRepository,
    InMemoryCaseRepository,
    InMemoryNotificationRepository,
)
from case.app.repositories.supabase import (
    SupabaseApprovalRepository,
    SupabaseAuditRepository,
    SupabaseCardStateRepository,
    SupabaseCaseNoteRepository,
    SupabaseCaseRepository,
    SupabaseNotificationRepository,
)
from case.app.services.workflow import (
    ActionService,
    ApprovalService,
    AuditService,
    CaseService,
    NotificationService,
    SummaryService,
)


@dataclass(slots=True)
class Container:
    settings: Settings
    cases: CaseRepository
    notes: CaseNoteRepository
    approvals: ApprovalRepository
    cards: CardStateRepository
    notifications: NotificationRepository
    audits: AuditRepository
    banking: BankingDataProvider
    fraud: FraudDataProvider
    audit: AuditService
    case: CaseService
    actions: ActionService
    approval: ApprovalService
    notification: NotificationService
    summary: SummaryService


def create_container(
    settings: Settings, *, memory: bool = False, banking: BankingDataProvider | None = None, fraud: FraudDataProvider | None = None, supabase_client: Any = None
) -> Container:
    use_memory = memory or settings.repository_backend == "memory"
    cases: CaseRepository
    notes: CaseNoteRepository
    approvals: ApprovalRepository
    cards: CardStateRepository
    notifications: NotificationRepository
    audits: AuditRepository
    if use_memory:
        cases = InMemoryCaseRepository()
        notes = InMemoryCaseNoteRepository()
        approvals = InMemoryApprovalRepository()
        cards = InMemoryCardStateRepository()
        notifications = InMemoryNotificationRepository()
        audits = InMemoryAuditRepository()
    else:
        client = supabase_client or create_supabase_client(settings)
        cases = SupabaseCaseRepository(client)
        notes = SupabaseCaseNoteRepository(client)
        approvals = SupabaseApprovalRepository(client)
        cards = SupabaseCardStateRepository(client)
        notifications = SupabaseNotificationRepository(client)
        audits = SupabaseAuditRepository(client)
    bp = banking or (
        McpBankingDataProvider(settings.banking_mcp_url, settings.banking_mcp_auth_token.get_secret_value() if settings.banking_mcp_auth_token else None)
        if settings.banking_mcp_url
        else NullBankingProvider()
    )
    fp = fraud or (
        McpFraudDataProvider(settings.fraud_mcp_url, settings.fraud_mcp_auth_token.get_secret_value() if settings.fraud_mcp_auth_token else None)
        if settings.fraud_mcp_url
        else NullFraudProvider()
    )
    audit = AuditService(audits)
    actions = ActionService(cases, approvals, cards, audit)
    case = CaseService(cases, notes, approvals, cards, notifications, audit, bp, fp)
    approval = ApprovalService(cases, approvals, audit, actions, AuthorizationPolicy(settings.case_enforce_rbac))
    return Container(
        settings,
        cases,
        notes,
        approvals,
        cards,
        notifications,
        audits,
        bp,
        fp,
        audit,
        case,
        actions,
        approval,
        NotificationService(cases, SupabaseNotificationProvider(notifications), audit),
        SummaryService(cases, notes, approvals, notifications),
    )
