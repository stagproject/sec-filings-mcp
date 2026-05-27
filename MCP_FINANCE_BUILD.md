# SEC Filings MCP — 構築引き継ぎ（AI / 開発者向け）

**新規リポジトリ:** `c:\AGS\mcp-server-finance`  
**データ源リポジトリ:** `c:\AGS\finance-factory`（倉庫・`fi_listings_portfolio`）  
**テンプレートリポジトリ:** `c:\AGS\mcp-server`（特許 MCP・x402・xpay 済み）  

最終更新: 2026-05-27

---

## 0. 外部仕様メモ（2026-05 時点）

### MCP（Model Context Protocol）

- トランスポート: **Streamable HTTP**（xpay 推奨）または SSE。
- クライアントは `tools/list` でツール定義を読み、LLM 向け説明（description）の品質が発見率に効く（Glama TDQS 等）。
- 公式レジストリ: [modelcontextprotocol.io/registry](https://modelcontextprotocol.io/registry/about) — メタデータのみ。評価・課金は下流（xpay / Glama）。

### xpay（公開・課金プロキシ）

- 自前 Cloud Run URL を登録 → **`https://{slug}.mcp.xpay.sh/mcp`** が発行される。
- 登録時に `tools/list` を introspect。`llms.txt` / `skill.md` / `.well-known/mcp.json` は **slug ごと自動生成**。
- 特許と金融は **必ず別 slug**（例: 特許 `mirelia-structured-data-marketplace`、金融 `mirelia-sec-filings`）。
- ドキュメント: [Register server](https://docs.xpay.sh/en/tools/publish/register-server) / [Connection URLs](https://docs.xpay.sh/en/tools/reference/connection-urls)
- Finance コレクション `https://finance.mcp.xpay.sh/mcp` とは別プロバイダとして登録する。

### A2A × x402（エージェント間決済）

- **A2A** = エージェント間プロトコル。**x402** = HTTP 402 + オンチェーン USDC 等のマイクロペイメント。
- 拡張仕様: [google-agentic-commerce/a2a-x402](https://github.com/google-agentic-commerce/a2a-x402)（Standalone / Embedded フロー）。
- **特許 MCP は既に MPP v1.0 型の 402 フロー**（`purchase_*` + `tx_hash` 2段）を `mcp_server.py` に実装済み。金融 MCP も同パターン流用可。
- **xpay** = プロキシ側でツール課金。**x402 直** = 自サーバーが 402 を返す。両方併用可（特許は xpay URL + 自前 402）。

---

## 1. 特許 MCP をコピーしてカスタマイズすべきか？

**結論: はい —「リポジトリを丸ごと複製」ではなく「スケルトンコピー + 特許除去」が最善。**

| 方式 | 推奨 |
|------|------|
| 同一 `mcp_server.py` に金融ツールを足す | **非推奨**（xpay slug・Glama 一貫性・障害分離が悪化） |
| `mcp-server` を git clone して別フォルダで維持 | **非推奨**（特許と金融のデプロイが絡む） |
| **`mcp-server-finance` 新規フォルダ** + 下記ファイルだけコピー | **推奨** |

### コピー元から持ってくるもの（`c:\AGS\mcp-server`）

| ファイル / ディレクトリ | 用途 |
|-------------------------|------|
| `mcp_server.py` | **ベース**。特許ツール・特許 Supabase テーブル参照を削除し金融ツールに差し替え |
| `pyproject.toml` | 依存関係（名前・description を金融用に変更） |
| Starlette 起動部（`mcp_server.py` 末尾の `MPPMiddleware` / `uvicorn`） | そのまま |
| x402 ヘルパー（`generate_payment_memo`, `chains`, `get_rose_price`） | `purchase_filing` 用に流用 |
| `.well-known/mcp.json` テンプレ | SEC 用に書き換え |
| `llms.txt`, `skill.md` | SEC キーワード特化で新規作成（xpay 再同期後も上書き方針を README に） |
| `glama.json`, `server.json` | 別名で新規（特許レジストリと混同しない） |

### コピーしないもの

- `data/batch/*`（特許バッチ入力）
- `downloaded_*.json`, `test_result_*.json`
- `.venv`（`uv sync` で再生成）
- 特許専用 Supabase ビュー名（`v_single_patent_*`）

### 同一 GCP アカウント

- Cloud Run **サービス名は別**（例: `mirelia-sec-filings-mcp`）。ポート 8080/8081 はローカルのみ。
- 特許: `mirelia-structured-data-marketplace-*.run.app`  
- 金融: 新サービス URL を xpay upstream に登録。

---

## 2. finance-factory 側の正（MCP が読むデータ）

### 公開ビュー（クライアント / MCP 納品の正）

- **ビュー:** `fi_listings_portfolio`（`sql/fi_listings_portfolio_views.sql`）
- **1行 = 1提出** のフラット JSON（`agent_bundle` ネストは含めない）
- サンプル: `c:\AGS\finance-factory\upwork_sample.json`（ADM 10-Q）
- スキーマ: `fi-agent-bundle-2.5.0` / パイプライン `fi-v2.5.0`

### 主要列（MCP ツールが返してよいもの）

| 列 | 内容 |
|----|------|
| `document_id`, `cik`, `ticker`, `company_name` | 識別 |
| `form_type`, `fiscal_period`, `period_end`, `filed_date` | 提出メタ |
| `alpha_signals` | `causality_events` + evidence |
| `financial_metrics` | CompanyFacts + YoY |
| `agent_summary`, `agent_readiness_score` | 要約・品質 |
| `edgar_url`, `schema_version` | リンク・版 |

### 返してはいけないもの（内部）

- `fi_listings` 生テーブルの `agent_bundle`, `validation`, `r2_url`, `pipeline_version` 直出し
- 倉庫「在庫即納」の対外表現（Buyer 指定分を処理する体裁）

### Supabase クエリ例

```python
# 検索（ティッカー / フォーム）
supabase.table("fi_listings_portfolio").select(
    "document_id,ticker,company_name,form_type,fiscal_period,filed_date,agent_readiness_score"
).ilike("ticker", f"{ticker}%").limit(20)

# 1件サンプル（無料ツール）
supabase.table("fi_listings_portfolio").select("*").eq("document_id", doc_id).single()

# 購入後フル行
# 同上 select *
```

倉庫の新規処理は **finance-factory** 側。MCP は **読み取り + 既存行の販売** のみ（MVP）。

---

## 3. 金融 MCP MVP スコープ

### ツール 3 つ（固定）

| ツール | 役割 | 課金案 |
|--------|------|--------|
| `search_filings` | `ticker` / `form_type` / `limit` で `fi_listings_portfolio` を検索。軽量列のみ。 | xpay 低額 or $0 |
| `get_filing_sample` | **1件**の portfolio 行（短縮可: compact view 相当）。無料サンプル。 | **$0** |
| `purchase_filing` | `document_id` + x402 2段（特許 `purchase_single_patent` と同型）で **フル JSON** 返却。 | 例 **$5**（`.env2` の `FINANCE_FILING_PRICE_USD`） |

### ツール description の必須文言（Glama / エージェント向け）

- 数値は **SEC CompanyFacts**、ナラティブは **evidence_verified** 付き `causality_events`。
- `get_filing_sample` と `purchase_filing` の使い分けを明記。
- 402 フロー: **tx_hash を最初は空**、on-chain 後に再呼び出し。

### xpay 登録後

- slug 例: `mirelia-sec-filings`
- `search_*` / `get_filing_sample` → **$0 または $0.01**
- `purchase_filing` → データ本体価格 + xpay 手数料

---

## 4. 環境変数（`.env2`）

生成済み: **`c:\AGS\mcp-server-finance\.env2`**

| 変数 | ソース | 用途 |
|------|--------|------|
| `SUPABASE_URL` | finance-factory | DB |
| `SUPABASE_SERVICE_ROLE_KEY` | finance-factory | 読み取り（RLS バイパス） |
| `PORT` | 8081（特許とローカル競合回避） | uvicorn |
| `PUBLIC_MCP_URL` | xpay 発行後に合わせる | ドキュメント用 |
| `HMAC_SECRET`, `SELLER_WALLET_*`, `*_MAINNET`, `*_USDC`, `ERC20_ABI` | mcp-server | x402 |
| `FINANCE_SAMPLE_PRICE_USD` | 0 | サンプル |
| `FINANCE_FILING_PRICE_USD` | 5.00 | 単品 |
| `XPAY_API_KEY` | 手動 | xpay テスト（任意） |

ローカル実行前:

```powershell
cd c:\AGS\mcp-server-finance
copy .env2 .env
uv sync
uv run python mcp_server_finance.py   # 実装後
```

再生成: `uv run python scripts/build_env2.py`

---

## 5. 実装チェックリスト（順序）

1. [ ] `mcp-server` から `mcp_server_finance.py` を作成（特許ツール削除）
2. [ ] Supabase を `fi_listings_portfolio` のみに接続
3. [ ] 3ツール実装 + Pydantic Field description（英語・長め）
4. [ ] ローカル `http://127.0.0.1:8081/mcp` で `tools/list`
5. [ ] Cloud Run 新サービスデプロイ（`finance-factory` とは別）
6. [ ] xpay 新 slug 登録・upstream URL 設定・ツール価格
7. [ ] `llms.txt` SEC キーワード（10-K, 10-Q, EDGAR, CompanyFacts, evidence）
8. [ ] Glama / MCP Registry は **特許とは別 entry**

---

## 6. 関連パス一覧

```
c:\AGS\finance-factory\
  docs/HANDOFF_SPEC.md          # パイプライン仕様
  AIへの指示.md                  # Upwork 優先順
  sql/fi_listings_portfolio_views.sql
  tools/export_upwork_sample.py
  upwork_sample.json
  .env                          # Supabase 元

c:\AGS\mcp-server\
  mcp_server.py                 # x402 + FastMCP テンプレート
  README.md                     # xpay デプロイ手順
  .env                          # ウォレット・HMAC 元

c:\AGS\mcp-server-finance\       # ← 本作業場所
  MCP_FINANCE_BUILD.md          # 本ファイル
  .env2                         # 秘密情報（gitignore）
  scripts/build_env2.py
```

---

## 7. Upwork / Catalog との関係

- Upwork Catalog（SEC JSON）は **別チャネル**。MCP はエージェント・Claude Code 向け。
- 対外コピーは Catalog と整合（portfolio 行・PREVIEW の説明）。
- 在庫即納は MCP 文案にも書かない。

---

## 8. よくある間違い

| 間違い | 正 |
|--------|-----|
| 特許 Supabase テーブルを query | `fi_listings_portfolio` |
| 1 MCP に特許 + 金融ツール | slug / Cloud Run 分離 |
| `agent_bundle` をそのまま返す | portfolio フラット行 |
| xpay 無しで公開 URL だけ | まず xpay upstream 登録 |

---

*実装 PR 時は特許 `mcp-server` のコミット履歴を参照し、差分を金融専用に保つこと。*
