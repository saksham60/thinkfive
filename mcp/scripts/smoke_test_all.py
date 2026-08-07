from __future__ import annotations

import asyncio
from typing import Any

import httpx
import uvicorn
from fastmcp import Client

from app import create_app
from tests.conftest import banking_settings, case_settings, combined_settings, configured_plaid, fraud_settings

HOST = "127.0.0.1"
PORT = 8766
TOKEN = "combined-test-token"


def payload(result: Any) -> Any:
    value = result.structured_content or {}
    if "result" in value:
        value = value["result"]
    if not isinstance(value, dict) or not value.get("success"):
        raise RuntimeError(f"MCP tool failed safely: {value}")
    return value.get("data")


async def main() -> None:
    app = create_app(
        combined_settings=combined_settings(TOKEN),
        banking_settings=banking_settings(),
        fraud_settings=fraud_settings(),
        case_settings=case_settings(),
        plaid=configured_plaid(),
        force_memory=True,
    )
    server = uvicorn.Server(uvicorn.Config(app, host=HOST, port=PORT, log_level="warning"))
    server_task = asyncio.create_task(server.serve())
    results: list[tuple[str, bool]] = []

    async def check(name: str, operation: Any) -> Any:
        try:
            value = await operation
            results.append((name, True))
            return value
        except Exception:
            results.append((name, False))
            return None

    try:
        for _ in range(100):
            if server.started:
                break
            await asyncio.sleep(0.05)
        if not server.started:
            raise RuntimeError("Combined application did not start")
        results.append(("Combined application startup", True))

        async with httpx.AsyncClient(base_url=f"http://{HOST}:{PORT}") as http:
            health = await check("Health endpoint", http.get("/health"))
            ready = await check("Readiness endpoint", http.get("/ready"))
            results[-2] = (results[-2][0], bool(health and health.status_code == 200))
            results[-1] = (results[-1][0], bool(ready and ready.status_code == 200))

        async with (
            Client(f"http://{HOST}:{PORT}/mcp/banking/", auth=TOKEN) as banking,
            Client(f"http://{HOST}:{PORT}/mcp/fraud/", auth=TOKEN) as fraud,
            Client(f"http://{HOST}:{PORT}/mcp/case/", auth=TOKEN) as case,
        ):
            banking_tools = await check("Banking MCP initialize / tools/list", banking.list_tools())
            fraud_tools = await check("Fraud MCP initialize / tools/list", fraud.list_tools())
            case_tools = await check("Case MCP initialize / tools/list", case.list_tools())
            results[-3] = (results[-3][0], len(banking_tools or []) == 15)
            results[-2] = (results[-2][0], len(fraud_tools or []) == 11)
            results[-1] = (results[-1][0], len(case_tools or []) == 23)

            accounts = payload(await banking.call_tool("get_accounts", {"customer_id": "demo_customer_001"}))
            results.append(("Plaid customer / accounts", bool(accounts)))
            payload(await banking.call_tool("sync_transactions", {"customer_id": "demo_customer_001"}))
            transactions = payload(await banking.call_tool("get_recent_transactions", {"customer_id": "demo_customer_001", "limit": 100}))
            target = next(item for item in transactions if item["transaction_id"] == "tx-suspicious")
            results.append(("Transactions", True))

            assessment = payload(
                await fraud.call_tool(
                    "assess_transaction_risk",
                    {"customer_id": "demo_customer_001", "transaction_id": target["transaction_id"]},
                )
            )
            results.append(("Fraud assessment / evidence", assessment["transaction_id"] == target["transaction_id"] and bool(assessment["evidence"])))
            alert = payload(
                await fraud.call_tool(
                    "create_fraud_alert",
                    {"assessment_id": assessment["assessment_id"], "customer_id": "demo_customer_001"},
                )
            )
            results.append(("Fraud alert", alert["assessment_id"] == assessment["assessment_id"]))

            workflow = payload(await case.call_tool("create_case_from_fraud_alert", {"fraud_alert_id": alert["alert_id"]}))
            results.append(("Case creation", workflow["fraud_alert_id"] == alert["alert_id"]))
            payload(await case.call_tool("assign_case", {"case_id": workflow["case_id"], "assignee": "fraud_team_demo"}))
            results.append(("Case assignment", True))
            payload(
                await case.call_tool(
                    "add_case_note",
                    {"case_id": workflow["case_id"], "content": "Combined endpoint smoke evidence reviewed.", "author_id": "agent_demo"},
                )
            )
            results.append(("Case note", True))
            approval = payload(
                await case.call_tool(
                    "request_approval",
                    {
                        "case_id": workflow["case_id"],
                        "action_type": "FREEZE_CARD",
                        "action_payload": {"card_id": "card_demo_001"},
                        "requested_by": "agent_demo",
                        "idempotency_key": f"smoke:{workflow['case_id']}",
                    },
                )
            )
            results.append(("Approval request", approval["status"] == "PENDING"))
            before = payload(await case.call_tool("get_card_status", {"customer_id": "demo_customer_001", "card_id": "card_demo_001"}))
            results.append(("Pre-approval card protection", before["status"] == "ACTIVE"))
            approved = payload(
                await case.call_tool(
                    "approve_action",
                    {"approval_id": approval["approval_id"], "reviewed_by": "human_reviewer_demo"},
                )
            )
            results.append(("Human approval", approved["status"] == "APPROVED"))
            frozen = payload(
                await case.call_tool(
                    "freeze_card",
                    {"case_id": workflow["case_id"], "approval_id": approval["approval_id"], "card_id": "card_demo_001"},
                )
            )
            results.append(("Card action", frozen["status"] == "FROZEN"))
            notification = payload(
                await case.call_tool(
                    "send_customer_notification",
                    {"case_id": workflow["case_id"], "channel": "IN_APP", "content": "Your synthetic demo card was secured."},
                )
            )
            results.append(("Notification outbox", notification["provider"] == "SUPABASE_OUTBOX"))
            summary = payload(await case.call_tool("generate_case_summary", {"case_id": workflow["case_id"]}))
            history = payload(await case.call_tool("get_audit_trail", {"case_id": workflow["case_id"]}))
            results.append(("Case summary", bool(summary["structured_summary"])))
            results.append(("Audit trail", len(history) >= 8))
            payload(
                await case.call_tool(
                    "resolve_case",
                    {
                        "case_id": workflow["case_id"],
                        "resolution": "Combined endpoint smoke completed.",
                        "resolved_by": "human_reviewer_demo",
                    },
                )
            )
            results.append(("Resolution", True))
            serialized = str([assessment, alert, workflow, notification, summary])
            results.append(("Secret leakage check", all(secret not in serialized for secret in ("combined-secret-value", "combined-test-service-key", TOKEN))))
    finally:
        server.should_exit = True
        await server_task

    for name, passed in results:
        print(f"{name:.<48} {'PASS' if passed else 'FAIL'}")
    overall = all(passed for _, passed in results)
    print(f"{'Overall deployment smoke':.<48} {'PASS' if overall else 'FAIL'}")
    raise SystemExit(0 if overall else 1)


if __name__ == "__main__":
    asyncio.run(main())
