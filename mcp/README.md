# ThinkFive combined MCP deployment

This directory is the only production deployment boundary: one Render Web Service, one Docker image, one Python process, one port, and three independent MCP endpoints.

## Routes

- `/mcp/banking` - Plaid banking evidence
- `/mcp/fraud` - deterministic, explainable fraud analysis
- `/mcp/case` - persistent workflow and human approval
- `/webhooks/plaid` - verified Plaid webhooks
- `/health` - process liveness
- `/ready` - authentication and dependency readiness

The combined app uses direct in-process providers. `BANKING_MCP_URL`, `BANKING_MCP_AUTH_TOKEN`, `FRAUD_MCP_URL`, and `FRAUD_MCP_AUTH_TOKEN` must remain blank when `MCP_PROVIDER_MODE=local`.

## Required database setup

Before creating the Render service, open the Supabase SQL Editor and run these files in this order:

1. `fraudMCP/app/database/migrations/001_fraud_mcp.sql`
2. `case/app/database/migrations/001_case_mcp.sql`

Both migrations are non-destructive and may be run again. Alternatively, set `SUPABASE_DB_URL` locally and run `python -m scripts.migrate_all` from this directory. Do not put the database URL in Render when `MCP_AUTO_MIGRATE=false`.

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
docker build -f mcp/Dockerfile -t thinkfive-mcp .
docker run --rm --env-file mcp/.env -p 8000:8000 thinkfive-mcp
```

The Dockerfile selectively copies source files and never copies `.env`. Plaid Sandbox data is reconstructed on restart when `PLAID_AUTO_BOOTSTRAP=true`; Fraud assessments, Fraud alerts, and all Case workflow records persist in Supabase.
