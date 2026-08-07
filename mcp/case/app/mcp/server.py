from fastmcp import FastMCP

from case.app.container import Container

from .tools import register_cases, register_notifications, register_workflow


def create_case_mcp(c: Container) -> FastMCP:
    m = FastMCP("Case MCP", instructions="Persistent deterministic case, human approval, simulated bank-control, notification outbox and audit workflows.")
    register_cases(m, c)
    register_workflow(m, c)
    register_notifications(m, c)
    return m
