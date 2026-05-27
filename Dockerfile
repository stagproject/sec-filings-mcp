FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    libgmp-dev \
    autoconf \
    automake \
    libtool \
    pkg-config \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-cache

COPY . .

ENV PORT 8080

CMD ["/app/.venv/bin/python", "mcp_server_finance.py", "--sse"]