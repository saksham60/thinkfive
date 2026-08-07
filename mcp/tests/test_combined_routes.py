from __future__ import annotations

from httpx import ASGITransport, AsyncClient


async def test_combined_health_ready_routes_and_webhook(combined_app):
    async with combined_app.router.lifespan_context(combined_app):
        async with AsyncClient(transport=ASGITransport(app=combined_app), base_url="http://combined") as client:
            health = await client.get("/health")
            ready = await client.get("/ready")
            webhook = await client.post("/webhooks/plaid", content=b"{}")
            for path in ("/mcp/banking/", "/mcp/fraud/", "/mcp/case/"):
                unauthenticated = await client.post(path, json={})
                authenticated = await client.post(path, json={}, headers={"Authorization": "Bearer combined-test-token"})
                assert unauthenticated.status_code == 401
                assert authenticated.status_code != 401
            assert health.status_code == 200
            assert health.json() == {"status": "ok", "services": {"banking": "ok", "fraud": "ok", "case": "ok"}}
            assert ready.status_code == 200
            assert ready.json()["status"] == "ready"
            assert webhook.status_code == 401
            assert webhook.json()["accepted"] is False
            assert health.headers["x-request-id"]


def test_one_process_uses_local_provider_objects(combined_app):
    assert combined_app.state.provider_mode == "local"
    assert combined_app.state.fraud.banking_provider.banking is combined_app.state.banking
    assert combined_app.state.case.banking.banking.banking is combined_app.state.banking
    assert combined_app.state.case.fraud.fraud is combined_app.state.fraud
