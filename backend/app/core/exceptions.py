"""Domain and application exceptions."""


class DomainError(Exception):
    """Base exception for domain errors."""

    def __init__(self, message: str, code: str | None = None) -> None:
        self.message = message
        self.code = code or self.__class__.__name__
        super().__init__(message)


class ValidationError(DomainError):
    """Validation error."""

    pass


class NotFoundError(DomainError):
    """Resource not found."""

    pass


class AuthenticationError(DomainError):
    """Authentication failed."""

    pass


class AuthorizationError(DomainError):
    """Authorization failed."""

    pass


class ConflictError(DomainError):
    """Resource conflict."""

    pass


class MCPError(DomainError):
    """MCP communication error."""

    pass


class LLMError(DomainError):
    """LLM provider error."""

    pass


class GraphError(DomainError):
    """LangGraph execution error."""

    pass


class HITLError(DomainError):
    """HITL workflow error."""

    pass


class MemoryError(DomainError):
    """Memory operation error."""

    pass


class RAGError(DomainError):
    """RAG operation error."""

    pass
