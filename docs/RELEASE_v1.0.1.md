# Release v1.0.1

## Highlights

- **A2A Agent Card** at Cloud Run upstream (xpay does not proxy `/.well-known/*`)
- **MCP Registry** workflow + `server.json` for `io.github.stagproject/sec-filings-mcp`
- **Cloud Run** redeploy: `GET /ping` → 200, discovery JSON live
- Docs: [A2A.md](A2A.md), [MCP_REGISTRY.md](MCP_REGISTRY.md)

## URLs

| Purpose | URL |
|---------|-----|
| MCP (production) | `https://sec-edgar-filings.mcp.xpay.sh/mcp?key=YOUR_XPAY_KEY` |
| A2A Agent Card | `https://sec-filings-mcp-1065601264332.us-central1.run.app/.well-known/agent-card.json` |
| mcp.json | `https://sec-filings-mcp-1065601264332.us-central1.run.app/.well-known/mcp.json` |
| Health | `https://sec-filings-mcp-1065601264332.us-central1.run.app/ping` |
| GitHub | https://github.com/stagproject/sec-filings-mcp |

## MCP Registry

If GitHub Actions OIDC publish failed, run once locally:

```powershell
cd c:\AGS\mcp-server-finance
.\mcp-publisher.exe login github
.\mcp-publisher.exe publish
```

Then verify: `curl "https://registry.modelcontextprotocol.io/v0/servers?search=sec-filings-mcp"`
