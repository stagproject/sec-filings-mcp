# sec-filings-mcp

[![SEC EDGAR Filings MCP](https://glama.ai/mcp/servers/stagproject/sec-filings-mcp/badges/card.svg)](https://glama.ai/mcp/servers/stagproject/sec-filings-mcp)

SEC EDGAR structured filing MCP for agents: **search_filings**, **get_filing_sample**, **purchase_filing**. Data lives in Supabase views (`fi_listings_portfolio`, `fi_listings_portfolio_compact`) populated by the [finance-factory](https://github.com/stagproject) pipeline.

| Read first | File |
|------------|------|
| **Try without xpay key** | [docs/TRY_WITHOUT_XPAY.md](docs/TRY_WITHOUT_XPAY.md) — Glama sandbox or Cloud Run upstream |
| Distribution (you vs repo) | [docs/DISTRIBUTION.md](docs/DISTRIBUTION.md) |
| Build / handoff | [MCP_FINANCE_BUILD.md](MCP_FINANCE_BUILD.md) |
| Env template | [.env.example](.env.example) → copy to `.env` |
| Glama | [glama.json](glama.json) (`maintainers: stagproject`); build fix: [GLAMA_BUILD.md](GLAMA_BUILD.md) |
| A2A / x402 | [docs/A2A.md](docs/A2A.md) — Agent Card + payment mapping |
| MCP Registry | `io.github.stagproject/sec-filings-mcp` — [docs/MCP_REGISTRY.md](docs/MCP_REGISTRY.md) |
| Discovery URLs | [docs/DISCOVERY.md](docs/DISCOVERY.md) |

Template reference: `mcp_server.py` (patent MCP, unmodified). **Runtime:** `mcp_server_finance.py`.

## Protocol stack (MCP + A2A + x402)

| Layer | How to use |
|-------|------------|
| **MCP (production)** | xpay URL below — `tools/call` on `search_filings`, `get_filing_sample`, `purchase_filing` |
| **A2A (discovery)** | Agent Card on Cloud Run upstream (xpay blocks `/.well-known/*`): `https://sec-filings-mcp-1065601264332.us-central1.run.app/.well-known/agent-card.json` |
| **x402 (payment)** | `purchase_filing` — 402 + Polygon USDC + `tx_hash` redelivery |

Native A2A JSON-RPC task API is on the roadmap; today agents invoke via **MCP Streamable HTTP**. Details: [docs/A2A.md](docs/A2A.md).

## Try first (no xpay API key)

| Path | URL / action |
|------|----------------|
| **Glama sandbox** | [Open server](https://glama.ai/mcp/servers/stagproject/sec-filings-mcp) → **Try in Browser** |
| **Cloud Run trial** | `https://sec-filings-mcp-1065601264332.us-central1.run.app/mcp` — `search_filings` + `get_filing_sample` without `?key=` |

Details: [docs/TRY_WITHOUT_XPAY.md](docs/TRY_WITHOUT_XPAY.md).  
xpay proxy always needs a key; per-tool **$0** is allowed on xpay ([docs](https://docs.xpay.sh/en/tools/publish/pricing-your-tools)) but is not the same as “no signup.”

## Connect (production)

| Endpoint | URL |
|----------|-----|
| **xpay (billing + catalog)** | `https://sec-edgar-filings.mcp.xpay.sh/mcp?key=YOUR_XPAY_KEY` |
| Cloud Run (upstream) | `https://sec-filings-mcp-1065601264332.us-central1.run.app/mcp` |

Register / manage on [xpay.tools](https://xpay.tools). Slug: `sec-edgar-filings`.  
Publisher checklist (finance collection, awesome list): [docs/DISTRIBUTION.md](docs/DISTRIBUTION.md).

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

Listed at [glama.ai/mcp/servers/stagproject/sec-filings-mcp](https://glama.ai/mcp/servers/stagproject/sec-filings-mcp) — use **Try in Browser** for a no-key sandbox; production traffic uses xpay or Cloud Run above.

## MCP Registry

```text
io.github.stagproject/sec-filings-mcp
```

Publish / update: [docs/MCP_REGISTRY.md](docs/MCP_REGISTRY.md). Search: https://registry.modelcontextprotocol.io

## License

MIT — see [LICENSE.md](LICENSE.md).
