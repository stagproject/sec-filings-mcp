# Stage C — awesome-mcp-servers PR（あなたがやる・詳細手順）

**所要時間:** 約 15〜25 分（初回 Fork 含む）  
**効果の目安:** 発見率 **28〜42**（B の xpay 返信と併用）

エージェント側では PR を代行できません（あなたの GitHub アカウントで Fork が必要）。  
掲載行・PR 本文は [awesome-mcp-servers-entry.md](awesome-mcp-servers-entry.md) に用意済みです。

---

## 掲載する1行（コピペ）

**セクション:** `### 💰 Finance & Fintech`  
**挿入位置:** `[staccDOTsol/staccbot-tg]` の**直後**、`[stefan-xyz/mcp-server-runescape]` の**直前**（アルファベット順 `stagproject`）

```markdown
- [stagproject/sec-filings-mcp](https://github.com/stagproject/sec-filings-mcp) [![stagproject/sec-filings-mcp MCP server](https://glama.ai/mcp/servers/stagproject/sec-filings-mcp/badges/score.svg)](https://glama.ai/mcp/servers/stagproject/sec-filings-mcp) 📇 ☁️ - SEC EDGAR MCP for agents: search 10-K/10-Q, free sample preview, full filing JSON via x402 USDC on Polygon. xpay: `sec-edgar-filings`. Trial without xpay key: [docs](https://github.com/stagproject/sec-filings-mcp/blob/main/docs/TRY_WITHOUT_XPAY.md). Registry: `io.github.stagproject/sec-filings-mcp`.
```

（Glama バッジは同セクションの他行に合わせて付与。不要なら badge 部分を削除しても可。）

---

## 方法 A — GitHub ブラウザのみ（おすすめ）

### 1. Fork

1. ブラウザで https://github.com/punkpeye/awesome-mcp-servers を開く  
2. 右上 **Fork** → 自分のアカウント（`stagproject`）に Fork  
3. 完了まで待つ（`https://github.com/stagproject/awesome-mcp-servers`）

### 2. README を編集

1. Fork したリポの **README.md** を開く  
2. 右上 **鉛筆アイコン**（Edit this file）  
3. `Ctrl+F` で `### 💰 Finance & Fintech` にジャンプ  
4. `staccDOTsol/staccbot-tg` の行を探す  
5. その**次の行**に、上記「掲載する1行」を貼り付け  
6. ページ下 **Commit changes**  
   - Branch: `add-sec-filings-mcp`（新規ブランチ名で OK）  
   - メッセージ: `Add sec-filings-mcp to Finance & Fintech`

### 3. Pull Request

1. Fork 後、黄色バナー **Compare & pull request** をクリック（出なければ **Pull requests** → **New pull request**）  
2. **base:** `punkpeye/awesome-mcp-servers` `main`  
3. **compare:** `stagproject/awesome-mcp-servers` の `add-sec-filings-mcp`  
4. **Title:**

   ```text
   Add sec-filings-mcp (SEC EDGAR search, sample, x402 purchase)
   ```

5. **Body:** [awesome-mcp-servers-entry.md](awesome-mcp-servers-entry.md) の「PR body」ブロックをコピペ  
6. **Create pull request**

### 4. マージ後（任意）

1. 自分の `sec-filings-mcp` README に1行追加（例: “Listed in [awesome-mcp-servers](https://github.com/punkpeye/awesome-mcp-servers)”）  
2. こちらに依頼すれば README 追記も可能

---

## 方法 B — ローカル git（慣れている人向け）

```powershell
git clone https://github.com/stagproject/awesome-mcp-servers.git
cd awesome-mcp-servers
git checkout -b add-sec-filings-mcp
# README.md を編集（上記の1行を挿入）
git add README.md
git commit -m "Add sec-filings-mcp to Finance & Fintech"
git push -u origin add-sec-filings-mcp
```

ブラウザで PR 作成（方法 A の 3 と同じ）。

---

## よくある却下理由と対策

| 却下理由 | 対策 |
|----------|------|
| 重複 | 既に SEC 系があるが niche なら説明（構造化 EDGAR + x402） |
| 説明が短い | 上記1行はツール3つ・xpay slug を明記済み |
| ライセンス不明 | MIT（リポに LICENSE.md） |

---

## 完了チェック

- [ ] PR URL を控えた  
- [ ] マージされた（数日〜数週間）  
- [ ] `finance.mcp.xpay.sh/llms.txt` で `sec-edgar` を再確認（B の結果）

関連: [DISTRIBUTION.md](DISTRIBUTION.md) · [YOUR_TODO.md](YOUR_TODO.md)
