"""LangGraph PostgreSQL checkpoint saver integration."""

from __future__ import annotations

import logging
from contextlib import AbstractAsyncContextManager

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from app.core.config import Settings

logger = logging.getLogger(__name__)


class CheckpointerFactory:
    """Factory for the LangGraph PostgreSQL checkpoint saver.

    Uses the officially supported ``AsyncPostgresSaver`` so that graph
    execution state (messages, evidence, HITL interrupts) survives process
    restarts. ``thread_id`` maps 1:1 to ``conversation_id``.
    """

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._saver: AsyncPostgresSaver | None = None
        self._cm: AbstractAsyncContextManager[AsyncPostgresSaver] | None = None

    async def setup(self) -> AsyncPostgresSaver:
        """Create and set up the checkpointer (creates required tables)."""
        if self._saver is not None:
            return self._saver

        ctx = AsyncPostgresSaver.from_conn_string(self.settings.postgres_url)
        self._saver = await ctx.__aenter__()
        self._cm = ctx
        await self._saver.setup()
        logger.info("LangGraph PostgreSQL checkpointer ready")
        return self._saver

    async def close(self) -> None:
        """Tear down the checkpointer connection."""
        if self._cm is not None:
            await self._cm.__aexit__(None, None, None)
            self._cm = None
            self._saver = None

    @property
    def saver(self) -> AsyncPostgresSaver:
        if self._saver is None:
            raise RuntimeError("Checkpointer not initialized - call setup() first")
        return self._saver
