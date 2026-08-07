from __future__ import annotations

from case.app.config import Settings
from case.app.database import apply_case_migrations


def main() -> None:
    s = Settings()
    try:
        apply_case_migrations(s)
    except RuntimeError as exc:
        raise SystemExit(f"{exc}; service API keys cannot execute PostgreSQL DDL.") from exc
    print("Case MCP migration applied successfully.")


if __name__ == "__main__":
    main()
