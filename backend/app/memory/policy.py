"""Memory policy enforcement wrapper (delegates to domain policy, adds PII scan)."""

from __future__ import annotations

from app.domain.memory.policies import MemoryPolicy as DomainMemoryPolicy
from app.memory.models import MemoryCandidate


class MemoryPolicyEnforcer:
    """Enforces MemoryPolicy before any candidate memory reaches the repository.

    Write flow: candidate -> structured extraction -> PII/secret check -> policy -> repository.
    The LLM alone never decides what becomes durable memory.
    """

    def can_store(self, candidate: MemoryCandidate) -> bool:
        return DomainMemoryPolicy.can_store(
            candidate.memory_type,
            candidate.memory_key,
            candidate.content,
        )
