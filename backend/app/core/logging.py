"""Logging configuration."""

import logging
import sys

from .correlation import get_correlation_id


class CorrelationFilter(logging.Filter):
    """Add correlation ID to log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.correlation_id = get_correlation_id()  # type: ignore[attr-defined]
        return True


def configure_logging(log_level: str = "INFO") -> None:
    """Configure application logging with correlation IDs."""
    handler = logging.StreamHandler(sys.stdout)
    # Filters attached to the root logger do not run for records propagated
    # from descendant/third-party loggers. Attach it to the handler so every
    # record formatted below has the required field.
    handler.addFilter(CorrelationFilter())
    logging.basicConfig(
        level=log_level.upper(),
        format="%(asctime)s [%(levelname)s] [%(correlation_id)s] %(name)s: %(message)s",
        handlers=[handler],
        force=True,
    )

    # Reduce noise from third-party libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger for the given name."""
    return logging.getLogger(name)
