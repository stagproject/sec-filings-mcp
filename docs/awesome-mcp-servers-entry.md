# awesome-mcp-servers — PR draft (you open the PR)

Target repo: https://github.com/punkpeye/awesome-mcp-servers

Pick section **Finance** or **Data**. One-line list entry + optional longer blurb for PR body.

## List line (markdown)

```markdown
- [SEC EDGAR Filings MCP](https://github.com/stagproject/sec-filings-mcp) — Search 10-K/10-Q, free filing preview, full JSON via x402 USDC. Try on [Glama](https://glama.ai/mcp/servers/stagproject/sec-filings-mcp) or Cloud Run upstream without xpay key ([docs](https://github.com/stagproject/sec-filings-mcp/blob/main/docs/TRY_WITHOUT_XPAY.md)). Production: `https://sec-edgar-filings.mcp.xpay.sh/mcp?key=YOUR_XPAY_KEY`.
```

## PR title

```text
Add sec-filings-mcp (SEC EDGAR search, sample, x402 purchase)
```

## PR body

```markdown
## Summary

Adds **sec-filings-mcp** — MCP server for agent-native SEC EDGAR structured data (search → free sample → x402 full row).

## Connect

- **xpay (production):** `https://sec-edgar-filings.mcp.xpay.sh/mcp?key=YOUR_XPAY_KEY`
- **Trial without xpay key:** https://github.com/stagproject/sec-filings-mcp/blob/main/docs/TRY_WITHOUT_XPAY.md
- **Glama:** https://glama.ai/mcp/servers/stagproject/sec-filings-mcp
- **MCP Registry:** `io.github.stagproject/sec-filings-mcp`

## Tools

| Tool | Purpose |
|------|---------|
| search_filings | Catalog search (filters required) |
| get_filing_sample | Free compact preview |
| purchase_filing | Full JSON via x402 USDC (Polygon) |

MIT · https://github.com/stagproject/sec-filings-mcp
```

## After merge

Add badge or “Listed in awesome-mcp-servers” to README (optional).
