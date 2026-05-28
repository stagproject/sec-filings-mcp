# v1.0.1 — SEC EDGAR Filings MCP

Release focused on **A2A discovery**, **MCP Registry**, and production hardening.

## What's new

- **A2A Agent Card** on Cloud Run upstream (xpay does not proxy `/.well-known/*`)
- **MCP Registry:** `io.github.stagproject/sec-filings-mcp` (active)
- **Cloud Run:** `GET /ping` health check; discovery JSON at upstream
- **Production pricing:** `FINANCE_FILING_PRICE_USD=5.00` (was test `0.000001`)
- Docs: [A2A.md](A2A.md), [MCP_REGISTRY.md](MCP_REGISTRY.md)

## Tools (3)

| Tool | Purpose | Cost |
|------|---------|------|
| **search_filings** | Catalog search (`fi_listings_portfolio`). ≥1 filter required. | xpay per-call |
| **get_filing_sample** | Free compact preview by `document_id`. | $0 |
| **purchase_filing** | Full JSON via MPP v1.0 x402 (Polygon USDC). | xpay + **$5** on-chain |

**Workflow:** `search_filings` → `get_filing_sample` → `purchase_filing`.

## Connect (xpay)

```
https://sec-edgar-filings.mcp.xpay.sh/mcp?key=YOUR_XPAY_KEY
```

## Discovery

| Resource | URL |
|----------|-----|
| MCP Registry | `io.github.stagproject/sec-filings-mcp` |
| A2A Agent Card | https://sec-filings-mcp-1065601264332.us-central1.run.app/.well-known/agent-card.json |
| mcp.json | https://sec-filings-mcp-1065601264332.us-central1.run.app/.well-known/mcp.json |
| Health | https://sec-filings-mcp-1065601264332.us-central1.run.app/ping |
| Glama | https://glama.ai/mcp/servers (search `sec-filings-mcp`) |

## Upstream

```
https://sec-filings-mcp-1065601264332.us-central1.run.app/mcp
```

## License

MIT
