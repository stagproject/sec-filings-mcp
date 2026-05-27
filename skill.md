# SEC Filings Agent Marketplace

SEC EDGAR structured filing MCP for equity research agents, quants, and LLM workflows.

## When to use

- User asks about 10-K, 10-Q, 8-K, EDGAR, CompanyFacts, or ticker fundamentals
- Agent needs evidence-backed causality chains (not hallucinated filing narrative)
- Compare free preview vs paid full filing JSON

## Connect

```json
{
  "mcpServers": {
    "sec-filings": {
      "url": "https://sec-edgar-filings.mcp.xpay.sh/mcp?key=YOUR_XPAY_KEY"
    }
  }
}
```

API key: https://xpay.tools

## A2A discovery

- Agent Card: `https://sec-edgar-filings.mcp.xpay.sh/.well-known/agent-card.json`
- Skills: `search_filings`, `get_filing_sample`, `purchase_filing` (invoke via MCP URL above)
- x402 extension: [a2a-x402 v0.2](https://github.com/google-agentic-commerce/a2a-x402/blob/main/spec/v0.2)

## Typical flow

1. `search_filings` with `ticker` and optional `form_type`
2. `get_filing_sample` with `document_id` (free compact preview)
3. `purchase_filing` — empty `tx_hash` → on-chain USDC → retry with `tx_hash`

## Networks

`polygon` (USDC, default). `base` (USDC) also supported.
