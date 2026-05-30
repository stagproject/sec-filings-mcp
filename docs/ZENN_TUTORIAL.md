# Zenn 投稿用 — SEC EDGAR MCP を xpay キーなしで試す（5分）

**あなたがやること:** ① プロフィール設定 → ② 記事本文を貼る。  
**所要:** 初回 60〜90分（アカウント作成含む）。2回目以降は 15分。

---

## 自己紹介は日本語？英語？

| 場所 | おすすめ | 理由 |
|------|----------|------|
| **Zenn プロフィール** | **日本語** | Zenn の読者は日本語が中心 |
| **記事の冒頭** | **日本語** | 本文も日本語で統一 |
| **GitHub / awesome / xpay** | **英語**（済み） | 海外メンテ・レジストリ向け |

記事だけ日本語、技術リンクは英語、で問題ありません。下の **プロフィール用** と **記事冒頭用** をそのままコピペしてください。

---

## ① Zenn プロフィール（アカウント設定）

サインアップ後: **ダッシュボード** → 左 **設定** → **プロフィール**

| 項目 | コピペする内容 |
|------|----------------|
| **ユーザー名** | `stagproject`（GitHub と揃える・取れなければ近い名前） |
| **表示名** | `stagproject` |
| **自己紹介（160字目安）** | 下記ブロック |

### プロフィール自己紹介（コピペ用）

```text
SEC EDGAR 提出書類をエージェント向け JSON で扱う MCP「sec-filings-mcp」の開発・公開をしています。search → 無料 sample → x402 でフル JSON という三段構成。MCP Registry / Glama / xpay 掲載。エージェント・金融データ・MCP の接続点が好きです。
```

### プロフィール用リンク（任意）

| ラベル | URL |
|--------|-----|
| GitHub | https://github.com/stagproject |
| 本リポ | https://github.com/stagproject/sec-filings-mcp |
| Glama | https://glama.ai/mcp/servers/stagproject/sec-filings-mcp |

---

## ② Zenn 初めての手順（記事投稿）

1. https://zenn.dev に **GitHub / X / Google** でサインアップ（無料）
2. ① のプロフィールを保存
3. 右上アイコン → **ダッシュボード**
3. **新規投稿** → **テキストエディタで投稿**（GitHub 連携は今回不要）
4. **タイトル** に下記タイトルを貼る
5. 本文欄に「記事本文」をすべて貼る
6. 右または下の設定:
   - **公開設定:** 公開
   - **トピック（タグ）:** `MCP`, `SEC`, `EDGAR`, `AIエージェント`, `Cursor`（5つまで）
7. **プレビュー** で見た目確認
8. **投稿する**

投稿後: X や Discord `#showcase` に URL を1行貼ると余計な露出になる（任意）。

---

## 記事のメタ情報（Zenn 用）

| 項目 | 値 |
|------|-----|
| **タイトル** | xpay キーなしで SEC EDGAR MCP を試す（search → 無料 sample まで 5 分） |
| **トピック** | MCP, SEC, EDGAR, AIエージェント, Cursor |
| **スラッグ（URL）** | `sec-edgar-mcp-trial-no-xpay`（任意） |

---

--- ここから記事本文 ---

## 自己紹介

**stagproject** です。[sec-filings-mcp](https://github.com/stagproject/sec-filings-mcp) を公開・メンテしています。

米国 SEC の 10-K / 10-Q などを、LLM がそのまま使えるフラット JSON（CompanyFacts 由来の指標、提出書類メタデータ、エージェント向けサマリー）として配る MCP サーバーです。いまは **MCP Registry**・**Glama**・**xpay**（slug: `sec-edgar-filings`）に載せており、[awesome-mcp-servers への PR](https://github.com/punkpeye/awesome-mcp-servers/pull/7145) も出しています。

「エージェントが EDGAR を検索して、無料で中身を少し見て、必要なら x402 でフルデータを買う」——その最短ルートを、**xpay の API キーなし**で試せる手順をこの記事にまとめました。同じことを自分で調べるより短いはずなので、うまくいったらスター・Issue・感想をもらえると助かります。

---

## はじめに

SEC の 10-K / 10-Q をエージェント向け JSON で扱う MCP サーバー **[sec-filings-mcp](https://github.com/stagproject/sec-filings-mcp)** を、**xpay の API キーなし**で試す手順です。

- 本番（課金・計測）: [xpay](https://xpay.tools) 経由
- **今回の試用:** Cloud Run の upstream URL のみ（`search_filings` + `get_filing_sample`）

フルデータの購入（`purchase_filing`）は x402 USDC が別途必要なので、今回は触りません。

## 前提

- [Cursor](https://cursor.com/) または Claude Desktop など **MCP 対応クライアント**
- ネット接続

## 1. MCP 接続設定

クライアントの MCP 設定（`mcp.json` 相当）に次を追加します。

```json
{
  "mcpServers": {
    "sec-filings-trial": {
      "url": "https://sec-filings-mcp-1065601264332.us-central1.run.app/mcp"
    }
  }
}
```

`?key=` は **不要** です。

設定を保存したら MCP サーバーを **再接続**（Cursor なら Settings → MCP → 再起動 or Reload）。

## 2. ツール一覧の確認

エージェントに「sec-filings-trial の tools/list を実行して」と頼むか、クライアントの MCP パネルで次の 3 ツールが見えることを確認します。

| ツール | 用途 |
|--------|------|
| `search_filings` | 10-K / 10-Q などのカタログ検索 |
| `get_filing_sample` | 1件の無料プレビュー |
| `purchase_filing` | フル JSON（x402・今回は未使用） |

## 3. search_filings — Apple の 10-K を検索

ツール: `search_filings`  
引数:

```json
{
  "ticker": "AAPL",
  "form_type": "10-K",
  "limit": 3
}
```

**ポイント:** `ticker` / `form_type` / `company_name` / `fiscal_period` / `cik` の **いずれか1つ以上** が必須です（全件スキャン防止）。

返却 JSON の各行に `document_id` と `agent_readiness_score` があります。スコアが高い行を短リストの候補にします。

## 4. get_filing_sample — 無料プレビュー

手順 3 で得た `document_id` を使います。例:

```json
{
  "document_id": "0000320193-0001062998"
}
```

※ 実際の ID は search の結果に合わせて置き換えてください。空 `{}` でもデモ行が返る場合があります。

プレビューには `agent_summary` や `financial_metrics`（CompanyFacts 由来）が含まれます。`alpha_signals` / `causality_events` のフルセットは `purchase_filing` 側です。

## 5. 本番に進むとき（xpay）

試用の次のステップ:

1. [xpay.tools](https://xpay.tools) で API キー取得（無料クレジットあり）
2. MCP URL を差し替え:

```text
https://sec-edgar-filings.mcp.xpay.sh/mcp?key=YOUR_XPAY_KEY
```

3. ダッシュボードで `search_filings` / `get_filing_sample` を **$0** にしておくと試しやすいです

## ブラウザだけで試す（Cursor なし）

[Glama](https://glama.ai/mcp/servers/stagproject/sec-filings-mcp) の **Try in Browser** から同じツールをサンドボックス実行できます（本番ウォレットは使いません）。

## リンク集

| 用途 | URL |
|------|-----|
| GitHub | https://github.com/stagproject/sec-filings-mcp |
| 試用ドキュメント | https://github.com/stagproject/sec-filings-mcp/blob/main/docs/TRY_WITHOUT_XPAY.md |
| Glama | https://glama.ai/mcp/servers/stagproject/sec-filings-mcp |
| MCP Registry | `io.github.stagproject/sec-filings-mcp` |
| awesome-mcp-servers PR | https://github.com/punkpeye/awesome-mcp-servers/pull/7145 |

## まとめ

- **xpay キーなし**でも Cloud Run upstream で **検索 + 無料サンプル** まで試せる
- 本番トラフィック・課金は xpay 経由が推奨
- フィードバックは [GitHub Issues](https://github.com/stagproject/sec-filings-mcp/issues) または xpay Discord の `#showcase` へ歓迎

## おわりに

次は xpay キーを取って本番 URL に繋ぐか、`purchase_filing` で x402 フル JSON まで試すか、は需要次第で記事にします。質問は Issue か Zenn のコメントでどうぞ。

---

### 英語1行（プロフィールや X 用・記事には不要）

```text
Maintainer of sec-filings-mcp — agent-native SEC EDGAR JSON (search, free sample, x402 full row). MCP Registry · Glama · xpay.
```

--- ここまで記事本文 ---

## 投稿後チェックリスト

- [ ] 公開 URL を控えた
- [ ] GitHub README の Discussions または X に URL を1行（任意）
- [ ] 1週間後: xpay ダッシュボードで tool call が増えたか見る
