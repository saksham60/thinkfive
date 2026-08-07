from __future__ import annotations

import asyncio
import json
import os
from dataclasses import dataclass
from typing import Any

from fastmcp import Client


def _is_true(value: str | None) -> bool:
    return bool(value and value.strip().casefold() in {"1", "true", "yes", "on"})


@dataclass
class CheckResult:
    name: str
    passed: bool
    details: str = ""


def _print_check(check: CheckResult) -> None:
    status = "PASS" if check.passed else "FAIL"
    print(f"{check.name:.<34} {status}")
    if check.details:
        print(f"  {check.details}")


def _extract_payload(result: Any) -> dict[str, Any]:
    if isinstance(result, dict):
        return result
    if hasattr(result, "data") and isinstance(result.data, dict):
        return result.data
    if hasattr(result, "content"):
        content = result.content
        if isinstance(content, list):
            for item in content:
                text = item.text if hasattr(item, "text") else None
                if isinstance(text, str):
                    try:
                        parsed = json.loads(text)
                    except json.JSONDecodeError:
                        continue
                    if isinstance(parsed, dict):
                        return parsed
    raise RuntimeError("Unable to parse MCP tool response payload")


async def _call(client: Client, tool: str, args: dict[str, Any]) -> dict[str, Any]:
    result = await client.call_tool(tool, args, raise_on_error=False)
    payload = _extract_payload(result)
    if payload.get("success") is False:
        code = payload.get("error_code", "UNKNOWN_ERROR")
        message = payload.get("message", "Unknown error")
        raise RuntimeError(f"{tool} failed with {code}: {message}")
    return payload


async def main() -> int:
    fraud_url = os.getenv("FRAUD_MCP_URL", "http://localhost:8002/mcp").strip()
    banking_url = os.getenv("BANKING_MCP_URL", "http://localhost:8001/mcp").strip()
    customer_id = os.getenv("PLAID_DEFAULT_CUSTOMER_ID", "demo_customer_001")

    fraud_token = os.getenv("MCP_AUTH_TOKEN") or None
    banking_token = os.getenv("BANKING_MCP_AUTH_TOKEN") or None

    checks: list[CheckResult] = []

    config_ok = bool(fraud_url and banking_url and customer_id)
    checks.append(CheckResult("Configuration", config_ok, f"fraud_url={fraud_url}, banking_url={banking_url}, customer_id={customer_id}"))
    if not config_ok:
        for item in checks:
            _print_check(item)
        print("Overall.............................. FAIL")
        return 1

    try:
        async with Client(banking_url, auth=banking_token, timeout=15) as banking_client:
            accounts = await _call(banking_client, "get_accounts", {"customer_id": customer_id})
            checks.append(CheckResult("Banking MCP connection", True, f"accounts={len(accounts.get('data', []))}"))

            recent = await _call(banking_client, "get_recent_transactions", {"customer_id": customer_id, "limit": 20})
            transactions = recent.get("data", [])
            if not isinstance(transactions, list) or not transactions:
                checks.append(CheckResult("Customer context", False, "No recent transactions returned"))
                for item in checks:
                    _print_check(item)
                print("Overall.............................. FAIL")
                return 1
            checks.append(CheckResult("Customer context", True, f"recent_transactions={len(transactions)}"))

            selected = transactions[0]
            suspicious = max(transactions, key=lambda item: float(item.get("amount") or 0.0))

        async with Client(fraud_url, auth=fraud_token, timeout=20) as fraud_client:
            assessment = await _call(
                fraud_client,
                "assess_transaction_risk",
                {
                    "customer_id": customer_id,
                    "transaction_id": selected["transaction_id"],
                    "channel": "smoke_test",
                },
            )
            assessment_data = assessment.get("data", {})
            checks.append(
                CheckResult(
                    "Risk assessment",
                    True,
                    f"score={assessment_data.get('risk_score')}, severity={assessment_data.get('severity')}",
                )
            )
            checks.append(CheckResult("Evidence generation", bool(assessment_data.get("evidence"))))

            explanation = await _call(fraud_client, "explain_risk", {"assessment_id": assessment_data["assessment_id"], "customer_id": customer_id})
            checks.append(CheckResult("Risk explanation", bool(explanation.get("data", {}).get("summary"))))

            suspicious_assessment = await _call(
                fraud_client,
                "assess_transaction_risk",
                {
                    "customer_id": customer_id,
                    "transaction_id": suspicious["transaction_id"],
                    "device_id": "device_primary",
                    "ip_address": "203.0.113.50",
                    "channel": "smoke_test",
                },
            )
            suspicious_data = suspicious_assessment.get("data", {})

            alert_payload: dict[str, Any] | None = None
            if float(suspicious_data.get("risk_score", 0.0)) >= float(os.getenv("FRAUD_ALERT_THRESHOLD", "0.65")):
                alert = await _call(
                    fraud_client,
                    "create_fraud_alert",
                    {
                        "assessment_id": suspicious_data["assessment_id"],
                        "customer_id": customer_id,
                    },
                )
                alert_payload = alert.get("data", {})
                checks.append(CheckResult("Fraud alert", True, f"alert_id={alert_payload.get('alert_id')}"))
            else:
                checks.append(CheckResult("Fraud alert", True, "suspicious transaction did not exceed threshold"))

            if alert_payload and alert_payload.get("alert_id"):
                alert_id = str(alert_payload["alert_id"])
                retrieved = await _call(fraud_client, "get_fraud_alert", {"alert_id": alert_id, "customer_id": customer_id})
                checks.append(CheckResult("Alert retrieval", bool(retrieved.get("data", {}).get("alert_id"))))

                updated = await _call(
                    fraud_client,
                    "update_fraud_alert_status",
                    {
                        "alert_id": alert_id,
                        "status": "INVESTIGATING",
                        "note": "smoke test update",
                        "customer_id": customer_id,
                    },
                )
                checks.append(CheckResult("Alert lifecycle", updated.get("data", {}).get("status") == "INVESTIGATING"))
            else:
                checks.append(CheckResult("Alert retrieval", True, "no alert created"))
                checks.append(CheckResult("Alert lifecycle", True, "no alert created"))

            alerts = await _call(fraud_client, "get_fraud_alerts", {"customer_id": customer_id, "limit": 10})
            checks.append(CheckResult("Fraud alerts listing", isinstance(alerts.get("data", {}).get("results"), list)))

            checks.append(
                CheckResult(
                    "No unauthorized bank action",
                    "case" not in json.dumps(suspicious_data).casefold()
                    and "freeze" not in json.dumps(suspicious_data).casefold()
                    and "block" not in json.dumps(suspicious_data).casefold(),
                )
            )

    except Exception as exc:
        checks.append(CheckResult("Execution", False, str(exc)))

    passed = True
    for item in checks:
        _print_check(item)
        if not item.passed:
            passed = False

    print(f"Overall.............................. {'PASS' if passed else 'FAIL'}")
    return 0 if passed else 1


if __name__ == "__main__":
    try:
        raise SystemExit(asyncio.run(main()))
    except KeyboardInterrupt:
        raise SystemExit(130) from None
