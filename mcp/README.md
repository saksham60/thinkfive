# ThinkFive combined MCP deployment

This directory is the only production deployment boundary: one Render Web Service, one Docker image, one Python process, one port, and three independent MCP endpoints.

## Production deployment

The platform is deployed at:

**https://thinkfive-mcp-stack.onrender.com**

Verified public status endpoints:

- [Health](https://thinkfive-mcp-stack.onrender.com/health) - process and module liveness
- [Readiness](https://thinkfive-mcp-stack.onrender.com/ready) - authentication, Plaid configuration, provider mode, and Supabase availability

Production MCP endpoints:

```text
https://thinkfive-mcp-stack.onrender.com/mcp/banking/
https://thinkfive-mcp-stack.onrender.com/mcp/fraud/
https://thinkfive-mcp-stack.onrender.com/mcp/case/
```

The Plaid webhook endpoint is:

```text
https://thinkfive-mcp-stack.onrender.com/webhooks/plaid
```

## Routes

- `/mcp/banking` - Plaid banking evidence
- `/mcp/fraud` - deterministic, explainable fraud analysis
- `/mcp/case` - persistent workflow and human approval
- `/webhooks/plaid` - verified Plaid webhooks
- `/health` - process liveness
- `/ready` - authentication and dependency readiness

The combined app uses direct in-process providers. `BANKING_MCP_URL`, `BANKING_MCP_AUTH_TOKEN`, `FRAUD_MCP_URL`, and `FRAUD_MCP_AUTH_TOKEN` must remain blank when `MCP_PROVIDER_MODE=local`.

## Connecting an agent

All MCP endpoints use Streamable HTTP and require the same bearer token. Copy `MCP_AUTH_TOKEN` from the Render service's **Environment** page and keep it in the agent's secret storage.

For an MCP client that accepts JSON server definitions:

```json
{
  "mcpServers": {
    "thinkfive-banking": {
      "type": "http",
      "url": "https://thinkfive-mcp-stack.onrender.com/mcp/banking/",
      "headers": {
        "Authorization": "Bearer ${MCP_AUTH_TOKEN}"
      }
    },
    "thinkfive-fraud": {
      "type": "http",
      "url": "https://thinkfive-mcp-stack.onrender.com/mcp/fraud/",
      "headers": {
        "Authorization": "Bearer ${MCP_AUTH_TOKEN}"
      }
    },
    "thinkfive-case": {
      "type": "http",
      "url": "https://thinkfive-mcp-stack.onrender.com/mcp/case/",
      "headers": {
        "Authorization": "Bearer ${MCP_AUTH_TOKEN}"
      }
    }
  }
}
```

Python agents can connect with FastMCP:

```python
import asyncio
import os

from fastmcp import Client


async def main() -> None:
    token = os.environ["MCP_AUTH_TOKEN"]
    async with Client(
        "https://thinkfive-mcp-stack.onrender.com/mcp/banking/",
        auth=token,
    ) as banking:
        tools = await banking.list_tools()
        result = await banking.call_tool(
            "get_accounts",
            {"customer_id": "demo_customer_001"},
        )
        print([tool.name for tool in tools])
        print(result.structured_content)


asyncio.run(main())
```

Recommended supervisor flow:

1. Banking: sync transactions and retrieve the target transaction.
2. Fraud: assess the transaction and create an alert when the score meets the configured threshold.
3. Case: create a case from the alert, investigate, and request approval.
4. A human reviewer approves or rejects the sensitive action.
5. Case: execute the matching simulated card action and record notification/audit evidence.

## MCP tool catalog

### Banking MCP - 15 tools

- `get_customer_identity` - retrieve Plaid identity evidence for a customer.
- `verify_customer_identity` - compare supplied identity claims with Plaid evidence.
- `get_accounts` - list the customer's linked accounts and balances.
- `get_account_summary` - return a bounded summary across linked accounts.
- `get_account_balance` - retrieve balance details for one account.
- `get_banking_connection_status` - inspect the customer's Plaid connection and sync state.
- `sync_transactions` - synchronize transaction changes from Plaid.
- `get_recent_transactions` - return bounded recent customer transactions.
- `get_transaction` - retrieve one customer-scoped transaction.
- `search_transactions` - search transactions using structured filters.
- `refresh_transactions` - ask Plaid Sandbox to refresh transaction data.
- `get_liabilities` - retrieve supported liability information.
- `simulate_transaction` - create a synthetic Plaid Sandbox transaction.
- `fire_transaction_webhook` - trigger a synthetic Sandbox transaction webhook.
- `create_demo_fraud_scenario` - generate a suspicious Sandbox transaction for demonstrations.

### Fraud MCP - 11 tools

- `assess_transaction_risk` - calculate an evidence-driven risk assessment for a Banking transaction.
- `get_risk_assessment` - retrieve a persisted assessment by ID.
- `get_customer_risk_context` - summarize bounded transaction and assessment context.
- `detect_transaction_anomalies` - identify evidence-backed anomalies in recent transactions.
- `explain_risk` - explain the recorded features and signals behind an assessment.
- `check_device` - evaluate a customer/device pair against known device evidence.
- `check_blacklist` - check a normalized entity against blacklist evidence.
- `create_fraud_alert` - create an alert from an assessment that meets the threshold.
- `get_fraud_alert` - retrieve one persisted fraud alert.
- `get_fraud_alerts` - search bounded alerts by customer, status, or severity.
- `update_fraud_alert_status` - move an alert through its controlled status workflow.

### Case MCP - 23 tools

- `create_case` - create a persistent investigation case.
- `create_case_from_fraud_alert` - create an idempotent case grounded in a Fraud alert.
- `get_case` - retrieve detailed case context.
- `get_case_status` - retrieve compact workflow and approval status.
- `search_cases` - search bounded cases using structured filters.
- `update_case` - update editable fields through the case state machine.
- `assign_case` - assign a case to an investigator or team identifier.
- `resolve_case` - resolve a case with recorded resolution evidence.
- `close_case` - close an eligible resolved case.
- `add_case_note` - append an attributed investigation note.
- `get_case_history` - retrieve chronological immutable case history.
- `request_approval` - request approval for a sensitive simulated bank action.
- `approve_action` - record an authorized human approval decision.
- `reject_action` - reject a pending sensitive action without executing it.
- `get_card_status` - retrieve the synthetic card-control state.
- `freeze_card` - execute an exactly matching approved freeze action.
- `unfreeze_card` - execute an exactly matching approved unfreeze action.
- `block_card` - execute an exactly matching approved terminal block action.
- `send_customer_notification` - add a customer notification to the persistent outbox.
- `send_email` - add a simulated email notification to the outbox.
- `send_sms` - add a simulated SMS notification to the outbox.
- `generate_case_summary` - generate a deterministic summary from stored evidence.
- `get_audit_trail` - retrieve ordered append-only audit events.

## Required database setup

Before creating the Render service, open the Supabase SQL Editor and run these files in this order:

1. `fraudMCP/app/database/migrations/001_fraud_mcp.sql`
2. `case/app/database/migrations/001_case_mcp.sql`

Both migrations are non-destructive and may be run again. Alternatively, set either `SUPABASE_DB_URL` or a local-only `SUPABASE_ACCESS_TOKEN`, then run `python -m scripts.migrate_all` from this directory. Do not put either administrative credential in Render when `MCP_AUTO_MIGRATE=false`.

## Render Web Service

1. Push the repository to GitHub.
2. In Render, choose **New > Blueprint**, select the repository, and set the Blueprint path to `mcp/render.yaml`. It creates exactly one service with type `web`.
3. Enter the secret environment values requested by the blueprint: `PLAID_CLIENT_ID`, `PLAID_SECRET`, `SUPABASE_URL`, and `SUPABASE_SECRET_KEY`.
4. Render generates `MCP_AUTH_TOKEN`. Copy its value from the service environment page into every MCP client that calls this service.
5. Deploy and wait for `/ready` to return HTTP 200.
6. Set Plaid's webhook URL to `https://YOUR-SERVICE.onrender.com/webhooks/plaid`, then redeploy if you also set `PLAID_WEBHOOK_URL` in Render.

The three MCP client URLs are:

```text
https://YOUR-SERVICE.onrender.com/mcp/banking
https://YOUR-SERVICE.onrender.com/mcp/fraud
https://YOUR-SERVICE.onrender.com/mcp/case
```

Each MCP request must include `Authorization: Bearer <MCP_AUTH_TOKEN>`.

## Local verification

From `mcp/`:

```bash
python -m pip install --user -e ".[dev]"
python -m pytest -p no:cacheprovider
python -m scripts.smoke_test_all
python -m uvicorn app:create_app --factory --host 0.0.0.0 --port 8000 --workers 1
```

## Docker

From the repository root:

```bash
docker build -f mcp/Dockerfile -t thinkfive-mcp mcp
docker run --rm --env-file mcp/.env -p 8000:8000 thinkfive-mcp
```

The Dockerfile selectively copies source files and never copies `.env`. Plaid Sandbox data is reconstructed on restart when `PLAID_AUTO_BOOTSTRAP=true`; Fraud assessments, Fraud alerts, and all Case workflow records persist in Supabase.
