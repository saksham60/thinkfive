"""Common domain enums."""

from enum import Enum


class AgentName(str, Enum):
    """Agent names."""

    SUPERVISOR = "supervisor"
    BANKING = "banking"
    FRAUD = "fraud"
    KNOWLEDGE = "knowledge"
    CASE = "case"
    SYNTHESIS = "synthesis"


class Severity(str, Enum):
    """Risk severity levels."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
