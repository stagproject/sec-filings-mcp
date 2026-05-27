# Glama Dockerfile builder — build steps (sec-filings-mcp)

Glama does **not** use the repo `Dockerfile` directly. It generates an image from the Admin → **Dockerfile** form. The base layer already installs `uv` (see generated Dockerfile step 2).

## Common build failure: `pip: not found`

**Cause:** Build steps include `pip install uv`, but Glama’s Debian image has **no `pip`** (only `uv` from the install script).

**Fix:** Remove `pip install uv`. Use `uv` directly.

## Recommended form values

| Field | Value |
|-------|--------|
| Base image | `debian:trixie-slim` |
| Python version | `3.14` |
| Node.js | default (used for `mcp-proxy`) |
| **Build steps** | see JSON below |
| **CMD arguments** | leave as Glama preview (`mcp-proxy` + `python mcp_server_finance.py --sse`) |
| Pinned SHA | empty (latest `main`) or current head |

### Build steps (copy into Glama)

```json
[
  "apt-get update && apt-get install -y --no-install-recommends build-essential git libgmp-dev autoconf automake libtool pkg-config python3-dev",
  "uv sync --frozen --no-cache"
]
```

Do **not** include `pip install uv`.

### Placeholder parameters

Must match **Environment variables JSON schema** `required` keys. Example:

```json
{
  "SUPABASE_URL": "https://placeholder.supabase.co",
  "SUPABASE_SERVICE_ROLE_KEY": "placeholder-service-role-key",
  "X402_KEY": "placeholder-for-glama-health-check-only",
  "PORT": "8080"
}
```

Use dummy values only — never production secrets.

### Environment schema note

Runtime code uses `HMAC_SECRET` for x402, not `X402_KEY`. Glama’s `X402_KEY` is only to satisfy the health-check form; production uses Cloud Run env (see `.env.example`).

## After changing build steps

1. Save the form and confirm the preview Dockerfile has **no** `pip install`.
2. **Build** (test), then **Build & Release**.
3. **Repository** → **Sync Server** if the pinned SHA is old.

## Production traffic

Users connect via **xpay**, not Glama hosting:

`https://sec-edgar-filings.mcp.xpay.sh/mcp?key=YOUR_XPAY_KEY`

Glama build success improves directory score/verification; it does not replace Cloud Run + xpay.
