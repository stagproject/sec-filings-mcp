# Distribution & discovery — who does what

How strangers find and **actually invoke** `sec-filings-mcp`, and what improves the score if baseline discovery is **10**.

## Three connection paths (not only xpay)

| Path | xpay API key? | xpay per-call charge? | `purchase_filing` (on-chain) |
|------|---------------|------------------------|------------------------------|
| **Glama → Try in Browser** | No (Glama sandbox / placeholders) | No | No (sandbox; not production wallet) |
| **Cloud Run upstream** | No | No | Yes — x402 USDC (~$5 default) |
| **xpay proxy** (`sec-edgar-filings`) | **Yes** ([xpay.tools](https://xpay.tools)) | Per xpay dashboard (can be **$0** per tool) | Yes — x402 on top |

Official xpay pricing docs: [Pricing Your Tools](https://docs.xpay.sh/en/tools/publish/pricing-your-tools) — *“Set the price to `0` for tools you want to offer for free … Free tools still require an API key.”*

So:

- **Glama listing alone** does not force xpay signup if the user clicks **Try in Browser** (stdio sandbox on Glama).
- **Production without xpay key** is possible for **`search_filings` + `get_filing_sample`** via Cloud Run (see [TRY_WITHOUT_XPAY.md](TRY_WITHOUT_XPAY.md)).
- **xpay path** always needs a key; you can set **$0** on `search_filings` / `get_filing_sample` in the xpay dashboard — that is allowed, not “no key.”

`purchase_filing` is never “free” in the product sense: on-chain USDC remains even on Cloud Run direct.

---

## Work split: you vs repo (agent)

### You (xpay / Glama admin / GitHub outreach)

| # | Action | Why |
|---|--------|-----|
| 1 | **Request finance collection** — use [xpay-collection-request.md](xpay-collection-request.md) (Discord / support) | `finance.mcp.xpay.sh` is where finance agents look; this slug is not in that bundle today |
| 2 | **xpay dashboard** — set `search_filings` / `get_filing_sample` to **$0**; keep `purchase_filing` priced or $0 proxy + on-chain $5 | Matches “try then buy”; free tools still need key per xpay rules |
| 3 | **Open PR** to [awesome-mcp-servers](https://github.com/punkpeye/awesome-mcp-servers) using [awesome-mcp-servers-entry.md](awesome-mcp-servers-entry.md) | Largest human-curated MCP list |
| 4 | **Glama Admin** — Sync Server; optional Glama release **v1.0.2**; confirm **Try in Browser** works | Discovery UI + sandbox |
| 5 | Optional: PulseMCP / Smithery / mcp.so — same URLs as README | Secondary directories |

### Done in repo (no dashboard access)

| # | Deliverable |
|---|-------------|
| 1 | [TRY_WITHOUT_XPAY.md](TRY_WITHOUT_XPAY.md) — Glama + Cloud Run copy-paste |
| 2 | README — try paths, Glama badges, honest xpay vs upstream table |
| 3 | `server.json` / Agent Card / `llms.txt` / `skill.md` — **trial** URL on Cloud Run |
| 4 | [xpay-collection-request.md](xpay-collection-request.md) — ready-to-send text |
| 5 | [awesome-mcp-servers-entry.md](awesome-mcp-servers-entry.md) — PR body + list line |

---

## Discovery score estimate (baseline = 10)

Rough **relative** reach index (not Glama’s internal score). Assumes baseline **10** = today (Registry + Glama page, almost no curated lists, xpay-only messaging).

| Stage | What’s live | Index (range) | Δ vs 10 |
|-------|-------------|---------------|---------|
| **Now** | Registry, Glama, xpay slug | **10** | — |
| **A — Repo only** (this doc + TRY_WITHOUT_XPAY + README/Agent Card) | Clear Glama try + Cloud Run trial; better SEO when someone lands on GitHub | **12–16** | +20–60% |
| **B — You: xpay $0 tools + finance collection approved** | `xpay_discover` / finance bundle | **22–35** | ~2–3× |
| **C — You: awesome-mcp-servers merged** | Finance/Data category backlink | **28–42** | ~3–4× |
| **D — B + C + 1 short tutorial** (Zenn/dev.to, sample call only) | Repeatable funnel | **35–55** | ~3.5–5× |
| **E — 6+ months + Maintenance A** | Trust badge; little extra traffic alone | **+0–5** on top of D | minor |

**Repo-only work (A)** does **not** replace xpay collection: expect about **+2 to +6** on a 10-point scale (~**12–16**), not 30+.

**“Free demo outside” is not impossible**

- **OK (platform):** Glama **Try in Browser**; Cloud Run **upstream** for catalog + sample without xpay key ([TRY_WITHOUT_XPAY.md](TRY_WITHOUT_XPAY.md)).
- **OK (xpay official):** $0 per-tool pricing + API key + free signup credits.
- **Not OK without key:** `https://sec-edgar-filings.mcp.xpay.sh/mcp` (xpay proxy always expects `?key=`).

---

## Metrics to watch

| Surface | Metric |
|---------|--------|
| xpay publisher dashboard | Calls per tool on slug `sec-edgar-filings` |
| Cloud Run | Requests to `/mcp` (trial path) |
| Glama | Active usage (includes sandbox) |

If xpay = 0 and Glama > 0, traffic is mostly **Try in Browser**, not paying users.

---

## Related

- [DISCOVERY.md](DISCOVERY.md) — canonical URLs
- [MCP_REGISTRY.md](MCP_REGISTRY.md) — registry publish
- [GLAMA_BUILD.md](../GLAMA_BUILD.md) — Glama Docker / stdio
