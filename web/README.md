# SentinelBank AI – AI-Powered Banking Customer Query Resolution & Fraud Alert System

**SentinelBank AI** is a regional-finals demonstration prototype of an enterprise-grade AI banking assistant, agentic LangGraph workflow orchestrator, fraud engine with risk analytics, MCP tool servers, PII masking, and human-in-the-loop analyst dashboard.

> ⚠️ **Synthetic Data Notice**: This application operates exclusively on synthetic data and isolated mock backend services. It does not connect to real banking systems, payment networks, customer accounts, or production credentials.

---

## 🌟 Key Functional Highlights

1. **AI Banking Chat**:
   - Customer-facing conversational concierge.
   - LangGraph Supervisor Agent detects intent across 7 categories (`account_query`, `transaction_query`, `fraud_report`, `card_issue`, `policy_question`, `complaint`, `unknown`).
   - RAG Policy Grounding via LlamaIndex-style hybrid policy search with citations.

2. **Multi-Factor Fraud Engine**:
   - **Rule Engine**: Evaluates amount multipliers (e.g. 55x historical average), unrecognized new device fingerprints, location/IP geo-mismatches, velocity spikes, and travel notice matches.
   - **XGBoost ML Classifier**: Synthetic machine learning risk scoring.
   - **Isolation Forest Anomaly Index**: Anomaly score index.
   - **Graph Network Analytics**: Customer-Device-IP-Merchant relationship graph detecting shared device clusters and fraud ring patterns.

3. **Three Model Context Protocol (MCP) Servers**:
   - **Banking MCP Server**: `get_customer_profile`, `get_account_summary`, `get_transaction`, `get_recent_transactions`, `get_card_status`, `freeze_card`.
   - **Fraud MCP Server**: `get_active_alerts`, `calculate_fraud_score`, `get_device_risk`, `get_related_entities`, `get_customer_risk_profile`, `get_fraud_evidence`.
   - **Case MCP Server**: `create_case`, `update_case`, `assign_case`, `add_case_note`, `request_approval`, `send_customer_notification`.

4. **Security & Guardrails**:
   - **Presidio PII Masking**: Automatically masks 16-digit credit cards, SSNs, CVVs, PINs, and full account numbers.
   - **Prompt Injection Defense**: Filters and blocks unauthorized instructions to override system rules or bypass approval steps.

5. **Human-in-the-Loop Analyst Dashboard**:
   - Real-time fraud alert stream powered by WebSockets.
   - Explainable multi-score breakdown (ML, Rules, Anomaly, Graph).
   - Interactive SVG Entity Network Graph.
   - 1-Click Analyst Approval modal for high-impact card freezing with audit log emission.

6. **Supervisor Command Center & Golden Eval Suite**:
   - Live system metrics (Total conversations, Auto-resolution rate %, Open alerts, SLA response times).
   - Real-time Audit Log Table with search and filtering.
   - Synthetic Event Simulator (inject Stolen Card Fraud, Fraud Ring, or Travel False Positive scenarios).
   - Golden Evaluation Suite runner (6 automated security & functional tests).

---

## 🚀 Demonstration Flow

1. **Customer View**: Click on the pre-built prompt *"Report $2,499.99 charge from Luxure Electronics"*. Watch the Supervisor Agent route the message, run the Fraud Engine, detect a Critical Risk (94/100), open a Case, and explain the Regulation E Zero Liability policy.
2. **Analyst Hub**: Switch to the **Analyst Hub** tab. Notice the new critical alert in the live stream. Click on it to inspect the multi-score breakdown, risk reasons, and entity network graph.
3. **Human Approval**: Click **Approve Card Freeze**. Sign the analyst identity signature and submit. Notice the card freeze execution via `BankingMCP:freeze_card` and customer SMS notification.
4. **Supervisor Command Center**: Switch to **Supervisor Dashboard** to view the updated SLA metrics, chart, and immutable audit logs.
5. **Golden Eval Suite**: Switch to **Agents & Eval** to run the 6 automated security & safety benchmark tests.

---

## 🛠️ Architecture

```
React/Next.js Frontend (Vite + Tailwind)
        ↓
Express API Gateway & WebSockets (Port 3000)
        ↓
Guardrails AI & Presidio PII Masking
        ↓
LangGraph Supervisor Agent
        ↓
Specialized Subgraphs (Support, Fraud & Risk, Knowledge RAG, Case)
        ↓
MCP Gateway (Banking MCP, Fraud MCP, Case MCP)
        ↓
Synthetic Banking Database Store
```

---

## ⚡ Getting Started

```bash
# Install dependencies
npm install

# Run dev server (Express + Vite + WebSockets on port 3000)
npm run dev

# Run linting
npm run lint

# Build production bundle
npm run build
```
