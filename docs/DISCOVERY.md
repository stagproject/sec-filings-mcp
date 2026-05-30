# Discovery & registry — sec-filings-mcp

Canonical URLs for clients, registries, and A2A-aware agents.

**Try without xpay key:** [TRY_WITHOUT_XPAY.md](TRY_WITHOUT_XPAY.md) · **Growth plan:** [DISTRIBUTION.md](DISTRIBUTION.md)

## MCP (production invoke)

| Endpoint | URL |
|----------|-----|
| xpay (billing + xpay catalog) | `https://sec-edgar-filings.mcp.xpay.sh/mcp?key=YOUR_XPAY_KEY` |
| Cloud Run upstream (trial: no xpay key) | `https://sec-filings-mcp-1065601264332.us-central1.run.app/mcp` |
| Glama sandbox (no xpay key) | https://glama.ai/mcp/servers/stagproject/sec-filings-mcp → Try in Browser |

xpay does **not** proxy `/.well-known/*` (403). Use Cloud Run for machine-readable discovery files.

## Discovery files (Cloud Run)

| File | URL |
|------|-----|
| Agent Card (A2A) | https://sec-filings-mcp-1065601264332.us-central1.run.app/.well-known/agent-card.json |
| mcp.json | https://sec-filings-mcp-1065601264332.us-central1.run.app/.well-known/mcp.json |
| Health | https://sec-filings-mcp-1065601264332.us-central1.run.app/ping |
| llms.txt (xpay auto) | https://sec-edgar-filings.mcp.xpay.sh/llms.txt |

## Registries

| Registry | ID / link |
|----------|-----------|
| MCP Registry | `io.github.stagproject/sec-filings-mcp` |
| Glama | https://glama.ai/mcp/servers/stagproject/sec-filings-mcp |

Republish after `server.json` changes:

```powershell
# Prefer: git tag vX.Y.Z && git push origin vX.Y.Z  (GitHub Actions publishes)
# Or locally: .\mcp-publisher.exe publish  (see docs/MCP_REGISTRY.md)
```

## Signed Agent Card (roadmap)

[A2A 1.2](https://a2a-protocol.org/) supports cryptographically signed Agent Cards for domain binding. Not yet enabled on this server; the unsigned card above is the current discovery surface.

## Related docs

- [A2A.md](A2A.md) — protocol stack
- [MCP_REGISTRY.md](MCP_REGISTRY.md) — publish steps
