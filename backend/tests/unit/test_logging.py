"""Logging configuration tests."""

from __future__ import annotations

import io
import logging

from app.core.logging import configure_logging


def test_third_party_log_records_receive_correlation_id(monkeypatch: object) -> None:
    """Propagated records must contain fields required by the root formatter."""
    stream = io.StringIO()
    monkeypatch.setattr("sys.stdout", stream)  # type: ignore[attr-defined]

    try:
        configure_logging("INFO")
        logging.getLogger("third.party").info("ready")
        assert "third.party: ready" in stream.getvalue()
    finally:
        logging.basicConfig(handlers=[logging.NullHandler()], force=True)
