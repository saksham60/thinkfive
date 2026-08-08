from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

from scripts.migrate import apply_migration, get_migration_checksum


class AsyncTransaction:
    async def __aenter__(self) -> None:
        return None

    async def __aexit__(self, *_args: object) -> None:
        return None


async def test_runner_records_successful_migration(tmp_path) -> None:
    migration = tmp_path / "008_transaction_monitor_state.sql"
    migration.write_text("SELECT 1;")
    connection = SimpleNamespace(
        transaction=Mock(return_value=AsyncTransaction()),
        execute=AsyncMock(),
    )

    await apply_migration(connection, migration)  # type: ignore[arg-type]

    assert connection.execute.await_count == 2
    first_call, record_call = connection.execute.await_args_list
    assert first_call.args == ("SELECT 1;",)
    assert "INSERT INTO backend_schema_migrations" in record_call.args[0]
    assert record_call.args[1:] == (
        "008_transaction_monitor_state",
        get_migration_checksum("SELECT 1;"),
        "008 transaction monitor state",
    )
