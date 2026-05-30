import os
import json
import time
import hmac
import hashlib
import uvicorn
from typing import Any, Optional

import requests
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from pydantic import Field
from starlette.applications import Starlette
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import FileResponse
from starlette.routing import Mount, Route
from supabase import Client, create_client
from web3 import Web3

try:
    from web3.middleware import ExtraDataToPOAMiddleware as poa_middleware
except ImportError:
    from web3.middleware import geth_poa_middleware as poa_middleware

load_dotenv()

DEFAULT_SAMPLE_DOCUMENT_ID = "000000708426000023"

security_settings = TransportSecuritySettings(enable_dns_rebinding_protection=False)
mcp = FastMCP(
    "SEC Filings Agent Marketplace",
    instructions=(
        "SEC EDGAR structured filings (10-K, 10-Q, 8-K) for equity research and agent workflows. "
        "Workflow: (1) search_filings with at least one filter — lightweight catalog; "
        "(2) get_filing_sample on a document_id — free compact preview; "
        "(3) purchase_filing — full JSON after x402 USDC on polygon. "
        "Never purchase without searching first. Paginate search with offset."
    ),
    website_url="https://github.com/stagproject/sec-filings-mcp",
    transport_security=security_settings,
)

PUBLIC_MCP_URL = os.environ.get("PUBLIC_MCP_URL", "https://sec-edgar-filings.mcp.xpay.sh/mcp")

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase: Optional[Client] = create_client(url, key) if url and key else None

rpc_base = os.environ.get("BASE_MAINNET")
rpc_polygon = os.environ.get("POLYGON_MAINNET")
rpc_oasis = os.environ.get("OASIS_MAINNET")
usdc_base_raw = os.environ.get("BASE_USDC")
usdc_polygon_raw = os.environ.get("POLYGON_USDC")
wrose_raw = os.environ.get("OASIS_WROSE")
abi_string = os.environ.get("ERC20_ABI")
WALLET_ADDRESS_RAW = os.environ.get("SELLER_WALLET_ADDRESS")
HMAC_SECRET = os.environ.get("HMAC_SECRET", "default_insecure_mcp_secret_change_in_production").encode()

FILING_PRICE_USD = float(os.environ.get("FINANCE_FILING_PRICE_USD", "5.00"))

chains = {}
if Web3 and abi_string and WALLET_ADDRESS_RAW:
    WALLET_ADDRESS = Web3.to_checksum_address(WALLET_ADDRESS_RAW)
    ERC20_ABI = json.loads(abi_string)

    if rpc_base and usdc_base_raw:
        w3_base = Web3(Web3.HTTPProvider(rpc_base))
        chains["base"] = {
            "w3": w3_base,
            "usdc": w3_base.eth.contract(
                address=Web3.to_checksum_address(usdc_base_raw), abi=ERC20_ABI
            ),
            "type": "erc20",
            "confs": 2,
        }

    if rpc_polygon and usdc_polygon_raw:
        w3_polygon = Web3(Web3.HTTPProvider(rpc_polygon))
        w3_polygon.middleware_onion.inject(poa_middleware, layer=0)
        chains["polygon"] = {
            "w3": w3_polygon,
            "usdc": w3_polygon.eth.contract(
                address=Web3.to_checksum_address(usdc_polygon_raw), abi=ERC20_ABI
            ),
            "type": "erc20",
            "confs": 15,
        }

    if rpc_oasis:
        w3_oasis = Web3(Web3.HTTPProvider(rpc_oasis))
        w3_oasis.middleware_onion.inject(poa_middleware, layer=0)
        chains["oasis"] = {"w3": w3_oasis, "usdc": None, "type": "native", "confs": 2}
        if wrose_raw:
            chains["oasis"]["w_token"] = w3_oasis.eth.contract(
                address=Web3.to_checksum_address(wrose_raw), abi=ERC20_ABI
            )
else:
    WALLET_ADDRESS = None


def generate_payment_memo(package_tag: str, amount_raw: int) -> str:
    msg = f"{package_tag}:{amount_raw}".encode()
    return hmac.new(HMAC_SECRET, msg, hashlib.sha256).hexdigest()


def is_valid_tx_hash(h: str) -> bool:
    return isinstance(h, str) and h.startswith("0x") and len(h) == 66


def _str_arg(value: Optional[str]) -> Optional[str]:
    """Normalize tool args when invoked outside the MCP runtime."""
    if value is None or not isinstance(value, str):
        return None
    s = value.strip()
    return s or None


def _int_arg(value: Optional[int], default: int) -> int:
    if isinstance(value, int):
        return value
    return default


def _bool_arg(value: Any, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    return default


def filing_package_tag(document_id: str) -> str:
    return f"FILING_{document_id}"


class MPPMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        return await call_next(request)


SEARCH_COLUMNS = (
    "document_id,cik,ticker,company_name,form_type,fiscal_period,"
    "period_end,filed_date,agent_readiness_score,edgar_url"
)


def _extract_one_liner(agent_summary: Any) -> Optional[str]:
    if agent_summary is None:
        return None
    if isinstance(agent_summary, str):
        try:
            agent_summary = json.loads(agent_summary)
        except json.JSONDecodeError:
            return None
    if isinstance(agent_summary, dict):
        line = agent_summary.get("agent_one_liner")
        return str(line)[:280] if line else None
    return None


@mcp.tool()
def search_filings(
    ticker: Optional[str] = Field(
        default=None,
        description="Ticker prefix, case-insensitive (e.g. AAPL, MSFT). At least one filter required.",
    ),
    form_type: Optional[str] = Field(
        default=None,
        description="SEC form: 10-K, 10-Q, 8-K, etc.",
    ),
    company_name: Optional[str] = Field(
        default=None,
        description="Substring match on company_name (e.g. Apple, Archer-Daniels).",
    ),
    fiscal_period: Optional[str] = Field(
        default=None,
        description="Fiscal period label (e.g. 2026Q1, 2025FY).",
    ),
    cik: Optional[str] = Field(
        default=None,
        description="SEC CIK prefix (digits, e.g. 0000320193).",
    ),
    min_agent_readiness_score: Optional[int] = Field(
        default=None,
        description="Minimum agent_readiness_score (0–100). Use 70+ for production-quality rows.",
    ),
    limit: Optional[int] = Field(
        default=10,
        description="Page size (1–100). Default 10 keeps payloads small for LLM context.",
    ),
    offset: Optional[int] = Field(
        default=0,
        description="Skip rows for pagination (e.g. 10 for page 2 when limit=10).",
    ),
    include_one_liner: Optional[bool] = Field(
        default=False,
        description=(
            "If true, adds agent_one_liner (~1 sentence) per row for triage without calling "
            "get_filing_sample. Slightly heavier response."
        ),
    ),
) -> str:
    """
    PRIMARY discovery tool — lightweight catalog over 10k+ SEC filings (fi_listings_portfolio).
    [COST: low xpay per-call fee]
    Does NOT return alpha_signals, causality_events, or financial_metrics (use get_filing_sample / purchase_filing).
    Always returns agent_readiness_score (higher = better structured data) and edgar_url.

    Required: at least one of ticker, form_type, company_name, fiscal_period, cik (avoids full-table scans).

    Agent workflow after this call:
    1. Shortlist by agent_readiness_score and optional agent_one_liner
    2. get_filing_sample(document_id) — free preview
    3. purchase_filing(document_id) — paid full JSON (x402)

    [EXAMPLE ARGUMENTS - MINIMAL]:
    {"ticker": "AAPL", "limit": 5}

    [EXAMPLE ARGUMENTS - MAXIMAL]:
    {
      "ticker": "ADM",
      "form_type": "10-Q",
      "company_name": "Archer",
      "fiscal_period": "2026Q1",
      "min_agent_readiness_score": 70,
      "limit": 20,
      "offset": 0,
      "include_one_liner": true
    }

    [EXAMPLE ARGUMENTS - PAGINATION (page 2)]:
    {"ticker": "MSFT", "form_type": "10-K", "limit": 10, "offset": 10}
    """
    if not supabase:
        return json.dumps({"error": "Database connection failed"}, ensure_ascii=False)
    try:
        ticker_q = _str_arg(ticker)
        form_q = _str_arg(form_type)
        company_q = _str_arg(company_name)
        fiscal_q = _str_arg(fiscal_period)
        cik_q = _str_arg(cik)
        if not any([ticker_q, form_q, company_q, fiscal_q, cik_q]):
            return json.dumps(
                {
                    "error": "At least one filter required (ticker, form_type, company_name, fiscal_period, or cik).",
                    "catalog_size_hint": "10000+ filings — unfiltered browse is disabled.",
                    "example_minimal": {"ticker": "AAPL", "limit": 5},
                    "example_maximal": {
                        "ticker": "ADM",
                        "form_type": "10-Q",
                        "fiscal_period": "2026Q1",
                        "min_agent_readiness_score": 70,
                        "limit": 20,
                        "include_one_liner": True,
                    },
                },
                ensure_ascii=False,
            )

        want_liner = _bool_arg(include_one_liner, False)
        select_cols = SEARCH_COLUMNS + (",agent_summary" if want_liner else "")
        query = supabase.table("fi_listings_portfolio").select(select_cols)
        if ticker_q:
            query = query.ilike("ticker", f"{ticker_q.upper()}%")
        if form_q:
            query = query.eq("form_type", form_q.upper())
        if company_q:
            safe_co = company_q.replace("%", "").replace("_", "")
            query = query.ilike("company_name", f"%{safe_co}%")
        if fiscal_q:
            query = query.eq("fiscal_period", fiscal_q)
        if cik_q:
            query = query.ilike("cik", f"{cik_q}%")
        if min_agent_readiness_score is not None and isinstance(
            min_agent_readiness_score, int
        ):
            query = query.gte("agent_readiness_score", min_agent_readiness_score)

        safe_limit = max(1, min(_int_arg(limit, 10), 100))
        safe_offset = max(0, _int_arg(offset, 0))

        res = (
            query.order("filed_date", desc=True)
            .order("agent_readiness_score", desc=True)
            .range(safe_offset, safe_offset + safe_limit - 1)
            .execute()
        )
        rows = []
        for raw in res.data or []:
            row = {k: v for k, v in raw.items() if k != "agent_summary"}
            if want_liner:
                line = _extract_one_liner(raw.get("agent_summary"))
                if line:
                    row["agent_one_liner"] = line
            rows.append(row)

        return json.dumps(
            {
                "rows": rows,
                "count": len(rows),
                "limit": safe_limit,
                "offset": safe_offset,
                "next_offset": safe_offset + len(rows) if len(rows) == safe_limit else None,
                "workflow_next": "get_filing_sample(document_id) then purchase_filing(document_id)",
                "sort": "filed_date desc, agent_readiness_score desc",
            },
            ensure_ascii=False,
        )
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


@mcp.tool()
def get_filing_sample(
    document_id: Optional[str] = Field(
        default=None,
        description=(
            "document_id from search_filings. "
            f"Defaults to demo ADM 10-Q ({DEFAULT_SAMPLE_DOCUMENT_ID})."
        ),
    ),
) -> str:
    """
    Free preview of one SEC filing (agent-friendly compact row from fi_listings_portfolio_compact).
    [COST: $0]
    Includes agent_summary and financial_metrics (CompanyFacts-derived) but NOT full
    alpha_signals / causality_events — those ship only via purchase_filing after x402 payment.
    Compare with purchase_filing: sample = evaluate quality; purchase = full evidence-backed JSON.

    [EXAMPLE ARGUMENTS - MINIMAL]:
    {}

    [EXAMPLE ARGUMENTS - MAXIMAL]:
    {"document_id": "000000708426000023"}
    """
    if not supabase:
        return json.dumps({"error": "Database connection failed"}, ensure_ascii=False)
    doc_id = _str_arg(document_id) or DEFAULT_SAMPLE_DOCUMENT_ID
    try:
        res = (
            supabase.table("fi_listings_portfolio_compact")
            .select("*")
            .eq("document_id", doc_id)
            .limit(1)
            .execute()
        )
        if not res.data:
            return json.dumps(
                {"error": f"document_id '{doc_id}' not found in portfolio."},
                ensure_ascii=False,
            )
        row = res.data[0]
        return json.dumps(
            {
                "preview": True,
                "schema_version": row.get("schema_version"),
                "document_id": row.get("document_id"),
                "data": row,
                "upgrade": "Call purchase_filing with this document_id for full alpha_signals and causality_events.",
            },
            ensure_ascii=False,
        )
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


@mcp.tool()
def purchase_filing(
    document_id: str = Field(description="document_id from search_filings or get_filing_sample."),
    network: Optional[str] = Field(
        default="polygon",
        description="Blockchain network. Default polygon (USDC). Also supports base.",
    ),
    tx_hash: Optional[str] = Field(
        default=None,
        description="Transaction hash. LEAVE EMPTY on first call to receive 402 payment instructions.",
    ),
) -> str:
    """
    Purchase and deliver one full SEC filing row from fi_listings_portfolio (MPP v1.0 x402).
    [COST: xpay per-call + on-chain USDC data price (see FINANCE_FILING_PRICE_USD)]
    Full JSON includes alpha_signals with evidence_verified causality_events and financial_metrics
    from SEC CompanyFacts. Do NOT return agent_bundle or internal pipeline fields.

    [AGENTIC WORKFLOW — mandatory 2-step 402 flow]:
    STEP 1: Call with document_id and network only; leave tx_hash EMPTY.
    STEP 2: Broadcast the exact transaction_payload on-chain (polygon USDC default).
    STEP 3: Call again with the same document_id, network, and confirmed tx_hash (66 chars).

    [EXAMPLE ARGUMENTS - MINIMAL (Step 1 — payment info)]:
    {"document_id": "000000708426000023", "network": "polygon"}

    [EXAMPLE ARGUMENTS - MAXIMAL (Step 3 — claim data)]:
    {
      "document_id": "000000708426000023",
      "network": "polygon",
      "tx_hash": "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
    }
    """
    if not supabase:
        return json.dumps({"error": "Supabase connection failed"}, ensure_ascii=False)
    net_key = (_str_arg(network) or "polygon").lower()
    if net_key not in chains:
        return json.dumps({"error": f"Unsupported network: {net_key}"}, ensure_ascii=False)

    doc_id = _str_arg(document_id)
    if not doc_id:
        return json.dumps({"error": "document_id is required."}, ensure_ascii=False)
    expected_tag = filing_package_tag(doc_id)
    chain_info = chains[net_key]

    tx = _str_arg(tx_hash)
    if tx:
        if not is_valid_tx_hash(tx):
            return json.dumps({"error": "Invalid tx_hash format."}, ensure_ascii=False)

    try:
        check_res = (
            supabase.table("fi_listings_portfolio")
            .select("document_id")
            .eq("document_id", doc_id)
            .limit(1)
            .execute()
        )
        if not check_res.data:
            return json.dumps(
                {"error": f"document_id '{doc_id}' not found."}, ensure_ascii=False
            )
    except Exception:
        return json.dumps(
            {
                "status": "pending",
                "message": "Database temporarily busy. Please wait 15 seconds and retry.",
            },
            ensure_ascii=False,
        )

    if not tx:
        try:
            required_raw = int(FILING_PRICE_USD * (10**6))
            memo_hex = generate_payment_memo(expected_tag, required_raw)
            base_calldata = chain_info["usdc"].encodeABI(
                fn_name="transfer", args=[WALLET_ADDRESS, required_raw]
            )
            tx_data = base_calldata + memo_hex
            tx_payload = {"to": chain_info["usdc"].address, "value": "0", "data": tx_data}
        except Exception as e:
            return json.dumps(
                {
                    "status": "pending",
                    "message": f"Service temporarily busy ({str(e)}). Retry in 15s.",
                },
                ensure_ascii=False,
            )

        return json.dumps(
            {
                "status": 402,
                "message": "Payment Required",
                "payment_request": {
                    "mpp_version": "1.0",
                    "destination": WALLET_ADDRESS,
                    "amount": FILING_PRICE_USD,
                    "asset": "USDC",
                    "network": net_key,
                    "description": f"Purchase SEC filing: {doc_id}",
                    "transaction_payload": tx_payload,
                    "instruction": (
                        "Broadcast transaction_payload exactly, then call purchase_filing "
                        "again with tx_hash after confirmation."
                    ),
                },
            },
            ensure_ascii=False,
        )

    current_time = int(time.time())

    try:
        tx_check = (
            supabase.table("fi_processed_transactions")
            .select("*")
            .eq("tx_hash", tx)
            .execute()
        )
        if tx_check.data:
            if tx_check.data[0]["package_tag"] == expected_tag:
                full = (
                    supabase.table("fi_listings_portfolio")
                    .select("*")
                    .eq("document_id", doc_id)
                    .limit(1)
                    .execute()
                )
                return json.dumps(
                    {
                        "system_log": "Verified. Data delivered.",
                        "data": full.data,
                    },
                    ensure_ascii=False,
                )
            return json.dumps(
                {"error": "Transaction already used for a different product."},
                ensure_ascii=False,
            )
    except Exception:
        return json.dumps(
            {
                "status": "pending",
                "message": "Database temporarily busy. Please wait 15 seconds and retry.",
            },
            ensure_ascii=False,
        )

    w3 = chain_info["w3"]
    try:
        receipt = w3.eth.get_transaction_receipt(tx)
        if receipt is None:
            return json.dumps(
                {
                    "status": "pending",
                    "message": "Transaction pending. Wait 15 seconds and retry.",
                },
                ensure_ascii=False,
            )
        if receipt["status"] != 1:
            return json.dumps({"error": "Transaction failed on-chain"}, ensure_ascii=False)

        current_block = w3.eth.block_number
        tx_block = receipt["blockNumber"]
        req_confs = chain_info["confs"]
        if (current_block - tx_block) < req_confs:
            return json.dumps(
                {
                    "status": "pending",
                    "message": f"Awaiting confirmations ({current_block - tx_block}/{req_confs}).",
                },
                ensure_ascii=False,
            )

        chain_tx = w3.eth.get_transaction(tx)
        tx_input_str = (
            chain_tx["input"].hex()
            if hasattr(chain_tx["input"], "hex")
            else str(chain_tx["input"])
        )
    except Exception as e:
        err_str = str(e).lower()
        if "not found" in err_str or "unknown" in err_str:
            return json.dumps(
                {
                    "status": "pending",
                    "message": "Transaction not yet confirmed. Wait and retry.",
                },
                ensure_ascii=False,
            )
        return json.dumps(
            {"status": "pending", "message": f"RPC busy ({str(e)}). Retry in 15s."},
            ensure_ascii=False,
        )

    payment_found = False
    try:
        events = chain_info["usdc"].events.Transfer().process_receipt(receipt)
        for event in events:
            if event["args"]["to"].lower() == WALLET_ADDRESS.lower():
                actual_amount = event["args"]["value"]
                expected_memo = generate_payment_memo(expected_tag, actual_amount)
                if expected_memo in tx_input_str:
                    payment_found = True
                    break
    except Exception as e:
        return json.dumps(
            {
                "status": "pending",
                "message": f"Payment verification busy ({str(e)}). Retry in 15s.",
            },
            ensure_ascii=False,
        )

    if not payment_found:
        return json.dumps(
            {
                "error": "Valid payment not found (memo mismatch or insufficient amount)."
            },
            ensure_ascii=False,
        )

    try:
        supabase.table("fi_processed_transactions").insert(
            {
                "tx_hash": tx,
                "network": net_key,
                "package_tag": expected_tag,
                "document_id": doc_id,
                "verified_at": current_time,
            }
        ).execute()
    except Exception:
        pass

    try:
        full = (
            supabase.table("fi_listings_portfolio")
            .select("*")
            .eq("document_id", doc_id)
            .limit(1)
            .execute()
        )
        return json.dumps(
            {"system_log": "Verified. Data delivered.", "data": full.data},
            ensure_ascii=False,
        )
    except Exception:
        return json.dumps(
            {
                "status": "pending",
                "message": "Database busy delivering data. Retry in 15s.",
            },
            ensure_ascii=False,
        )


if __name__ == "__main__":
    import sys

    is_cloud_run = "K_SERVICE" in os.environ
    if is_cloud_run or "--sse" in sys.argv:
        port = int(os.environ.get("PORT", 8080))
        mcp_asgi_app = mcp.streamable_http_app()

        async def ping_handler(request):
            from starlette.responses import JSONResponse

            return JSONResponse({"status": "ok"})

        async def root_handler(request):
            from starlette.responses import JSONResponse

            if request.method == "POST":
                try:
                    payload = await request.json()
                    print(f"[Webhook Received JSON] {payload}")
                except Exception:
                    raw_body = await request.body()
                    print(f"[Webhook Received RAW] {raw_body}")
                return JSONResponse({"status": "healthy"})
            return JSONResponse(
                {
                    "name": "SEC Filings Agent Marketplace",
                    "status": "healthy",
                    "mcp_endpoint": PUBLIC_MCP_URL,
                    "public_connect_url": f"{PUBLIC_MCP_URL}?key=YOUR_XPAY_KEY",
                    "trial_connect_url": "https://sec-filings-mcp-1065601264332.us-central1.run.app/mcp",
                    "glama_try_url": "https://glama.ai/mcp/servers/stagproject/sec-filings-mcp",
                    "try_without_xpay_doc": "https://github.com/stagproject/sec-filings-mcp/blob/main/docs/TRY_WITHOUT_XPAY.md",
                    "xpay_explore": "https://xpay.tools/explore",
                    "discovery": {
                        "llms_txt": "/llms.txt",
                        "skill_md": "/skill.md",
                        "mcp_json": "/.well-known/mcp.json",
                        "agent_card": "/.well-known/agent-card.json",
                    },
                    "keywords": [
                        "SEC",
                        "EDGAR",
                        "10-K",
                        "10-Q",
                        "CompanyFacts",
                        "evidence_verified",
                        "x402",
                    ],
                }
            )

        def _static_file(path: str, media_type: str):
            async def handler(request):
                return FileResponse(path, media_type=media_type)

            return handler

        app = Starlette(
            lifespan=mcp_asgi_app.router.lifespan_context,
            routes=[
                Route("/ping", endpoint=ping_handler, methods=["GET"]),
                Route("/", endpoint=root_handler, methods=["GET", "POST"]),
                Route(
                    "/llms.txt",
                    endpoint=_static_file("llms.txt", "text/plain; charset=utf-8"),
                ),
                Route(
                    "/skill.md",
                    endpoint=_static_file("skill.md", "text/markdown; charset=utf-8"),
                ),
                Route(
                    "/.well-known/mcp.json",
                    endpoint=_static_file(
                        ".well-known/mcp.json", "application/json"
                    ),
                ),
                Route(
                    "/.well-known/agent-card.json",
                    endpoint=_static_file(
                        ".well-known/agent-card.json", "application/json"
                    ),
                ),
                Mount("/", app=mcp_asgi_app),
            ],
        )

        app.add_middleware(MPPMiddleware)
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=False,
            allow_methods=["*"],
            allow_headers=["*"],
            expose_headers=["mcp-session-id"],
        )

        uvicorn.run(app, host="0.0.0.0", port=port, proxy_headers=True, forwarded_allow_ips="*")
    else:
        mcp.run(transport="stdio")
