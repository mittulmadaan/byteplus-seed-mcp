FROM python:3.11-slim
WORKDIR /app

COPY packages/seed-sdk ./packages/seed-sdk
COPY packages/seed-mcp ./packages/seed-mcp

RUN pip install --no-cache-dir \
    ./packages/seed-sdk \
    ./packages/seed-mcp

ENV MCP_TRANSPORT=sse
EXPOSE 8000
CMD ["python", "-m", "seed_mcp"]
