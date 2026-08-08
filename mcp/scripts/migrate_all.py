from case.app.config import Settings
from migrations import apply_all_migrations

if __name__ == "__main__":
    apply_all_migrations(Settings())  # type: ignore[call-arg]
    print("Banking, Fraud, and Case MCP migrations applied successfully.")
