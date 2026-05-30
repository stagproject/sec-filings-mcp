# awesome-mcp-servers — PR draft (you open the PR)

Target repo: https://github.com/punkpeye/awesome-mcp-servers

Pick section **Finance** or **Data**. One-line list entry + optional longer blurb for PR body.

## Where to insert

- **Section:** `### 💰 Finance & Fintech` in https://github.com/punkpeye/awesome-mcp-servers/blob/main/README.md
- **After line:** `[staccDOTsol/staccbot-tg](...)`
- **Before line:** `[stefan-xyz/mcp-server-runescape](...)`
- **Full steps:** [STAGE_C_AWESOME_PR.md](STAGE_C_AWESOME_PR.md)

## List line (markdown)

```markdown
- [stagproject/sec-filings-mcp](https://github.com/stagproject/sec-filings-mcp) [![stagproject/sec-filings-mcp MCP server](https://glama.ai/mcp/servers/stagproject/sec-filings-mcp/badges/score.svg)](https://glama.ai/mcp/servers/stagproject/sec-filings-mcp) 📇 ☁️ - SEC EDGAR MCP for agents: search 10-K/10-Q, free sample preview, full filing JSON via x402 USDC on Polygon. xpay: `sec-edgar-filings`. Trial without xpay key: [docs](https://github.com/stagproject/sec-filings-mcp/blob/main/docs/TRY_WITHOUT_XPAY.md). Registry: `io.github.stagproject/sec-filings-mcp`.
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
