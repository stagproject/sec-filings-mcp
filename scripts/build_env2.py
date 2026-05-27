"""Merge finance-factory + patent mcp-server env into .env2 (run once locally)."""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# Override with FINANCE_FACTORY_ENV / MCP_PATENT_ENV if not using default local paths.
FF_ENV = Path(os.environ.get("FINANCE_FACTORY_ENV", r"c:\AGS\finance-factory\.env"))
PAT_ENV = Path(os.environ.get("MCP_PATENT_ENV", r"c:\AGS\mcp-server\.env"))
OUT = ROOT / ".env2"


def load_env(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        out[key.strip()] = val.strip().strip('"').strip("'")
    return out


def main() -> None:
    ff = load_env(FF_ENV)
    pat = load_env(PAT_ENV)
    if "HMAC_SECRET" not in pat and "SIGNATURE_SECRET" in ff:
        pat["HMAC_SECRET"] = ff["SIGNATURE_SECRET"]

    lines = [
        "# mcp-server-finance — local secrets (gitignored). Copy: cp .env2 .env",
        "# Sources: finance-factory/.env (Supabase) + mcp-server/.env (x402)",
        "",
        "# --- Supabase (fi_listings_portfolio) ---",
    ]
    for key in ("SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY"):
        lines.append(f"{key}={ff.get(key, '')}")

    lines += [
        "",
        "# --- HTTP server ---",
        "PORT=8081",
        "PUBLIC_MCP_URL=https://sec-edgar-filings.mcp.xpay.sh/mcp",
        "",
        "# --- x402 (reuse patent MCP wallet config) ---",
    ]
    for key in (
        "HMAC_SECRET",
        "SELLER_WALLET_ADDRESS",
        "BASE_MAINNET",
        "POLYGON_MAINNET",
        "OASIS_MAINNET",
        "BASE_USDC",
        "POLYGON_USDC",
        "OASIS_WROSE",
        "ERC20_ABI",
    ):
        if pat.get(key):
            lines.append(f"{key}={pat[key]}")

    lines += [
        "",
        "# --- Finance MCP pricing ---",
        "FINANCE_SAMPLE_PRICE_USD=0",
        "FINANCE_FILING_PRICE_USD=5.00",
        "",
        "# --- xpay publisher (after slug registration) ---",
        "XPAY_API_KEY=",
    ]

    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
