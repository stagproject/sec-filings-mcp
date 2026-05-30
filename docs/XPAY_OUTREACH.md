# xpay 掲載依頼 — メール & Discord のやり方

finance コレクション（`finance.mcp.xpay.sh`）と `xpay_discover` 向けの問い合わせ手順。  
**公式サポート経路**（[Troubleshooting](https://docs.xpay.sh/en/developer-resources/troubleshooting) / [Community](https://docs.xpay.sh/en/community)）に沿った送り方。

**前提（済んでいること）**

- [x] xpay に `sec-edgar-filings` 登録済み
- [x] 3ツールとも Flat Rate **$0.00** を **Save Pricing** 済み

---

## 1. メール（推奨：まずこちら）

### 手順

1. メールアプリを開く（Gmail 等）。
2. **新規作成**
3. 下記をコピペ（`[Your name]` だけ自分の名前に変更）。
4. **送信**
5. 返信が来るまで 1〜7 日ほど待つ（来なければ Discord でも同内容を追記）。

| 項目 | 値 |
|------|-----|
| **宛先** | `support@xpay.sh` |
| **件名** | `Request: add sec-edgar-filings to Finance MCP collection` |
| **言語** | 英語（運営向け） |

### 本文（コピペ用）

```
Hi xpay team,

I publish SEC EDGAR Filings MCP and would like it included in the Finance MCP collection (finance.mcp.xpay.sh) and discoverable via xpay_discover for queries like "SEC EDGAR 10-K CompanyFacts".

Provider slug: sec-edgar-filings
Proxy MCP URL: https://sec-edgar-filings.mcp.xpay.sh/mcp
Upstream (Cloud Run): https://sec-filings-mcp-1065601264332.us-central1.run.app/mcp
GitHub: https://github.com/stagproject/sec-filings-mcp
MCP Registry: io.github.stagproject/sec-filings-mcp
Glama: https://glama.ai/mcp/servers/stagproject/sec-filings-mcp

Tools (3):
- search_filings — catalog search ($0 on xpay dashboard)
- get_filing_sample — free compact preview ($0 on xpay dashboard)
- purchase_filing — full JSON via x402 USDC on Polygon (on-chain data fee applies on upstream; $0 xpay proxy per call)

Requests:
1. Add these tools to the finance.mcp.xpay.sh collection (or tell me the official process).
2. Confirm $0 per-call pricing for search_filings and get_filing_sample is correct with API key required.
3. Any metadata/tags you need for catalog search (SEC, EDGAR, 10-K, CompanyFacts).

Trial without xpay key (documented): https://github.com/stagproject/sec-filings-mcp/blob/main/docs/TRY_WITHOUT_XPAY.md

Thanks,
[Your name]
stagproject
```

### 送信後

- [ ] 送信済み（日付: ______）
- [ ] 返信あり → 指示どおり設定
- [ ] 1週間無返信 → Discord に同じ要約を投稿（下記）

---

## 2. Discord

### 手順

1. 招待を開く: https://discord.com/invite/vukXDGT7n5  
2. **招待を受ける** でサーバー `{xpay✦}` に参加。  
3. 左のチャンネル一覧から **`#api-monetization`** を開く。  
   - 見つからなければ **`#showcase`** または **`#developer-help`**。  
   - （[Community Hub](https://docs.xpay.sh/en/community) のチャンネル一覧参照）  
4. 下記 **Discord 用短文** を貼って **Enter**。  
5. メールも送っている場合は、文末の「Also emailed support@」の行を残す。

**注意**

- メンバー数が少なくても運営が読むことがある。  
- 長文より **短文 + リンク** の方が読まれやすい。  
- スパム扱いされないよう、同じ長文を複数チャンネルに連投しない（1チャンネルで足りる）。

### 投稿文（コピペ用・英語）

```
Hi — publisher of SEC EDGAR Filings MCP (slug: sec-edgar-filings).

Asking to be listed on the Finance MCP collection (finance.mcp.xpay.sh) and xpay_discover (e.g. "SEC EDGAR 10-K").

• Proxy: https://sec-edgar-filings.mcp.xpay.sh/mcp
• Tools: search_filings, get_filing_sample ($0 on dashboard), purchase_filing (x402 on upstream)
• Repo: https://github.com/stagproject/sec-filings-mcp
• Registry: io.github.stagproject/sec-filings-mcp

What’s the process to join the finance collection? Also emailed support@xpay.sh on [DATE you sent].

Thanks — stagproject
```

`[DATE you sent]` をメールを送った日付に変える（例: `May 30, 2026`）。メール未送信ならその行を削除。

### 投稿後

- [ ] `#api-monetization`（または代替チャンネル）に投稿済み  
- [ ] 返信・スレッドがあれば内容をメモ  
- [ ] finance コレクションの `llms.txt` に自分のツール名が出るか後日確認: https://finance.mcp.xpay.sh/llms.txt で `sec-edgar` を検索

---

## 3. 掲載されたか確認する方法

1. ブラウザで https://finance.mcp.xpay.sh/llms.txt を開く。  
2. `Ctrl+F` で `sec-edgar` または `search_filings` を検索。  
3. ヒットすれば finance コレクションに載っている可能性が高い。  
4. 別途 https://xpay.tools で「SEC」「EDGAR」検索。

---

## 4. 次（B のあと）

- [ ] [awesome-mcp-servers-entry.md](awesome-mcp-servers-entry.md) で awesome PR（ステージ C）  
- [ ] 週1: xpay ダッシュボードのコール数を確認  

関連: [DISTRIBUTION.md](DISTRIBUTION.md) · [YOUR_TODO.md](YOUR_TODO.md)
