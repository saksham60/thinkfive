# Backend completion status

The backend implementation is functionally wired end-to-end. Live deployment validation remains gated by environment credentials and running services.

## Implemented

- Direct `DATABASE_URL` usage for asyncpg, migrations, RAG, and LangGraph PostgreSQL checkpoints.
- FastMCP 3 Streamable HTTP clients for `/mcp/banking`, `/mcp/fraud`, and `/mcp/case`, owned by one lifespan-managed manager.
- Central MCP success-envelope normalization and typed failures.
- Banking, Fraud, Case, notification, and Sandbox adapter contracts aligned to the source in `mcp/`.
- Bounded specialist tool loops using real `ToolMessage` results; business IDs are derived from MCP results.
- Trusted backend customer injection; customer-facing LLM tools cannot select another customer.
- Persistent conversation history, bounded prompt context, customer memory reads, summaries, and idempotent assistant-message persistence.
- True LangGraph interrupts correlated through `workflow_interrupts`, with trusted customer recovery and PostgreSQL resume.
- Human approve/reject endpoints; Case MCP approval executes a stored card action exactly once and the backend only reads the resulting card status.
- Durable workflow/tool/domain SSE events and replay with `Last-Event-ID`; heartbeat remains transient.
- bcrypt demo-password validation and `GET /api/auth/me`.
- Policy search API and programmatic citation filtering.
- Transaction monitoring baseline and Fraud MCP-owned alert-threshold behavior.
- Executable evaluation cases and corrected Docker package-copy order.

## Verification

- Unit/contract/security/HITL/SSE/RAG suite: see the latest `pytest` result.
- Ruff: clean.
- Targeted mypy over changed runtime modules: clean.
- Live MCP integration tests require `RUN_INTEGRATION_TESTS=1` and configured service credentials.
- Migration, live graph smoke test, restart recovery, and Docker image execution require external PostgreSQL/MCP/LLM services (and a running Docker engine).

## Demo credentials

- Customer: `demo@thinkfive.ai` / `demo123`
- Analyst: `analyst@thinkfive.ai` / `analyst123`

Permissive CORS is intentional for this demo phase and should be tightened before production.
