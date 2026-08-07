"""Smoke test - complete user journey validation against a running backend.

Run with the backend already started (locally or in Docker) and
MCP services reachable. Prints PASS/FAIL for each stage; never fakes results.
"""

from __future__ import annotations

import asyncio
import logging
import sys

import httpx

logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:8000"

RESULTS: list[tuple[str, bool, str]] = []


def record(name: str, passed: bool, detail: str = "") -> None:
    RESULTS.append((name, passed, detail))
    status = "PASS" if passed else "FAIL"
    print(f"{name:.<40}{status} {detail}")


async def run_smoke_test() -> bool:
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
        # 1. Health
        try:
            resp = await client.get("/health")
            record("Health check", resp.status_code == 200)
        except Exception as e:
            record("Health check", False, str(e))
            return False

        # 2. Readiness
        try:
            resp = await client.get("/ready")
            body = resp.json()
            record("Readiness check", resp.status_code == 200 and body.get("status") == "ready", str(body))
        except Exception as e:
            record("Readiness check", False, str(e))

        # 3. Customer login
        try:
            resp = await client.post("/api/auth/login", json={"email": "demo@thinkfive.ai", "password": "demo"})
            passed = resp.status_code == 200
            record("Customer login", passed)
            cookies = resp.cookies if passed else None
        except Exception as e:
            record("Customer login", False, str(e))
            cookies = None

        if cookies is None:
            record("Remaining customer journey", False, "skipped - login failed")
            return False

        client.cookies.update(cookies)

        # 4. Start conversation / banking question
        conversation_id = None
        try:
            resp = await client.post("/api/chat", json={"message": "What is my account balance?"})
            passed = resp.status_code == 200
            body = resp.json() if passed else {}
            conversation_id = body.get("conversation_id")
            record("Chat submission (banking)", passed, str(body))
        except Exception as e:
            record("Chat submission (banking)", False, str(e))

        # 5. SSE connectivity check (best-effort, short read)
        if conversation_id:
            try:
                async with client.stream("GET", f"/api/events?conversation_id={conversation_id}") as stream:
                    got_event = False
                    async for line in stream.aiter_lines():
                        if line.startswith("event:"):
                            got_event = True
                            break
                    record("SSE connects", got_event)
            except Exception as e:
                record("SSE connects", False, str(e))

        # 6. Analyst login + pending approvals visibility
        try:
            analyst_client = httpx.AsyncClient(base_url=BASE_URL, timeout=30.0)
            resp = await analyst_client.post(
                "/api/auth/login", json={"email": "analyst@thinkfive.ai", "password": "demo"}
            )
            passed = resp.status_code == 200
            record("Analyst login", passed)
            if passed:
                analyst_client.cookies.update(resp.cookies)
                pending_resp = await analyst_client.get("/api/approvals/pending")
                record("Analyst pending approvals visibility", pending_resp.status_code == 200)
            await analyst_client.aclose()
        except Exception as e:
            record("Analyst login", False, str(e))

    total = len(RESULTS)
    passed_count = sum(1 for _, p, _ in RESULTS if p)
    print(f"\nOverall: {passed_count}/{total} checks passed")
    return passed_count == total


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
    success = asyncio.run(run_smoke_test())
    sys.exit(0 if success else 1)
