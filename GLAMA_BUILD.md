# Glama Dockerfile builder — build steps (sec-filings-mcp)

Glama does **not** use the repo `Dockerfile` directly. It generates an image from the Admin → **Dockerfile** form. The base layer already installs `uv` (see generated Dockerfile step 2).

## Common build failures

### 1. `pip: not found`

**Cause:** Build steps include `pip install uv`, but Glama’s Debian image has **no `pip`** (only `uv` from the install script).

**Fix:** Remove `pip install uv`. Use `uv` directly.

### 2. `No module named 'uvicorn'`

**Cause:** CMD uses bare `python` instead of the venv created by `uv sync`.

**Fix:** Use `/app/.venv/bin/python` in CMD.

### 3. `GET /ping HTTP/1.1 404` → Request timed out

**Cause:** Glama runs `mcp-proxy`, which expects the child process to speak **MCP over stdio**. With `--sse`, the server starts **Streamable HTTP (uvicorn)** on port 8080 instead. `mcp-proxy` never gets JSON-RPC on stdin and times out after 60s. Glama may also probe `GET /ping`, which HTTP mode did not expose (fixed in repo `main` via `/ping` route — still use stdio for Glama).

**Fix:** **Remove `--sse` from CMD arguments** for Glama builds only.

| Deployment | CMD |
|------------|-----|
| **Glama verify** | `mcp-proxy` + venv python + **no `--sse`** (stdio) |
| **Cloud Run / xpay** | venv python + **`--sse`** (HTTP `/mcp`) |

## Recommended form values

| Field | Value |
|-------|--------|
| Base image | `debian:trixie-slim` |
| Python version | `3.14` |
| Node.js | default (used for `mcp-proxy`) |
| **Build steps** | see JSON below |
| **CMD arguments** | stdio (no `--sse`) — see below |
| Pinned SHA | empty (latest `main`) or current head |

### Build steps

```json
[
  "apt-get update && apt-get install -y --no-install-recommends build-essential git libgmp-dev autoconf automake libtool pkg-config python3-dev",
  "uv sync --frozen --no-cache"
]
```

Do **not** include `pip install uv`.

### CMD arguments (Glama — stdio for mcp-proxy)

```json
[
  "mcp-proxy",
  "--",
  "/app/.venv/bin/python",
  "mcp_server_finance.py"
]
```

**Do not pass `--sse`** on Glama. Production Cloud Run uses `--sse` in the repo `Dockerfile` instead.

### Placeholder parameters

```json
{
  "SUPABASE_URL": "https://placeholder.supabase.co",
  "SUPABASE_SERVICE_ROLE_KEY": "placeholder-service-role-key",
  "X402_KEY": "placeholder-for-glama-health-check-only",
  "PORT": "8080"
}
```

Dummy values only — never production secrets.

## After changing settings

1. Save the form; preview CMD must **not** include `--sse`.
2. **Build**, then **Build & Release**.
3. **Repository** → **Sync Server** so Glama clones latest `main` (includes `/ping` for HTTP probes).

## Production traffic

Users connect via **xpay**, not Glama hosting:

`https://sec-edgar-filings.mcp.xpay.sh/mcp?key=YOUR_XPAY_KEY`

Glama build success improves directory score/verification; it does not replace Cloud Run + xpay.
