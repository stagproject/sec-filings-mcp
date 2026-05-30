# xpay finance collection — request template (you send)

**Step-by-step (email + Discord):** [XPAY_OUTREACH.md](XPAY_OUTREACH.md)

Copy into xpay Discord / support / publisher onboarding. Edit bracketed fields.

---

**Subject:** Add `sec-edgar-filings` to Finance MCP collection

Hi xpay team,

I publish **SEC EDGAR Filings MCP** and would like it included in the **Finance collection** (`finance.mcp.xpay.sh`) and discoverable via master `xpay_discover` for queries like “SEC EDGAR 10-K CompanyFacts”.

| Field | Value |
|-------|--------|
| Provider slug | `sec-edgar-filings` |
| Proxy MCP URL | `https://sec-edgar-filings.mcp.xpay.sh/mcp` |
| Upstream (Cloud Run) | `https://sec-filings-mcp-1065601264332.us-central1.run.app/mcp` |
| GitHub | https://github.com/stagproject/sec-filings-mcp |
| MCP Registry | `io.github.stagproject/sec-filings-mcp` |
| Glama | https://glama.ai/mcp/servers/stagproject/sec-filings-mcp |

**Tools (3)**

- `search_filings` — catalog search (suggest **$0** on xpay)
- `get_filing_sample` — free compact preview (suggest **$0** on xpay)
- `purchase_filing` — full JSON via x402 USDC on Polygon (on-chain ~$5; xpay per-call as configured)

**Ask**

1. Add tools to **finance.mcp.xpay.sh** collection (or confirm process to apply).
2. Confirm `search_filings` / `get_filing_sample` can stay at **$0** with API key (per [pricing docs](https://docs.xpay.sh/en/tools/publish/pricing-your-tools)).
3. Any metadata/tags you need for catalog search (“SEC”, “EDGAR”, “10-K”, “CompanyFacts”).

Trial without xpay key (for your docs): Cloud Run upstream — documented in repo `docs/TRY_WITHOUT_XPAY.md`.

Thanks,  
[Your name] — stagproject

---

**Your checklist after send**

- [ ] Dashboard: `search_filings` / `get_filing_sample` = $0
- [ ] Dashboard: branding/description mentions “free preview”
- [ ] awesome-mcp-servers PR opened ([awesome-mcp-servers-entry.md](awesome-mcp-servers-entry.md))
