# Your checklist (after agent push) — stages B → D

Baseline discovery index **10** → repo stage **A ~12–16** after push + Cloud Run deploy. **30+** needs your xpay + awesome work below.

## Done by agent (stage A)

- [x] `docs/DISTRIBUTION.md`, `TRY_WITHOUT_XPAY.md`, xpay/awesome templates
- [x] README / Agent Card / `server.json` / `llms.txt` — trial URLs
- [ ] **You confirm:** `git pull` on `main` (after push)

## 1. Cloud Run deploy (~5 min) — required for live trial URL

From repo root, with `gcloud` logged in and project set:

```powershell
cd c:\AGS\mcp-server-finance
gcloud run deploy sec-filings-mcp --source . --region us-central1 --allow-unauthenticated --port 8080
```

Verify:

- https://sec-filings-mcp-1065601264332.us-central1.run.app/ping → `{"status":"ok"}`
- https://sec-filings-mcp-1065601264332.us-central1.run.app/ → JSON includes `trial_connect_url`

## 2. Glama Admin (~2 min)

1. https://glama.ai → your server **sec-filings-mcp**
2. **Repository → Sync Server**
3. Optional: **Build & Release** if you changed Dockerfile tab; confirm **Try in Browser** works

## 3. Stage B — xpay (~15 min) → index **22–35**

### B1. Dashboard pricing — done if all tools $0 + Save Pricing

### B2. Finance collection request → **[XPAY_OUTREACH.md](XPAY_OUTREACH.md)**

1. **Email** → `support@xpay.sh`（本文コピペ）
2. **Discord** → `#showcase`（紹介）+ 任意 `#agentic-payments`（掲載手順の質問）— [XPAY_OUTREACH.md](XPAY_OUTREACH.md)
3. 1週間後: https://finance.mcp.xpay.sh/llms.txt で `sec-edgar` を検索

## 4. Stage C — awesome-mcp-servers (~10 min) → index **28–42**

1. Fork https://github.com/punkpeye/awesome-mcp-servers
2. Add the line from [awesome-mcp-servers-entry.md](awesome-mcp-servers-entry.md) under **Finance** or **Data**
3. Open PR (title/body in same file)
4. After merge, optional: link from README

## 5. Stage D — one short tutorial (optional) → index **35–55**

Publish once (Zenn / dev.to / GitHub Discussions):

- Title idea: *Try SEC EDGAR MCP without xpay key*
- Link: [TRY_WITHOUT_XPAY.md](TRY_WITHOUT_XPAY.md)
- One example: `search_filings` `{"ticker":"AAPL","form_type":"10-K","limit":3}`

## Metrics (weekly)

| Where | What to check |
|-------|----------------|
| xpay publisher | Calls on `sec-edgar-filings` by tool |
| Cloud Run metrics | Requests to `/mcp` |
| Glama | Active usage (sandbox-heavy) |

If **xpay = 0** and **Glama > 0** → only sandbox; focus on B + C + tutorial.
