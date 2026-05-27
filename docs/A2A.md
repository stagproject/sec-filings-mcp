# A2A, MCP, and x402 — sec-filings-mcp

How this server fits the **agent protocol stack** (2026).

## Stack map

| Layer | Protocol | This project |
|-------|----------|--------------|
| Tool use | **MCP** (Streamable HTTP) | **Production API** — xpay + Cloud Run |
| Discovery | **A2A Agent Card** | Cloud Run upstream `/.well-known/agent-card.json` (xpay returns 403 for `/.well-known/*`; `llms.txt` on xpay is auto-generated) |
| Payment | **x402** (HTTP 402 + on-chain USDC) | `purchase_filing` (MPP v1.0 two-step) |
| Agent-to-agent tasks | **A2A** JSON-RPC | **Roadmap** — card + skills today; task endpoint later |

MCP and A2A are **complementary** ([A2A protocol](https://a2a-protocol.org/)): MCP = agent → tools; A2A = agent → agent delegation.

## Connect today (MCP)

```json
{
  "mcpServers": {
    "sec-edgar-filings": {
      "url": "https://sec-edgar-filings.mcp.xpay.sh/mcp?key=YOUR_XPAY_KEY"
    }
  }
}
```

Tools: `search_filings` → `get_filing_sample` → `purchase_filing`.

## A2A discovery

- **Agent Card (live):** `https://sec-filings-mcp-1065601264332.us-central1.run.app/.well-known/agent-card.json`
- **Agent Card (git):** `https://raw.githubusercontent.com/stagproject/sec-filings-mcp/main/.well-known/agent-card.json`
- **x402 extension declared:** [a2a-x402 v0.2](https://github.com/google-agentic-commerce/a2a-x402/blob/main/spec/v0.2)
- **MCP extension:** primary invoke at `url` (Streamable HTTP)

Clients that speak **A2A only** should read the card, then use **MCP** at the documented URL until a native A2A task endpoint ships.

## x402 mapping

| User-facing | Protocol detail |
|-------------|-----------------|
| `purchase_filing` step 1 (no `tx_hash`) | HTTP 402 + `transaction_payload` |
| On-chain USDC broadcast | Polygon (default), Base optional |
| `purchase_filing` step 2 (with `tx_hash`) | Verify + deliver full JSON |

This matches **x402 monetization intent**; transport is **MCP tool calls**, not yet A2A `payment-required` task metadata ([a2a-x402 spec](https://github.com/google-agentic-commerce/a2a-x402/blob/main/spec/v0.2/spec.md)).

## Official MCP Registry

- Name: `io.github.stagproject/sec-filings-mcp`
- Publish: see [docs/MCP_REGISTRY.md](MCP_REGISTRY.md)

## References

- [A2A Protocol](https://a2a-protocol.org/)
- [a2a-x402](https://github.com/google-agentic-commerce/a2a-x402)
- [x402](https://x402.gitbook.io/x402)
- [MCP Specification](https://modelcontextprotocol.io/)
- [xpay.tools](https://xpay.tools)
