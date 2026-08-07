# Case MCP

Case MCP is the persistent workflow and human-approval layer for the ThinkFive banking demo. It records customer-service and fraud-investigation cases, human decisions, simulated card controls, notification outbox entries, and an immutable application audit timeline.

It is deliberately separate from the two evidence systems:

- Banking MCP owns Plaid-backed accounts, balances, identity, and transactions.
- Fraud MCP owns risk assessments, signals, severity, and fraud alerts.
- Case MCP references evidence from those MCPs and owns the operational workflow in Supabase.

Case MCP does not calculate fraud risk and does not copy Plaid transaction storage.

## Architecture

The MCP factory (`create_case_mcp`) is separate from the standalone ASGI factory (`create_case_asgi_app`). This lets a future root application mount the three independently constructed MCP applications at `/mcp/banking`, `/mcp/fraud`, and `/mcp/case` in one container.

Production uses six Supabase repositories by default. Deterministic tests use six matching in-memory implementations. MCP schemas and tools do not depend on which implementation is injected.

Supabase tables:

- `cases`: primary workflow record and external evidence references
- `case_notes`: attributed investigation and communication notes
- `approvals`: immutable requested action payload plus human decision and consumption time
- `card_states`: synthetic demo bank-control state
- `notifications`: email, SMS, and in-app outbox
- `audit_events`: append-only application timeline

The migration enables RLS and removes direct `anon`/`authenticated` table access. The server-side service-role credential is used only inside Case MCP. Apply [001_case_mcp.sql](app/database/migrations/001_case_mcp.sql) with the migration script; it does not drop schemas, databases, or unrelated tables.

## State machines

Case transitions are centrally defined:

```text
OPEN -> TRIAGED | INVESTIGATING | AWAITING_APPROVAL | RESOLVED
TRIAGED -> INVESTIGATING | AWAITING_APPROVAL | RESOLVED
INVESTIGATING -> AWAITING_APPROVAL | RESOLVED
AWAITING_APPROVAL -> ACTION_APPROVED | ACTION_REJECTED | INVESTIGATING
ACTION_APPROVED -> INVESTIGATING | RESOLVED
ACTION_REJECTED -> INVESTIGATING | RESOLVED
RESOLVED -> CLOSED
CLOSED -> terminal
```

Approval state begins at `PENDING` and can be reviewed once as `APPROVED` or `REJECTED`; an expired request becomes `EXPIRED`. Supported sensitive actions are `FREEZE_CARD`, `UNFREEZE_CARD`, and `BLOCK_CARD`. When RBAC enforcement is enabled, the reviewer must use an allowed review role and cannot be the requesting actor.

Card transitions:

```text
ACTIVE -> FROZEN | BLOCKED
FROZEN -> ACTIVE | BLOCKED
BLOCKED -> terminal
```

Sensitive actions cannot execute until a matching human approval has been approved. The execution path reads the case, action type, and card identifier from the stored approval; callers cannot replace that payload after review. A high or critical fraud score creates no card action by itself.

Plaid does not freeze or block cards in this prototype. Card actions are simulated banking actions persisted in Supabase. Every seeded card is marked `synthetic=true` with source `demo_bank_control`.

## Fraud-alert workflow

`create_case_from_fraud_alert` asks Fraud MCP for the alert, validates its customer, carries forward alert/assessment/transaction references, records grounded severity and risk score when present, derives priority, and deduplicates by alert ID. Transaction ownership is validated through Banking MCP when a transaction reference is supplied. Provider failures fail closed and never fabricate evidence.

A normal sensitive-action flow is:

1. Create and assign the investigation case.
2. Add grounded investigation notes.
3. Request approval with the exact card action payload.
4. Verify card state is unchanged while approval is pending.
5. A distinct human reviewer approves or rejects.
6. Only an approved matching action updates synthetic card state.
7. Queue customer communication and resolve/close the case.
8. Retrieve the chronological audit trail.

## Notes, notifications, summaries, and audit

Notes are bounded, attributed, and included in the audit timeline. Summaries are deterministic and use only stored case data, notes, approvals, notifications, and resolution; no LLM or API key is required.

Email and SMS are represented through a Supabase notification outbox unless an external delivery provider is configured. Phase 3 records `QUEUED` with provider `SUPABASE_OUTBOX`, leaves `sent_at` empty, and never claims external delivery. `NotificationProvider` is the replacement boundary for a future Twilio, SendGrid, or SMTP adapter.

Create, update, assignment, note, approval, action, notification, resolution, and closure mutations append audit events with actor, entity, case/customer IDs, and before/after state where applicable.

## Idempotency and concurrency

Cases deduplicate on fraud-alert ID or idempotency key. Pending approvals deduplicate by case/action and optional key. Notifications deduplicate by key. Unique partial indexes enforce the important invariants in Supabase, while service locks make same-process races deterministic. Card actions use per-card locks and consumed approvals support safe exact retries without permitting later reuse against changed state.

## Configuration

Copy `.env.example` values into `mcp/.env` or `mcp/case/.env`. Required production variables are:

```dotenv
SUPABASE_URL=https://project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=server-only-service-role-key
```

The existing compatibility variable `SUPABASE_SECRET_KEY` is accepted, but `SUPABASE_SERVICE_ROLE_KEY` is the canonical name. Never expose either to web or mobile clients.

Recommended variables:

```dotenv
MCP_AUTH_TOKEN=shared-bearer-token
BANKING_MCP_URL=http://localhost:8000/mcp
BANKING_MCP_AUTH_TOKEN=
FRAUD_MCP_URL=http://localhost:8001/mcp
FRAUD_MCP_AUTH_TOKEN=
CASE_MCP_MOUNT_PATH=/mcp
CASE_AUTO_MIGRATE=false
CASE_AUTO_SEED=false
CASE_ENFORCE_RBAC=true
CASE_REPOSITORY_BACKEND=supabase
```

`SUPABASE_DB_URL` is required only to run SQL migrations. A Supabase service key can call the Data API but cannot execute PostgreSQL DDL.

## Install, migrate, test, and run

The project requires Python 3.12+. No virtual environment is required:

```bash
python -m pip install --user -e "mcp/case[dev]"
python mcp/case/scripts/migrate.py
python mcp/case/scripts/seed_demo_data.py
python -m pytest -q -p no:cacheprovider mcp/case/tests
python mcp/case/scripts/smoke_test.py
python -m uvicorn app.main:create_app --factory --app-dir mcp/case --host 0.0.0.0 --port 8002
```

Standalone endpoints:

- MCP: `http://localhost:8002/mcp/`
- health: `http://localhost:8002/health`
- readiness: `http://localhost:8002/ready`

Set `RUN_SUPABASE_INTEGRATION_TESTS=true` after applying the migration to enable the real Supabase round-trip and scoped cleanup. Set `RUN_MCP_INTEGRATION_TESTS=true` plus the Banking/Fraud URLs and `CASE_TEST_FRAUD_ALERT_ID`/`CASE_TEST_CUSTOMER_ID` to enable the live cross-MCP flow.

## Docker and Render

Build and run standalone:

```bash
docker build -t thinkfive-case-mcp mcp/case
docker run --rm -p 8002:8000 --env-file mcp/.env thinkfive-case-mcp
```

`render.yaml` uses Docker with root directory `mcp/case`, health path `/health`, and `CASE_MCP_MOUNT_PATH=/mcp`. Add `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, optional bearer/provider tokens, and provider URLs as secret Render environment values. The container binds `0.0.0.0:$PORT`.

For the future combined container, construct the MCP without starting Uvicorn and mount its HTTP application at `/mcp/case`. Case MCP has no hardcoded port, global process startup, or assumption that it owns the root ASGI application.

## Security notes and limitations

- MCP bearer authentication is enabled when `MCP_AUTH_TOKEN` is configured; health/readiness remain suitable for platform probes.
- Service-role, database, and upstream MCP tokens are represented as secret settings and are never returned by tools or readiness output.
- Tool errors return stable safe envelopes without exception internals or credentials.
- Reviewer identity and role are service-authenticated claims in this phase; a combined production gateway should derive them from verified identity rather than accepting arbitrary client strings.
- Supabase Data API operations are individually persistent. Multi-record approval/action updates are protected and ordered in the service, but full cross-table transactional execution should move to a narrowly scoped PostgreSQL RPC before real financial controls are introduced.
- Email/SMS delivery workers and real issuer/card-processor controls are intentionally outside Phase 3.
