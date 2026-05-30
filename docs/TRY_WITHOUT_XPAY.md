# Try SEC filings MCP without xpay (catalog + free sample)

Use this for README links, tutorials, and Glama visitors who do not have an xpay API key yet.

## Option 1 — Glama (no key, sandbox)

1. Open [SEC EDGAR Filings MCP on Glama](https://glama.ai/mcp/servers/stagproject/sec-filings-mcp).
2. Click **Try in Browser**.
3. Call `search_filings` then `get_filing_sample` in Glama’s sandbox (placeholder Supabase/x402 env — not your production wallet).

Glama verify build uses stdio + placeholders; see [GLAMA_BUILD.md](../GLAMA_BUILD.md).

## Option 2 — Cloud Run upstream (no xpay key; real data)

**MCP URL (no `?key=`):**

```text
https://sec-filings-mcp-1065601264332.us-central1.run.app/mcp
```

**Cursor / Claude Desktop** (`mcp.json` style):

```json
{
  "mcpServers": {
    "sec-filings-trial": {
      "url": "https://sec-filings-mcp-1065601264332.us-central1.run.app/mcp"
    }
  }
}
```

**Works without xpay key**

| Tool | Charge |
|------|--------|
| `search_filings` | No xpay meter (upstream direct) |
| `get_filing_sample` | No xpay meter |
| `purchase_filing` | **x402 USDC on Polygon** (~$5 list; see `FINANCE_FILING_PRICE_USD`) |

Discovery JSON on the same host:

- Agent Card: `/.well-known/agent-card.json`
- `mcp.json`: `/.well-known/mcp.json`
- Health: `/ping`

xpay **does not** proxy `/.well-known/*` (403 on the xpay host).

## Option 3 — xpay (key required; tools can be $0)

1. Get a key: https://xpay.tools (free credits on signup).
2. Connect:

```json
{
  "mcpServers": {
    "sec-edgar-filings": {
      "url": "https://sec-edgar-filings.mcp.xpay.sh/mcp?key=YOUR_XPAY_KEY"
    }
  }
}
```

Publisher: set per-tool price to **0** for `search_filings` and `get_filing_sample` in the xpay dashboard ([pricing docs](https://docs.xpay.sh/en/tools/publish/pricing-your-tools)). Calls still require the key; balance is not deducted for $0 tools.

## Example first call (after connect)

Tool: `search_filings`

```json
{
  "ticker": "AAPL",
  "form_type": "10-K",
  "limit": 3
}
```

Then: `get_filing_sample` with a `document_id` from the result.

## When to use which path

| Goal | Path |
|------|------|
| Quick look in browser | Glama Try |
| Real data, no xpay signup yet | Cloud Run upstream |
| Billing, xpay catalog, finance collection | xpay slug |

Full distribution plan: [DISTRIBUTION.md](DISTRIBUTION.md).
