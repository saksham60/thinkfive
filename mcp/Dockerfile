FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PORT=8000
WORKDIR /opt/thinkfive/mcp

COPY mcp/pyproject.toml mcp/README.md ./
COPY mcp/app.py mcp/config.py mcp/migrations.py mcp/providers.py ./
COPY mcp/common ./common
COPY mcp/plaidbanking/app ./plaidbanking/app
COPY mcp/plaidbanking/__init__.py ./plaidbanking/__init__.py
COPY mcp/fraudMCP/app ./fraudMCP/app
COPY mcp/fraudMCP/data ./fraudMCP/data
COPY mcp/fraudMCP/__init__.py ./fraudMCP/__init__.py
COPY mcp/case/app ./case/app
COPY mcp/case/__init__.py ./case/__init__.py

RUN pip install --no-cache-dir .

USER 65532:65532
CMD ["sh", "-c", "python -m uvicorn app:create_app --factory --host 0.0.0.0 --port ${PORT} --workers 1"]
