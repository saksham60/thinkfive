FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PORT=8000
WORKDIR /opt/thinkfive/mcp

COPY pyproject.toml README.md ./
COPY app.py config.py migrations.py providers.py ./
COPY common ./common
COPY plaidbanking/app ./plaidbanking/app
COPY plaidbanking/__init__.py ./plaidbanking/__init__.py
COPY fraudMCP/app ./fraudMCP/app
COPY fraudMCP/data ./fraudMCP/data
COPY fraudMCP/__init__.py ./fraudMCP/__init__.py
COPY case/app ./case/app
COPY case/__init__.py ./case/__init__.py

RUN pip install --no-cache-dir .

USER 65532:65532
CMD ["sh", "-c", "python -m uvicorn app:create_app --factory --host 0.0.0.0 --port ${PORT} --workers 1"]
