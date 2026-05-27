"""Automated SEC filings MCP test suite (xpay + optional on-chain E2E).

  uv run python test_finance_mcp.py
  uv run python test_finance_mcp.py --e2e
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from dotenv import load_dotenv
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

ROOT = Path(__file__).resolve().parent
PATENT_ENV = Path(r"c:\AGS\mcp-server\.env")

load_dotenv(ROOT / ".env")
if not os.environ.get("CLIENT_PRIVATE_KEY") and PATENT_ENV.exists():
    load_dotenv(PATENT_ENV, override=False)

DIRECT_URL = os.environ.get(
    "MCP_DIRECT_URL",
    "https://sec-filings-mcp-1065601264332.us-central1.run.app/mcp",
)
PUBLIC_MCP_URL = os.environ.get(
    "PUBLIC_MCP_URL", "https://sec-edgar-filings.mcp.xpay.sh/mcp"
)
XPAY_KEY = os.environ.get("XPAY_API_KEY", "").strip()
SAMPLE_DOC = "000000708426000023"
OUT_DIR = ROOT / "test_results"


def mcp_url(base: str, use_xpay_key: bool) -> str:
    base = base.rstrip("/")
    if use_xpay_key and XPAY_KEY and "key=" not in base:
        return f"{base}?key={XPAY_KEY}"
    return base


def parse_tool_json(text: str) -> Any:
    return json.loads(text.split("\n---")[0].strip())


def search_rows(data: Any) -> list:
    if isinstance(data, dict) and "rows" in data:
        return data["rows"]
    if isinstance(data, list):
        return data
    return []


@dataclass
class CaseResult:
    name: str
    ok: bool
    detail: str = ""
    data: Any = None


@dataclass
class RunReport:
    channel: str
    results: list[CaseResult] = field(default_factory=list)

    def add(self, name: str, ok: bool, detail: str = "", data: Any = None) -> None:
        self.results.append(CaseResult(name, ok, detail, data))

    @property
    def passed(self) -> int:
        return sum(1 for r in self.results if r.ok)

    @property
    def failed(self) -> int:
        return sum(1 for r in self.results if not r.ok)


async def run_cases(session: ClientSession, report: RunReport) -> None:
    # --- tools/list ---
    tools = await session.list_tools()
    names = {t.name for t in tools.tools}
    expected = {"search_filings", "get_filing_sample", "purchase_filing"}
    report.add(
        "tools_list",
        names == expected,
        f"got {sorted(names)}",
    )

    # --- search_filings ---
    patterns = [
        ("search_ticker_adm", {"ticker": "ADM", "limit": 3}),
        ("search_form_10q", {"ticker": "ADM", "form_type": "10-Q", "limit": 2}),
        ("search_limit_1", {"ticker": "AAPL", "limit": 1}),
        ("search_unknown_ticker", {"ticker": "ZZZZNOTICK", "limit": 5}),
        ("search_no_filter_rejected", {"limit": 5}),
        ("search_one_liner", {"ticker": "ADM", "limit": 1, "include_one_liner": True}),
        ("search_pagination", {"ticker": "ADM", "limit": 1, "offset": 0}),
    ]
    first_doc: Optional[str] = None
    for pname, args in patterns:
        res = await session.call_tool("search_filings", arguments=args)
        data = parse_tool_json(res.content[0].text)
        if pname == "search_no_filter_rejected":
            report.add(
                pname,
                isinstance(data, dict) and "error" in data,
                str(data.get("error", ""))[:80],
            )
            continue
        if isinstance(data, dict) and "error" in data:
            report.add(pname, False, data["error"])
            continue
        rows = search_rows(data)
        ok = isinstance(data, dict) and "workflow_next" in data and isinstance(rows, list)
        if pname == "search_one_liner" and rows:
            ok = ok and bool(rows[0].get("agent_one_liner"))
        if ok and rows and not first_doc:
            first_doc = rows[0].get("document_id")
        report.add(pname, ok, f"rows={len(rows)}")

    doc_id = first_doc or SAMPLE_DOC

    # --- get_filing_sample ---
    for pname, args in [
        ("sample_default", {}),
        ("sample_by_id", {"document_id": doc_id}),
        ("sample_invalid_id", {"document_id": "000000000000000000"}),
    ]:
        res = await session.call_tool("get_filing_sample", arguments=args)
        data = parse_tool_json(res.content[0].text)
        if pname == "sample_invalid_id":
            ok = isinstance(data, dict) and "error" in data
            report.add(pname, ok, str(data.get("error", data))[:80])
        else:
            ok = data.get("preview") is True and "data" in data
            has_summary = ok and "agent_summary" in (data.get("data") or {})
            report.add(pname, ok and has_summary, f"doc={data.get('document_id')}")

    # --- purchase_filing (402 / errors only; no chain spend) ---
    res = await session.call_tool(
        "purchase_filing",
        arguments={"document_id": doc_id, "network": "polygon"},
    )
    p402 = parse_tool_json(res.content[0].text)
    amt = (p402.get("payment_request") or {}).get("amount")
    report.add(
        "purchase_402",
        p402.get("status") == 402 and amt is not None,
        f"status=402 amount={amt}",
    )

    res = await session.call_tool(
        "purchase_filing",
        arguments={"document_id": "000000000000000000", "network": "polygon"},
    )
    bad_doc = parse_tool_json(res.content[0].text)
    report.add(
        "purchase_missing_doc",
        "error" in bad_doc,
        str(bad_doc.get("error", ""))[:80],
    )

    fake_hash = "0x" + "ab" * 32
    res = await session.call_tool(
        "purchase_filing",
        arguments={
            "document_id": doc_id,
            "network": "polygon",
            "tx_hash": fake_hash,
        },
    )
    fake_tx = parse_tool_json(res.content[0].text)
    ok_fake = fake_tx.get("status") == "pending" or "error" in fake_tx
    report.add("purchase_fake_tx", ok_fake, str(fake_tx)[:100])


async def run_e2e_purchase(session: ClientSession, report: RunReport) -> None:
    from web3 import Web3

    try:
        from web3.middleware import ExtraDataToPOAMiddleware as poa_middleware
    except ImportError:
        from web3.middleware import geth_poa_middleware as poa_middleware

    pk = os.environ.get("CLIENT_PRIVATE_KEY", "").strip()
    if not pk:
        report.add("e2e_purchase", False, "CLIENT_PRIVATE_KEY not set (skip)")
        return

    rpc = os.environ.get("POLYGON_MAINNET")
    if not rpc:
        report.add("e2e_purchase", False, "POLYGON_MAINNET missing")
        return

    res = await session.call_tool(
        "search_filings", arguments={"ticker": "ADM", "limit": 1}
    )
    parsed = parse_tool_json(res.content[0].text)
    rows = search_rows(parsed)
    if not rows:
        report.add("e2e_purchase", False, "no ADM row for purchase")
        return
    doc_id = rows[0]["document_id"]

    res = await session.call_tool(
        "purchase_filing",
        arguments={"document_id": doc_id, "network": "polygon"},
    )
    data = parse_tool_json(res.content[0].text)
    if data.get("status") != 402:
        report.add("e2e_purchase", False, f"no 402: {data}")
        return

    payload = data["payment_request"]["transaction_payload"]
    w3 = Web3(Web3.HTTPProvider(rpc))
    w3.middleware_onion.inject(poa_middleware, layer=0)
    acct = w3.eth.account.from_key(pk)

    nonce = w3.eth.get_transaction_count(acct.address, "pending")
    tx_draft = {
        "nonce": nonce,
        "to": w3.to_checksum_address(payload["to"]),
        "value": int(payload["value"]),
        "data": payload["data"],
        "gasPrice": w3.eth.gas_price,
        "chainId": w3.eth.chain_id,
    }
    try:
        tx_draft["gas"] = int(w3.eth.estimate_gas(tx_draft) * 1.2)
    except Exception:
        tx_draft["gas"] = 200000

    signed = acct.sign_transaction(tx_draft)
    tx_hash = w3.to_hex(w3.eth.send_raw_transaction(signed.rawTransaction))
    report.add("e2e_tx_sent", True, f"hash={tx_hash[:18]}...")

    args = {"document_id": doc_id, "network": "polygon", "tx_hash": tx_hash}
    final = None
    for _ in range(20):
        await asyncio.sleep(8)
        res = await session.call_tool("purchase_filing", arguments=args)
        final = parse_tool_json(res.content[0].text)
        if final.get("status") == "pending":
            continue
        break

    delivered = isinstance(final, dict) and final.get("data")
    report.add(
        "e2e_purchase",
        bool(delivered),
        "delivered" if delivered else str(final)[:120],
        final if delivered else None,
    )


def _format_exc(e: BaseException) -> str:
    if isinstance(e, BaseExceptionGroup):
        return "; ".join(_format_exc(x) for x in e.exceptions)
    return f"{type(e).__name__}: {e}"


async def run_channel(label: str, url: str, run_e2e: bool) -> RunReport:
    report = RunReport(channel=label)
    base = url.split("?")[0]
    print(f"\n=== {label} ===\n  {base}?key=...")
    last_err = ""
    for attempt in range(1, 4):
        try:
            async with streamablehttp_client(url) as (read, write, _):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    await run_cases(session, report)
                    if run_e2e:
                        await run_e2e_purchase(session, report)
            return report
        except BaseException as e:
            last_err = _format_exc(e)
            if attempt < 3:
                await asyncio.sleep(2 * attempt)
    report.add("connection", False, last_err[:500])
    return report


def save_reports(reports: list[RunReport]) -> Path:
    OUT_DIR.mkdir(exist_ok=True)
    ts = time.strftime("%Y%m%d_%H%M%S")
    out = OUT_DIR / f"finance_mcp_{ts}.json"
    payload = {
        r.channel: {
            "passed": r.passed,
            "failed": r.failed,
            "cases": [
                {"name": c.name, "ok": c.ok, "detail": c.detail}
                for c in r.results
            ],
        }
        for r in reports
    }
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return out


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--e2e",
        action="store_true",
        help="Run one real Polygon purchase (gas + ~FINANCE_FILING_PRICE_USD USDC)",
    )
    parser.add_argument("--xpay-only", action="store_true")
    parser.add_argument("--direct-only", action="store_true")
    args = parser.parse_args()

    reports: list[RunReport] = []

    if not args.direct_only:
        if not XPAY_KEY:
            r = RunReport(channel="xpay_proxy")
            r.add(
                "connection",
                False,
                "XPAY_API_KEY empty in .env — paste full xpay_sk_... key",
            )
            reports.append(r)
            print("\n[!] XPAY_API_KEY is empty in .env (value after = has length 0).")
            print("    Copy the full key from xpay Settings > API Keys into .env")
        else:
            reports.append(
                await run_channel(
                    "xpay_proxy",
                    mcp_url(PUBLIC_MCP_URL, True),
                    args.e2e,
                )
            )

    if not args.xpay_only:
        reports.append(
            await run_channel(
                "direct_cloud_run",
                mcp_url(DIRECT_URL, False),
                args.e2e and not XPAY_KEY,
            )
        )

    out = save_reports(reports)
    print(f"\n--- Summary (saved {out.name}) ---")
    exit_code = 0
    for r in reports:
        print(f"  {r.channel}: {r.passed} passed, {r.failed} failed")
        for c in r.results:
            mark = "OK" if c.ok else "FAIL"
            detail = c.detail[:90].encode("ascii", "replace").decode("ascii")
            print(f"    [{mark}] {c.name}: {detail}")
            if not c.ok:
                exit_code = 1
    return exit_code


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
