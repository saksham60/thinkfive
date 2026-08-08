# ThinkFive Banking MCP

ThinkFive Banking MCP is the provider-neutral banking-data boundary for an AI-assisted customer-query and fraud-alert platform. It exposes stable typed tools over MCP Streamable HTTP while keeping provider credentials and persistence details on the server.

> Banking MCP provides access to banking data. It does not determine whether a transaction is fraudulent.

> Banking MCP does not perform card issuer operations such as freezing or blocking cards.

> Transaction search operates over the MCP's synchronized TransactionRepository. It is not represented as a native Plaid arbitrary transaction-search API.

## Architecture

```text
Supervisor Agent
      |
      +-- Banking MCP --> Supabase canonical store (live demo)
      |               `-> Plaid (optional compatibility mode)
      +-- Fraud MCP --> same canonical banking evidence
      `-- Case MCP ---> Supabase workflow data
```

Standalone Phase 1:

```text
Uvicorn -> FastAPI parent
              +-- /mcp             FastMCP Streamable HTTP
              +-- /health          process health
              +-- /ready           local readiness
              `-- /webhooks/plaid  verified, fast webhook handler
                         |
              services + repository interfaces
                         |
                 official Plaid SDK
```

The code does not bind a port during import. `create_banking_mcp()` creates only the MCP server, while `create_banking_asgi_app()` creates the standalone parent application. Services, repositories, models, and tool contracts do not know the mount path.

Future combined container:

```text
mcp/app.py
  +-- /mcp/banking  -> create_banking_mcp(container).http_app(path="/")
  +-- /mcp/fraud    -> Fraud MCP
  +-- /mcp/case     -> Case MCP
  +-- /webhooks/plaid
  +-- /health
  `-- /ready
```

The combined parent must enter the FastMCP ASGI lifespan. Only that parent binds `0.0.0.0:$PORT` and owns shared health routes and middleware.

## Project layout

```text
app/
  main.py                 standalone ASGI factory
  config.py               typed environment configuration
  container.py            dependency assembly
  security.py             optional MCP bearer guard
  logging.py              structured JSON logs and redaction
  mcp/server.py           MCP factory
  mcp/tools/              15 domain tool registrations
  models/                 external domain contracts
  plaid/                  official SDK gateway, mapping, safe errors
  repositories/           in-memory Phase 1 repository implementations
  services/               banking, synchronization, bootstrap, sandbox logic
  webhook/                JWT verification and idempotent handling
scripts/
  bootstrap_sandbox.py
  smoke_test.py
tests/
  unit/
  integration/
Dockerfile
render.yaml
pyproject.toml
```

## Local setup

Python 3.12 or newer is required. From `mcp/plaidbanking`:

```powershell
python -m pip install -e ".[dev]"
python -m uvicorn app.main:create_app --factory --host 0.0.0.0 --port 8000
```

Local configuration is loaded from `mcp/.env`; an optional `mcp/plaidbanking/.env` overrides it. Copy `.env.example` if you prefer a project-local file. Both locations must stay out of Git.

## Configuration

| Variable | Required | Default | Purpose |
|---|---:|---|---|
| `BANKING_DATA_PROVIDER` | no | `plaid` | Select `plaid` or `supabase` |
| `SUPABASE_URL` | Supabase mode | — | Canonical Supabase project URL |
| `SUPABASE_SECRET_KEY` or `SUPABASE_SERVICE_ROLE_KEY` | Supabase mode | — | Server-only data key; never expose to browsers |
| `PLAID_CLIENT_ID` | Plaid mode | — | Plaid client identifier |
| `PLAID_SECRET` | Plaid mode | — | Plaid environment secret |
| `PLAID_ENV` | yes | `sandbox` | `sandbox`, `development`, or `production` |
| `PLAID_WEBHOOK_URL` | no | — | Public Plaid webhook URL |
| `MCP_AUTH_TOKEN` | no | — | Opaque bearer token protecting only the MCP route |
| `PLAID_AUTO_BOOTSTRAP` | no | `true` | Create the demo Sandbox Item during startup |
| `PLAID_DEFAULT_CUSTOMER_ID` | no | `demo_customer_001` | Demo repository partition |
| `PLAID_INSTITUTION_ID` | no | `ins_109508` | Non-OAuth Sandbox institution |
| `PLAID_MCP_MOUNT_PATH` | no | `/mcp` | Standalone MCP mount path |
| `PLAID_TIMEOUT_SECONDS` | no | `10` | Strict provider timeout |
| `PLAID_MAX_RETRIES` | no | `3` | Bounded retry attempts |
| `RUN_PLAID_SANDBOX_TESTS` | no | `false` | Enable tests that call Plaid |

Pydantic validates configuration before startup. Secret values use `SecretStr`, are absent from readiness details, and are redacted from structured fields.

## Sandbox bootstrap

Plaid bootstrap runs only when `BANKING_DATA_PROVIDER=plaid` and `PLAID_AUTO_BOOTSTRAP=true`. Supabase mode creates no Plaid client, performs no token exchange, and makes no Plaid runtime call.

Manual bootstrap:

```powershell
python scripts/bootstrap_sandbox.py
```

In Supabase mode, accounts, connections, and transactions are durable across restarts. Simulation inserts only a canonical transaction row and intentionally does not mutate account balances.

## Repository design

`ItemRepository` maps an application `customer_id` to the server-only Plaid access token and Item ID. Tools and callers never accept or return an access token. `InMemoryItemRepository` also maintains the reverse Item-to-customer lookup required by webhooks.

`TransactionRepository` owns current transaction state and partitions every operation by customer. `SupabaseTransactionRepository` queries individual transactions with both `customer_id` and `transaction_id` without changing models, service contracts, MCP tools, or supervisor prompts.

`SyncStateRepository` owns the internal cursor, last sync time, status, stale flag, and one lock per customer. Customers synchronize independently.

## Synchronization

```text
first/stale read -> acquire customer lock -> /transactions/sync page loop
  -> collect added + modified + removed
  -> atomically update TransactionRepository
  -> commit new cursor and freshness state
  -> answer from repository
```

The cursor is committed only after repository mutation succeeds. On any failure, the previous cursor is retained and state remains stale. Repeating a page is safe because transaction upserts and removals are idempotent. Explicit `sync_transactions` always synchronizes; normal reads synchronize only on first access or after a webhook/refresh marks the customer stale.

## MCP tool catalog

All tools return a consistent envelope containing `success`, `source`, `customer_id`, `retrieved_at`, `data`, and `warnings`, or a safe `error` object.

| Tool | Arguments | Purpose |
|---|---|---|
| `get_customer_identity` | `customer_id` | Return available Plaid Identity owners and linked accounts |
| `verify_customer_identity` | `customer_id`, optional `name`, `phone`, `email`, `address` | Return Identity Match evidence when enabled |
| `get_accounts` | `customer_id` | List linked accounts and balances |
| `get_account_summary` | `customer_id` | Summarize accounts with totals separated by currency |
| `get_account_balance` | `customer_id`, `account_id` | Return one customer-owned account balance |
| `sync_transactions` | `customer_id` | Apply all incremental sync pages to local state |
| `get_recent_transactions` | `customer_id`, `limit=20`, optional `account_id` | Read recent synchronized transactions |
| `get_transaction` | `customer_id`, `transaction_id` | Read one customer-owned transaction |
| `search_transactions` | `customer_id`, optional account/merchant/amount/date/category/pending filters, `limit=100` | Search synchronized repository state |
| `refresh_transactions` | `customer_id` | Request asynchronous Plaid refresh and mark state stale |
| `get_liabilities` | `customer_id` | Return enabled credit, mortgage, and student liability data |
| `get_banking_connection_status` | `customer_id` | Return safe Item health and sync freshness |
| `simulate_transaction` | `customer_id`, `amount`, `description`, optional `date` | Create synthetic Sandbox transaction data |
| `fire_transaction_webhook` | `customer_id` | Trigger a Sandbox transaction webhook |
| `create_demo_fraud_scenario` | `customer_id` | Generate suspicious-looking data for Fraud MCP to assess |

Example response:

```json
{
  "success": true,
  "source": "plaid_sandbox",
  "customer_id": "demo_customer_001",
  "retrieved_at": "2026-08-07T12:00:00Z",
  "data": {"account_count": 2},
  "warnings": []
}
```

Example safe failure:

```json
{
  "success": false,
  "source": "plaid_sandbox",
  "customer_id": "unknown",
  "retrieved_at": "2026-08-07T12:00:00Z",
  "error": {
    "error_code": "CUSTOMER_NOT_FOUND",
    "message": "No banking connection exists for this customer.",
    "retryable": false
  }
}
```

## Webhooks

`POST /webhooks/plaid` preserves the exact request bytes and validates the `Plaid-Verification` JWT using Plaid's current ES256 JWK mechanism. Verification enforces the signing algorithm, key ID, signature, issued-at time within five minutes, and a constant-time SHA-256 body comparison. Keys are cached with a bounded lifetime.

Transaction update events resolve the Item internally, atomically claim a body-derived event ID, mark the customer stale, and return without synchronizing. Duplicate events are acknowledged idempotently; unsupported events are safely ignored; expired signatures and invalid body hashes return 401. A future handler can publish to a durable queue without changing the endpoint.

## Security and observability

- Credentials come only from environment variables.
- Plaid access/public tokens and sync cursors never enter MCP models.
- Account and transaction lookups are customer-partitioned.
- Sandbox mutations are rejected outside Sandbox.
- Plaid calls use strict timeouts and exponential backoff with jitter only for transient failures.
- Tool errors never include stack traces.
- Optional `MCP_AUTH_TOKEN` uses constant-time bearer comparison; health and Plaid webhook routes remain independent.
- JSON logs support request/provider/error metadata and recursively redact sensitive keys.
- Financial PII and provider response bodies are not logged.

In-memory repositories are suitable for one-process Phase 1. They are not suitable for multiple Uvicorn workers, rolling deployments, or durable banking history. Use one worker until durable repositories and distributed locking are implemented.

## Testing

Mocked tests cover configuration, secret redaction, Item lifecycle, customer isolation, transaction filters, added/modified/removed reconciliation, cursor failure safety, stale/current behavior, concurrency, accounts, multi-currency summaries, Sandbox guards, all MCP registrations, bearer auth, webhook signatures, body integrity, duplicates, and malformed input.

```powershell
python -m pytest -q -p no:cacheprovider
python -m ruff check app tests scripts
python -m mypy app
```

Real Sandbox integration is opt-in:

```powershell
$env:RUN_PLAID_SANDBOX_TESTS="true"
python -m pytest -q -m sandbox -p no:cacheprovider
python scripts/smoke_test.py
```

The smoke test validates configuration, bootstrap, connection, accounts, balances, initial sync, repository reads/search, transaction lookup, a custom synthetic transaction, a second sync, and secret protection. It prints no token values.

## Docker

```powershell
docker build -t plaid-banking-mcp .
docker run --rm -p 8000:8000 --env-file ../.env plaid-banking-mcp
```

The image runs as a non-root user and starts `uvicorn app.main:create_app --factory --host 0.0.0.0 --port $PORT`.

## Render deployment

1. Push this repository without either `.env` file.
2. In Render, create a Blueprint using `mcp/plaidbanking/render.yaml`, or create a Docker Web Service with root directory `mcp/plaidbanking`. The Blueprint already sets this root directory.
3. For the live demo set `BANKING_DATA_PROVIDER=supabase`, `PLAID_AUTO_BOOTSTRAP=false`, `SUPABASE_URL`, and a server-only Supabase secret key.
4. Plaid credentials and webhook configuration are required only when explicitly switching back to `BANKING_DATA_PROVIDER=plaid`.
5. Optionally set `MCP_AUTH_TOKEN` and supply it to MCP clients as a bearer token.
6. Deploy and verify `/health`, `/ready`, and `/mcp/`.

Standalone endpoints:

- MCP: `https://<service>/mcp/`
- Health: `https://<service>/health`
- Readiness: `https://<service>/ready`
- Plaid webhook: `https://<service>/webhooks/plaid`

The combined MCP endpoint is `https://<service>/mcp/banking/`.

## Product availability and boundaries

Sandbox bootstrap requests Transactions and Identity. Identity Match and Liabilities depend on products enabled for the Plaid account and Item; their tools explicitly report capability unavailability instead of fabricating results. Sandbox custom transactions require `user_transactions_dynamic`.

This MCP intentionally has no fraud scoring, anomaly detection, device analysis, blacklist checks, case persistence, approvals, notifications, card status, freeze/block operation, LLM orchestration, or Supabase implementation. Fraud analysis belongs to Fraud MCP; workflow and persistence belong to Case MCP.
