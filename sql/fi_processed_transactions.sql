-- x402 payment deduplication for SEC filings MCP (run in Supabase SQL Editor).

CREATE TABLE IF NOT EXISTS fi_processed_transactions (
  tx_hash TEXT PRIMARY KEY,
  network TEXT NOT NULL,
  package_tag TEXT NOT NULL,
  document_id TEXT NOT NULL,
  verified_at BIGINT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_fi_processed_transactions_document_id
  ON fi_processed_transactions (document_id);

CREATE INDEX IF NOT EXISTS idx_fi_processed_transactions_package_tag
  ON fi_processed_transactions (package_tag);

COMMENT ON TABLE fi_processed_transactions IS
  'On-chain purchase receipts for purchase_filing (MPP v1.0). One tx_hash per settlement.';
