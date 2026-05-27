# sec-filings-mcp

SEC EDGAR structured filing MCP for agents: **search_filings**, **get_filing_sample**, **purchase_filing**. Data lives in Supabase views (`fi_listings_portfolio`, `fi_listings_portfolio_compact`) populated by the [finance-factory](https://github.com/stagproject) pipeline.

| Read first | File |
|------------|------|
| Build / handoff | [MCP_FINANCE_BUILD.md](MCP_FINANCE_BUILD.md) |
| Env template | [.env.example](.env.example) → copy to `.env` |
| Glama | [glama.json](glama.json) (`maintainers: stagproject`) |

Template reference: `mcp_server.py` (patent MCP, unmodified). **Runtime:** `mcp_server_finance.py`.

## Connect (public)

| Endpoint | URL |
|----------|-----|
| **xpay (recommended)** | `https://sec-edgar-filings.mcp.xpay.sh/mcp?key=YOUR_XPAY_KEY` |
| Cloud Run (upstream) | `https://sec-filings-mcp-1065601264332.us-central1.run.app/mcp` |

Register / manage on [xpay.tools](https://xpay.tools). Slug: `sec-edgar-filings`.

## Local dev

```powershell
git clone https://github.com/stagproject/sec-filings-mcp.git
cd sec-filings-mcp
copy .env.example .env
# Edit .env with Supabase + x402 keys
uv sync
# Run once in Supabase SQL Editor: sql/fi_processed_transactions.sql
uv run python mcp_server_finance.py --sse
# MCP: http://127.0.0.1:8081/mcp  (PORT in .env)
```

Tests:

```powershell
uv run python test_finance_mcp.py
uv run python test_finance_mcp.py --xpay-only --e2e
```

## Cloud Run

```powershell
gcloud run deploy sec-filings-mcp `
  --source . `
  --region us-central1 `
  --allow-unauthenticated `
  --port 8080
```

Set env vars from `.env` (not committed). Do not deploy `.env.cloudrun.yaml` to git.

## Glama

1. Push this repo (public) under `stagproject/sec-filings-mcp`.
2. Wait for indexing at [glama.ai/mcp/servers](https://glama.ai/mcp/servers).
3. **Claim ownership** with GitHub org/user `stagproject` (must match `glama.json` maintainers).

## License

MIT — see [LICENSE.md](LICENSE.md).
