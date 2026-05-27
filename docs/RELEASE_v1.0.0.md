# v1.0.0 — SEC EDGAR Filings MCP

First stable release of **sec-filings-mcp**: an MCP server for equity-research agents over structured SEC EDGAR data (10-K, 10-Q, 8-K, CompanyFacts-derived metrics).

## Tools (3)

| Tool | Purpose | Cost |
|------|---------|------|
| **search_filings** | Catalog search over 10k+ filings (`fi_listings_portfolio`). Requires ≥1 filter (ticker, form_type, company_name, fiscal_period, cik). Returns `agent_readiness_score`, pagination. | xpay per-call |
| **get_filing_sample** | Free compact preview (`fi_listings_portfolio_compact`) for a `document_id`. | $0 |
| **purchase_filing** | Full JSON row after MPP v1.0 x402 (Polygon USDC). Includes `alpha_signals`, `causality_events`, `financial_metrics`. | xpay + on-chain |

**Agent workflow:** `search_filings` → `get_filing_sample` → `purchase_filing`.

## Connect (recommended — xpay)

```
https://sec-edgar-filings.mcp.xpay.sh/mcp?key=YOUR_XPAY_KEY
```

- Get an API key: https://xpay.tools  
- Slug: `sec-edgar-filings`  
- Transport: Streamable HTTP (`/mcp`)

## Upstream (developers)

```
https://sec-filings-mcp-1065601264332.us-central1.run.app/mcp
```

## Quick test (Cursor / Claude Desktop style)

Add under `mcpServers` (replace `YOUR_XPAY_KEY`):

```json
{
  "sec-edgar-filings": {
    "url": "https://sec-edgar-filings.mcp.xpay.sh/mcp?key=YOUR_XPAY_KEY"
  }
}
```

Example tool call after connect:

```json
{ "ticker": "AAPL", "form_type": "10-K", "limit": 5 }
```

→ tool: `search_filings`

## Discovery

- GitHub: https://github.com/stagproject/sec-filings-mcp  
- Glama: https://glama.ai/mcp/servers (search `sec-filings-mcp` / `stagproject`)  
- MCP Registry: `io.github.stagproject/sec-filings-mcp`  
- A2A Agent Card: `https://sec-filings-mcp-1065601264332.us-central1.run.app/.well-known/agent-card.json`  
- `llms.txt`, `skill.md`, `.well-known/mcp.json` on the xpay host

## License

MIT
