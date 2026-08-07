from __future__ import annotations

import asyncio

from case.app.config import Settings
from case.app.container import create_container
from case.app.models.domain import CardState


class Banking:
    async def get_transaction(self, c: str, t: str):
        return {"customer_id": c, "transaction_id": t}

    async def get_accounts(self, c: str):
        return []

    get_account_summary = get_accounts
    get_customer_identity = get_accounts


class Fraud:
    async def get_fraud_alert(self, a: str):
        return {"alert_id": a, "customer_id": "demo_customer_001", "transaction_id": "tx_demo", "assessment_id": "assessment_demo", "severity": "HIGH"}

    async def get_risk_assessment(self, a: str):
        return {"assessment_id": a}

    async def get_fraud_alerts(self, **kwargs):
        return []


async def main() -> None:
    s = Settings(_env_file=None, SUPABASE_URL="https://test.invalid", SUPABASE_SECRET_KEY="test", CASE_REPOSITORY_BACKEND="memory")
    c = create_container(s, memory=True, banking=Banking(), fraud=Fraud())
    results = []

    async def check(name, op):
        try:
            v = await op()
            results.append((name, True))
            return v
        except Exception:
            results.append((name, False))
            return None

    await c.cards.upsert(CardState(card_id="card_demo_001", customer_id="demo_customer_001"))
    case = await check("Fraud alert linkage / case creation", lambda: c.case.from_alert("alert_demo"))
    await check("Assignment", lambda: c.case.assign(case.case_id, "fraud_team_demo"))
    await check("Investigation note", lambda: c.case.note(case.case_id, "Investigated synthetic alert."))
    approval = await check("Approval requested", lambda: c.approval.request(case.case_id, "FREEZE_CARD", {"card_id": "card_demo_001"}, "agent_demo"))
    results.append(("No pre-approval action", str((await c.cards.get("card_demo_001")).status) == "ACTIVE"))
    await check("Human approval", lambda: c.approval.approve(approval.approval_id, "human_reviewer_demo"))
    await check("Approved freeze action", lambda: c.actions.execute(case.case_id, approval.approval_id, "card_demo_001", "FREEZE_CARD"))
    results.append(("Card frozen", str((await c.cards.get("card_demo_001")).status) == "FROZEN"))
    await check("In-app notification", lambda: c.notification.send(case.case_id, "IN_APP", "Your synthetic card was frozen."))
    await check("Email outbox", lambda: c.notification.send(case.case_id, "EMAIL", "Fraud investigation update", "Account update"))
    await check("SMS outbox", lambda: c.notification.send(case.case_id, "SMS", "Fraud investigation update"))
    await check("Case summary", lambda: c.summary.generate(case.case_id))
    await check("Resolution", lambda: c.case.resolve(case.case_id, "Synthetic review completed.", "human_reviewer_demo"))
    await check("Close", lambda: c.case.close(case.case_id, "human_reviewer_demo"))
    await check("Audit trail", lambda: c.case.history(case.case_id))
    for n, p in results:
        print(f"{n:.<42} {'PASS' if p else 'FAIL'}")
    ok = all(p for _, p in results)
    print(f"{'Overall':.<42} {'PASS' if ok else 'FAIL'}")
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    asyncio.run(main())
