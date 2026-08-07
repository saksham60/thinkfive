# ThinkFive Backend

AI-powered banking customer query resolution and fraud-alert platform.

## Architecture

### Clean Architecture Layers

```
API (FastAPI) 
    ↓
Application (Use Cases)
    ↓
Domain (Entities, Ports)
    ↑
Infrastructure (Adapters, Repositories)
```

### Agent Structure

Each agent lives in its own package with:
- `prompt.py` - System prompt and version
- `schemas.py` - Pydantic output schemas  
- `toolset.py` - Tool definitions and wrappers
- `agent.py` - Agent construction
- `node.py` - LangGraph node implementation

Agents:
- **Supervisor** - Routes and orchestrates
- **Banking** - Banking data via Banking MCP
- **Fraud** - Risk assessment via Fraud MCP
- **Knowledge** - RAG policy retrieval
- **Case** - Case management via Case MCP
- **Synthesis** - Final customer response

### Memory Model

**Three layers:**

1. **Graph Working Memory** - LangGraph checkpoints (PostgreSQL)
2. **Conversation Memory** - Persistent messages table
3. **Long-term Customer Memory** - Controlled memory storage with policy

### HITL (Human-In-The-Loop)

True LangGraph interrupt/resume flow:
1. Agent requests sensitive action (e.g., freeze card)
2. Graph interrupts and persists checkpoint
3. Run status → `WAITING_FOR_HUMAN`
4. Human analyst approves/rejects via REST API
5. Graph resumes from checkpoint with decision
6. Action executes only if approved

### MCP Integration

Three MCP adapters:
- `BankingMCPAdapter` - Plaid transactions, accounts, identity
- `FraudMCPAdapter` - Risk assessment, alerts, anomalies
- `CaseMCPAdapter` - Cases, approvals, card actions

### Security

- **Authentication**: Demo mode (cookie session) + future Supabase Auth
- **RBAC**: CUSTOMER, ANALYST, SUPERVISOR, ADMIN
- **Guardrails**: PII filtering, prompt injection protection
- **Memory Policy**: Blocks OTP, PIN, CVV, passwords from storage
- **HITL Policy**: Autonomous agents cannot freeze/block cards

### RAG

- PostgreSQL + pgvector
- Hybrid retrieval (vector + full-text)
- Citations preserved
- Prompt injection protection in Knowledge Agent

### SSE (Server-Sent Events)

Real-time updates:
- Agent progress
- Tool execution
- Fraud alerts
- Case updates  
- HITL requests
- Card state changes

Event persistence with replay support.

## Database

PostgreSQL via Supabase with:
- LangGraph checkpoints
- Conversations & messages
- Customer memories
- Agent runs & events
- Workflow interrupts
- RAG policy documents
- Transaction processing state
- Evaluation results

**Does NOT duplicate MCP-owned tables** (fraud_assessments, cases, approvals, card_states).

## Setup

```bash
# Install dependencies
pip install -e ".[dev]"

# Set environment (use provided .env)
cp ../.env .env

# Run migrations
python scripts/migrate.py

# Seed demo data
python scripts/seed_demo_data.py

# Start backend
uvicorn app.main:app --reload
```

## API Endpoints

### Chat
- `POST /api/chat` - Submit message (async, returns run_id)
- `GET /api/events` - SSE stream for conversation updates

### Customers
- `GET /api/customers/me` - Current customer profile
- `GET /api/customers/me/dashboard` - Full dashboard with accounts, alerts, cases

### Fraud
- `GET /api/alerts` - List fraud alerts
- `GET /api/alerts/{alert_id}` - Get alert details

### Cases
- `GET /api/cases` - List cases
- `GET /api/cases/{case_id}` - Get case details
- `POST /api/cases/{case_id}/notes` - Add case note

### Approvals (ANALYST+)
- `GET /api/approvals/pending` - List pending approvals
- `POST /api/approvals/{approval_id}/approve` - Approve action
- `POST /api/approvals/{approval_id}/reject` - Reject action

### Supervisor (SUPERVISOR+)
- `GET /api/supervisor/metrics` - System metrics
- `GET /api/supervisor/runs` - Agent run history
- `GET /api/system/mcp/tools` - MCP capability discovery

### Simulator (ADMIN)
- `POST /api/simulator/transaction` - Create test transaction
- `POST /api/simulator/fraud` - Trigger fraud scenario

### Health
- `GET /health` - Health check
- `GET /ready` - Readiness check

## Testing

```bash
# Unit tests
pytest tests/unit -v

# Integration tests (requires MCP services)
pytest tests/integration -v

# Smoke test (full journey)
python scripts/smoke_test.py

# All tests
pytest -v --cov=app
```

## Deployment

Single Render Web Service:
- `numInstances=1`
- `workers=1`
- Environment from `.env`
- PostgreSQL via Supabase
- No Redis required (in-process event broker)

```bash
# Build Docker
docker build -t thinkfive-backend .

# Run locally
docker run -p 8000:8000 --env-file .env thinkfive-backend
```

## Project Structure

```
backend/
├── app/
│   ├── core/              # Config, exceptions, logging
│   ├── domain/            # Entities, value objects, ports
│   ├── application/       # Use cases
│   ├── agents/            # Agent packages (each with prompt.py, schemas.py, toolset.py, agent.py, node.py)
│   ├── memory/            # Memory service, policies
│   ├── hitl/              # HITL coordinator
│   ├── mcp/               # MCP adapters
│   ├── rag/               # RAG service
│   ├── llm/               # LLM provider abstraction
│   ├── infrastructure/    # Repositories, database, embeddings
│   ├── events/            # SSE broker, publisher
│   ├── security/          # Auth, RBAC, guardrails
│   ├── api/               # FastAPI routers
│   └── evaluation/        # Evaluation framework
├── migrations/            # SQL migrations
├── scripts/               # Utility scripts
├── tests/                 # Test suite
├── Dockerfile
├── render.yaml
└── pyproject.toml
```

## Key Design Patterns

- **Repository Pattern**: Persistence abstraction
- **Adapter Pattern**: MCP clients, LLM providers
- **Strategy Pattern**: LLM/embedding provider selection
- **Factory Pattern**: Provider/agent construction
- **Policy Pattern**: Memory, HITL, authorization
- **Observer Pattern**: SSE event publishing

## Configuration

All configuration via environment variables (see `.env`).

Critical settings:
- `AUTH_MODE=demo` - Demo auth (no Supabase Auth required)
- `HITL_ENABLED=true` - Enable human-in-the-loop
- `MONITOR_ENABLED=true` - Enable transaction monitoring
- `GRAPH_MAX_ITERATIONS=15` - Max graph iterations
- `MEMORY_SUMMARY_THRESHOLD=20` - Messages before summarization

## MCP Tool Discovery

Backend discovers actual MCP tools at runtime:

```python
# GET /api/system/mcp/tools
{
  "banking": ["get_accounts", "get_transactions", ...],
  "fraud": ["assess_transaction_risk", "create_fraud_alert", ...],
  "case": ["create_case", "request_approval", "freeze_card", ...]
}
```

## Security Considerations

**Autonomous agents NEVER have access to:**
- `approve_action`
- `reject_action`
- `freeze_card`
- `unfreeze_card`
- `block_card`

These tools are available only to:
1. Human action APIs (after RBAC check)
2. After explicit approval via HITL workflow

**Memory cannot store:**
- OTP, PIN, CVV, passwords
- Access tokens, API keys
- Full card numbers
- Unverified fraud allegations as facts

## Limitations

- Single-instance deployment (no horizontal scaling yet)
- In-process SSE broker (Redis upgrade path documented)
- Demo auth mode only (Supabase Auth integration planned)
- Card actions are simulated (Case MCP state, not real Plaid)

## License

Proprietary - TCS Internal Hackathon Project
