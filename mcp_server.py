import os
import json
import time
import requests
import hmac
import hashlib
import uvicorn
from typing import Optional
from pydantic import Field
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from supabase import create_client, Client
from dotenv import load_dotenv

from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import FileResponse
from starlette.middleware.base import BaseHTTPMiddleware

from web3 import Web3
try:
    from web3.middleware import ExtraDataToPOAMiddleware as poa_middleware
except ImportError:
    from web3.middleware import geth_poa_middleware as poa_middleware

load_dotenv()

security_settings = TransportSecuritySettings(enable_dns_rebinding_protection=False)
mcp = FastMCP(
    "Mirelia USPTO Patent Marketplace",
    instructions=(
        "USPTO patent data for competitive intelligence, prior art search, and R&D scouting. "
        "Use search_single_patents or search_packages first, then purchase with on-chain x402 flow."
    ),
    website_url="https://github.com/stagproject/mirelia-structured-data-marketplace",
    transport_security=security_settings,
)

PUBLIC_MCP_URL = os.environ.get(
    "PUBLIC_MCP_URL",
    "https://mirelia-structured-data-marketplace.mcp.xpay.sh/mcp",
)

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
if url and key:
    supabase: Client = create_client(url, key)
else:
    supabase = None

rpc_base = os.environ.get("BASE_MAINNET")
rpc_polygon = os.environ.get("POLYGON_MAINNET")
rpc_oasis = os.environ.get("OASIS_MAINNET")

usdc_base_raw = os.environ.get("BASE_USDC")
usdc_polygon_raw = os.environ.get("POLYGON_USDC")
wrose_raw = os.environ.get("OASIS_WROSE")
abi_string = os.environ.get("ERC20_ABI")
WALLET_ADDRESS_RAW = os.environ.get("SELLER_WALLET_ADDRESS")

HMAC_SECRET = os.environ.get("HMAC_SECRET", "default_insecure_mcp_secret_change_in_production").encode()

chains = {}
if Web3 and abi_string and WALLET_ADDRESS_RAW:
    WALLET_ADDRESS = Web3.to_checksum_address(WALLET_ADDRESS_RAW)
    ERC20_ABI = json.loads(abi_string)
    
    if rpc_base and usdc_base_raw:
        w3_base = Web3(Web3.HTTPProvider(rpc_base))
        chains["base"] = {"w3": w3_base, "usdc": w3_base.eth.contract(address=Web3.to_checksum_address(usdc_base_raw), abi=ERC20_ABI), "type": "erc20", "confs": 2}
    
    if rpc_polygon and usdc_polygon_raw:
        w3_polygon = Web3(Web3.HTTPProvider(rpc_polygon))
        w3_polygon.middleware_onion.inject(poa_middleware, layer=0)
        chains["polygon"] = {"w3": w3_polygon, "usdc": w3_polygon.eth.contract(address=Web3.to_checksum_address(usdc_polygon_raw), abi=ERC20_ABI), "type": "erc20", "confs": 15}
        
    if rpc_oasis:
        w3_oasis = Web3(Web3.HTTPProvider(rpc_oasis))
        w3_oasis.middleware_onion.inject(poa_middleware, layer=0)
        chains["oasis"] = {"w3": w3_oasis, "usdc": None, "type": "native", "confs": 2}
        if wrose_raw:
            chains["oasis"]["w_token"] = w3_oasis.eth.contract(address=Web3.to_checksum_address(wrose_raw), abi=ERC20_ABI)
else:
    WALLET_ADDRESS = None

# -----------------------------------------------------------------------------
# ユーティリティ関数
# -----------------------------------------------------------------------------
PRICE_CACHE = {"rose_usd": {"price": 0.0, "timestamp": 0}}
CACHE_TTL = 300  # 5分

def get_rose_price() -> float:
    now = time.time()
    if now - PRICE_CACHE["rose_usd"]["timestamp"] < CACHE_TTL and PRICE_CACHE["rose_usd"]["price"] > 0:
        return PRICE_CACHE["rose_usd"]["price"]
    try:
        res = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=ROSEUSDT", timeout=5)
        price = float(res.json()['price'])
    except Exception:
        try:
            res = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=oasis-network&vs_currencies=usd", timeout=5)
            price = float(res.json()['oasis-network']['usd'])
        except Exception:
            if PRICE_CACHE["rose_usd"]["price"] > 0: return PRICE_CACHE["rose_usd"]["price"]
            price = 0.08
            
    PRICE_CACHE["rose_usd"]["price"] = price
    PRICE_CACHE["rose_usd"]["timestamp"] = now
    return price

def generate_payment_memo(package_tag: str, amount_raw: int) -> str:
    """決済の正当性を証明するステートレスなHMAC署名を生成"""
    msg = f"{package_tag}:{amount_raw}".encode()
    return hmac.new(HMAC_SECRET, msg, hashlib.sha256).hexdigest()

def clean_supabase_data(rows):
    array_fields = ['assignee', 'inventor', 'secondary_cpcs', 'attr_tech_stack', 'tech_stacks', 'biz_target_ind', 'attr_performance', 'package_tags', 'cited_patents']
    for row in rows:
        for field in array_fields:
            if field in row and isinstance(row[field], str):
                try: row[field] = json.loads(row[field])
                except Exception: pass
    return rows

def is_valid_tx_hash(h: str) -> bool:
    return isinstance(h, str) and h.startswith("0x") and len(h) == 66

class MPPMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next): return await call_next(request)


# -----------------------------------------------------------------------------
# 1. 1件販売用: 高精度・軽量検索ツール
# -----------------------------------------------------------------------------
@mcp.tool()
def search_single_patents(
    primary_cpc: str = Field(description="Must be one of the exact codes (e.g., G01, G06, H04)."),
    cross_domain_cpc: Optional[str] = Field(default=None, description="Optional secondary CPC for cross-domain searches."),
    keyword: Optional[str] = Field(default=None, description="Searches only in title."),
    min_score: Optional[int] = Field(default=70, description="Minimum importance_p (0-100)."),
    limit: Optional[int] = Field(default=20, description="Number of results to return (max 100)."),
    offset: Optional[int] = Field(default=0, description="Number of results to skip for pagination (e.g., 20 for page 2).")
) -> str:
    """
    USPTO patent search for competitive intelligence, prior art, IP analytics, and R&D scouting.
    [COST: low xpay per-call fee; $0.50 USDC on-chain per patent dataset if purchased]
    Searches 3000+ AI-enriched USPTO patents ($0.50 each to buy full JSON). Daily-updated database.
    Returns: patent_id, title, importance_p, publication_date, primary_cpc, secondary_cpcs, biz_target_ind.
    Supports pagination via offset.

    [AVAILABLE PRIMARY CPCs]: 
    G01(Measurement/Testing), G02(Optics), G03(Photography), G04(Horology), G05(Control Systems), 
    G06(Computing/Data Processing), G07(Checking Devices), G08(Signaling), G09(Displays/Cryptography), 
    G10(Acoustics/Speech), G11(Info Storage), G12(Instrument Details), G16(Specific ICT/Healthcare), 
    G21(Nuclear), H01(Basic Electric Elements), H02(Electric Power), H03(Electronic Circuitry), 
    H04(Communication), H05(Misc Electric), H10(Solid State Devices)

    [EXAMPLE ARGUMENTS - MINIMAL]:
    {"primary_cpc": "G06"}

    [EXAMPLE ARGUMENTS - MAXIMAL]:
    {"primary_cpc": "H02", "cross_domain_cpc": "G06", "keyword": "thermal power generation", "min_score": 80, "limit": 50, "offset": 50}
    """
    if not supabase: return json.dumps({"error": "Database connection failed"}, ensure_ascii=False)
    try:
        query = supabase.table("v_single_patent_search").select("patent_id, title, importance_p, publication_date, primary_cpc, secondary_cpcs, biz_target_ind")
        query = query.eq("primary_cpc", primary_cpc.upper())
        if cross_domain_cpc: query = query.contains("secondary_cpcs", [cross_domain_cpc.upper()])
        if keyword:
            safe_kw = keyword.strip().replace("'", "''")
            query = query.or_(f"title.ilike.%{safe_kw}%")
        if min_score is not None: query = query.gte("importance_p", min_score)
        
        # 末尾に .offset() を追加
        res = query.order("importance_p", desc=True).order("publication_date", desc=True).limit(max(1, min(limit or 20, 100))).offset(offset or 0).execute()
        return json.dumps(res.data, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)
# -----------------------------------------------------------------------------
# 2. 1件販売用: 決済・納品ツール
# -----------------------------------------------------------------------------
@mcp.tool()
def purchase_single_patent(
    patent_id: str = Field(description="The patent_id obtained from search_single_patents."),
    network: Optional[str] = Field(default="polygon", description="Blockchain network. Defaults to 'polygon' (USDC). Supports 'base' or 'oasis'."),
    tx_hash: Optional[str] = Field(default=None, description="The transaction hash. LEAVE EMPTY first to retrieve payment instructions.")
) -> str:
    """
    USPTO patent purchase and delivery — prior art / competitive intelligence single-patent dataset.
    [COST: xpay per-call + $0.50 USDC on-chain data price]
    Delivers full structured JSON after on-chain payment verification.

    [AGENTIC WORKFLOW (MPP v1.0 402 Payment Flow)]:
    This is a mandatory 2-step process. Do NOT hallucinate a tx_hash.
    STEP 1: Call this tool with ONLY 'patent_id' and 'network'. Leave 'tx_hash' EMPTY. The server will return a 402 Payment Required response containing a 'transaction_payload'.
    STEP 2: You MUST securely execute/broadcast the exact 'transaction_payload' on the blockchain using your wallet. This payload contains the required cryptographic HMAC memo to bind your payment to the product.
    STEP 3: Once the transaction is confirmed on-chain, call this exact tool AGAIN, providing the 'patent_id', 'network', and the resulting 66-character 'tx_hash'.

    [SUPPORTED NETWORKS]: 'polygon' (USDC), 'base' (USDC), 'oasis' (ROSE natively via EOA, or WROSE via AA wallets). Default is 'polygon'.

    [EXAMPLE ARGUMENTS - MINIMAL (Step 1 - Request Payment Info)]:
    {"patent_id": "US12449246B2"}

    [EXAMPLE ARGUMENTS - MAXIMAL (Step 3 - Claim Data)]:
    {"patent_id": "US12449246B2", "network": "polygon", "tx_hash": "0x123abc456def7890123abc456def7890123abc456def7890123abc456def7890"}
    """
    if not supabase: return json.dumps({"error": "Supabase connection failed"}, ensure_ascii=False)
    net_key = (network or "polygon").lower()
    if net_key not in chains: return json.dumps({"error": f"Unsupported network: {net_key}"}, ensure_ascii=False)

    SINGLE_PRICE_USD = 0.50
    expected_package_tag = f"SINGLE_{patent_id}"
    chain_info = chains[net_key]

    if tx_hash is not None and tx_hash.strip() != "":
        if not is_valid_tx_hash(tx_hash):
            return json.dumps({"error": "Invalid tx_hash format."}, ensure_ascii=False)

    try:
        check_res = supabase.table("v_single_patent_delivery").select("patent_id").eq("patent_id", patent_id).execute()
        if not check_res.data: return json.dumps({"error": f"Patent ID '{patent_id}' not found."}, ensure_ascii=False)
    except Exception:
        return json.dumps({"status": "pending", "message": "Database temporarily busy. Please wait 15 seconds and retry."}, ensure_ascii=False)

    # --- 402要求 ---
    if not tx_hash or tx_hash.strip() == "":
        aa_tx_payload = None
        try:
            if chain_info["type"] == "erc20":
                required_raw = int(SINGLE_PRICE_USD * (10**6))
                memo_hex = generate_payment_memo(expected_package_tag, required_raw)
                base_calldata = chain_info["usdc"].encodeABI(fn_name='transfer', args=[WALLET_ADDRESS, required_raw])
                tx_data = base_calldata + memo_hex
                tx_payload = {"to": chain_info["usdc"].address, "value": "0", "data": tx_data}
            else:
                rose_price = get_rose_price()
                required_raw = int((SINGLE_PRICE_USD / rose_price) * (10**18))
                memo_hex = generate_payment_memo(expected_package_tag, required_raw)
                tx_data = "0x" + memo_hex
                tx_payload = {"to": WALLET_ADDRESS, "value": str(required_raw), "data": tx_data}
                
                # AAウォレット用のW-Tokenペイロードを生成
                if chain_info.get("w_token"):
                    base_aa_calldata = chain_info["w_token"].encodeABI(fn_name='transfer', args=[WALLET_ADDRESS, required_raw])
                    aa_tx_data = base_aa_calldata + memo_hex
                    aa_tx_payload = {"to": chain_info["w_token"].address, "value": "0", "data": aa_tx_data}
                    
        except Exception as e:
            return json.dumps({"status": "pending", "message": f"Service temporarily busy ({str(e)}). Please wait 15 seconds and retry."}, ensure_ascii=False)

        instruction_text = (
            "Agent MUST execute 'transaction_payload' exactly if using a standard EOA wallet. "
            "CRITICAL for AA (Smart Contract) wallets: Native transfers are untraceable. "
            "If using an AA wallet, you MUST execute 'aa_transaction_payload' instead (wraps payment in ERC20). "
            "After payment is confirmed on-chain, call this exact tool again with the tx_hash to receive the data."
        )
        
        payment_req = {
            "mpp_version": "1.0", "destination": WALLET_ADDRESS, "amount": SINGLE_PRICE_USD,
            "asset": "USDC" if net_key != "oasis" else "ROSE", "network": net_key,
            "description": f"Purchase of Single Patent: {patent_id}",
            "transaction_payload": tx_payload,
            "instruction": instruction_text
        }
        if aa_tx_payload:
            payment_req["aa_transaction_payload"] = aa_tx_payload

        return json.dumps({
            "status": 402, "message": "Payment Required",
            "payment_request": payment_req
        }, ensure_ascii=False)

    current_time = int(time.time())

    # --- DB検証 ---
    try:
        tx_check = supabase.table("processed_transactions").select("*").eq("tx_hash", tx_hash).execute()
        if tx_check.data:
            if tx_check.data[0]['package_tag'] == expected_package_tag:
                full_data_res = supabase.table("v_single_patent_delivery").select("*").eq("patent_id", patent_id).execute()
                return json.dumps({"system_log": "Verified. Data delivered.", "data": clean_supabase_data(full_data_res.data)}, ensure_ascii=False)
            else:
                return json.dumps({"error": "Transaction already used for a different product."}, ensure_ascii=False)
    except Exception:
        return json.dumps({"status": "pending", "message": "Database temporarily busy. Please wait 15 seconds and retry."}, ensure_ascii=False)

    # --- オンチェーン検証 ---
    w3 = chain_info["w3"]
    try:
        receipt = w3.eth.get_transaction_receipt(tx_hash)
        if receipt is None: return json.dumps({"status": "pending", "message": "Transaction is pending. Please wait 15 seconds and retry."}, ensure_ascii=False)
        if receipt['status'] != 1: return json.dumps({"error": "Transaction failed on-chain"}, ensure_ascii=False)
        
        current_block = w3.eth.block_number
        tx_block = receipt['blockNumber']
        req_confs = chain_info["confs"]
        if (current_block - tx_block) < req_confs:
            return json.dumps({"status": "pending", "message": f"Awaiting block confirmations ({current_block - tx_block}/{req_confs}). Please wait 15 seconds and retry."}, ensure_ascii=False)
            
        tx = w3.eth.get_transaction(tx_hash)
        tx_input_str = tx['input'].hex() if hasattr(tx['input'], 'hex') else str(tx['input'])
        
    except Exception as e:
        err_str = str(e).lower()
        if "not found" in err_str or "unknown" in err_str: return json.dumps({"status": "pending", "message": "Transaction is not yet confirmed. Please wait 15-30 seconds and retry."}, ensure_ascii=False)
        return json.dumps({"status": "pending", "message": f"RPC Node temporarily busy ({str(e)}). Please wait 15 seconds and retry."}, ensure_ascii=False)
    
    payment_found = False
    try:
        if chain_info["type"] == "erc20":
            events = chain_info["usdc"].events.Transfer().process_receipt(receipt)
            for event in events:
                if event['args']['to'].lower() == WALLET_ADDRESS.lower():
                    actual_amount = event['args']['value']
                    expected_memo = generate_payment_memo(expected_package_tag, actual_amount)
                    if expected_memo in tx_input_str:
                        payment_found = True; break
        elif chain_info["type"] == "native":
            # 1. Native ROSE check (EOA)
            if tx['to'] and tx['to'].lower() == WALLET_ADDRESS.lower():
                actual_amount = tx['value']
                expected_memo = generate_payment_memo(expected_package_tag, actual_amount)
                if expected_memo in tx_input_str:
                    payment_found = True
            
            # 2. W-Token (ERC20) check for AA wallets
            if not payment_found and chain_info.get("w_token"):
                events = chain_info["w_token"].events.Transfer().process_receipt(receipt)
                for event in events:
                    if event['args']['to'].lower() == WALLET_ADDRESS.lower():
                        actual_amount = event['args']['value']
                        expected_memo = generate_payment_memo(expected_package_tag, actual_amount)
                        if expected_memo in tx_input_str:
                            payment_found = True; break

    except Exception as e:
        return json.dumps({"status": "pending", "message": f"Service temporarily busy verifying payment ({str(e)}). Please wait 15 seconds and retry."}, ensure_ascii=False)

    if not payment_found:
         return json.dumps({"error": "Valid payment not found. Payment memo mismatch, amount insufficient, or unauthorized AA wallet transfer."}, ensure_ascii=False)
         
    try:
        supabase.table("processed_transactions").insert({
            "tx_hash": tx_hash, "network": net_key, "package_tag": expected_package_tag, "verified_at": current_time
        }).execute()
    except Exception:
        pass 
        
    try:
        full_data_res = supabase.table("v_single_patent_delivery").select("*").eq("patent_id", patent_id).execute()
        return json.dumps({"system_log": "Verified. Data delivered.", "data": clean_supabase_data(full_data_res.data)}, ensure_ascii=False)
    except Exception:
        return json.dumps({"status": "pending", "message": "Database temporarily busy storing data. Please wait 15 seconds and retry."}, ensure_ascii=False)

# -----------------------------------------------------------------------------
# 3. パッケージ販売用: バルクパック探索ツール
# -----------------------------------------------------------------------------
@mcp.tool()
def search_packages(
    search_query: str = Field(default="", description="Search keywords like 'G01', 'H04'. Leave blank for all."),
    limit: Optional[int] = Field(default=20, description="Number of results to return (max 100).")
) -> str:
    """
    USPTO bulk patent package catalog for competitive intelligence and landscape analysis.
    [COST: low xpay per-call fee]
    Bulk datasets (10, 100, 1000 patents per pack). Large-scale R&D and IP analytics.
    If 'search_query' is empty, returns the full catalog of available packages.
    If 'search_query' contains a CPC or keyword, returns specific domain packs.

    [AVAILABLE DOMAINS]: 
    G01(Measurement), G02(Optics), G03(Photography), G04(Horology), G05(Control), 
    G06(Computing), G07(Checking), G08(Signaling), G09(Displays), G10(Acoustics), 
    G11(Storage), G12(Instruments), G16(Healthcare ICT), G21(Nuclear), H01(Electric Elements), 
    H02(Power), H03(Circuitry), H04(Communication), H05(Misc), H10(Solid State)

    [EXAMPLE ARGUMENTS - MINIMAL (List All Catalogs)]:
    {}

    [EXAMPLE ARGUMENTS - MAXIMAL (Search Specific Domain & Limit)]:
    {"search_query": "G06_100", "limit": 10}
    """
    if not supabase: return json.dumps({"error": "Database connection failed"})
    try:
        q = (search_query or "").strip()
        safe_limit = max(1, min(limit or 20, 100))
        if not q:
            res = supabase.table("v_package_marketplace").select("package_tag, category, title, record_count, price_usd, avg_importance_p, tech_stacks").order("package_tag").limit(safe_limit).execute()
            return json.dumps(clean_supabase_data(res.data), ensure_ascii=False)
        else:
            safe_q = q.replace(",", " ")
            if "_" in safe_q:
                exact = supabase.table("v_catalogs").select("*").eq("package_tag", safe_q).execute()
                if exact.data: return json.dumps(clean_supabase_data(exact.data), ensure_ascii=False)
            res = supabase.table("v_catalogs").select("*").or_(f"category.ilike.%{safe_q}%,title.ilike.%{safe_q}%,description.ilike.%{safe_q}%,package_tag.ilike.%{safe_q}%").order("package_tag").limit(safe_limit).execute()
            return json.dumps(clean_supabase_data(res.data), ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)})

# -----------------------------------------------------------------------------
# 4. パッケージ販売用: 決済・配信ツール
# -----------------------------------------------------------------------------
@mcp.tool()
def verify_crypto_payment_and_deliver(
    package_tag: str = Field(description="The tag of the package to purchase."),
    network: Optional[str] = Field(default="polygon", description="The network (base, polygon, oasis). Defaults to 'polygon'."),
    tx_hash: Optional[str] = Field(default=None, description="Transaction hash. LEAVE EMPTY for 402 request.")
) -> str:
    """
    USPTO bulk patent package purchase — competitive intelligence datasets with on-chain payment.
    [COST: xpay per-call + package price on-chain]
    Delivers full JSON package after payment verification.

    [AGENTIC WORKFLOW (MPP v1.0 402 Payment Flow)]:
    This is a mandatory 2-step process. Do NOT hallucinate a tx_hash.
    STEP 1: Call this tool with ONLY 'package_tag' and 'network'. Leave 'tx_hash' EMPTY. You will receive a 402 response with a 'transaction_payload'.
    STEP 2: Execute/broadcast the 'transaction_payload' exactly as provided to apply the HMAC cryptographic memo. Do not modify the payload data.
    STEP 3: After confirmation, call this tool AGAIN with the exact 'package_tag', 'network', and the resulting 'tx_hash' to receive the dataset.

    [EXAMPLE ARGUMENTS - MINIMAL (Step 1 - Request Payment Info)]:
    {"package_tag": "G01_10_001"}

    [EXAMPLE ARGUMENTS - MAXIMAL (Step 3 - Claim Data)]:
    {"package_tag": "G01_10_001", "network": "base", "tx_hash": "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"}
    """
    if not supabase: return json.dumps({"error": "Supabase connection failed"}, ensure_ascii=False)
    net_key = (network or "polygon").lower()
    if net_key not in chains: return json.dumps({"error": f"Unsupported network: {net_key}"}, ensure_ascii=False)

    if tx_hash is not None and tx_hash.strip() != "":
        if not is_valid_tx_hash(tx_hash): return json.dumps({"error": "Invalid tx_hash format."}, ensure_ascii=False)

    try:
        catalog_res = supabase.table("patent_packages").select("price_usd, sales_count").eq("package_tag", package_tag).execute()
        if not catalog_res.data: return json.dumps({"error": "Package not found"}, ensure_ascii=False)
    except Exception:
        return json.dumps({"status": "pending", "message": "Database temporarily busy. Please wait 15 seconds and retry."}, ensure_ascii=False)
        
    catalog_data = catalog_res.data[0]
    price_usd = float(catalog_data['price_usd'])
    chain_info = chains[net_key]

    # --- 402要求 ---
    if not tx_hash or tx_hash.strip() == "":
        aa_tx_payload = None
        try:
            if chain_info["type"] == "erc20":
                required_raw = int(price_usd * (10**6))
                memo_hex = generate_payment_memo(package_tag, required_raw)
                base_calldata = chain_info["usdc"].encodeABI(fn_name='transfer', args=[WALLET_ADDRESS, required_raw])
                tx_data = base_calldata + memo_hex
                tx_payload = {"to": chain_info["usdc"].address, "value": "0", "data": tx_data}
            else:
                rose_price = get_rose_price()
                required_raw = int((price_usd / rose_price) * (10**18))
                memo_hex = generate_payment_memo(package_tag, required_raw)
                tx_data = "0x" + memo_hex
                tx_payload = {"to": WALLET_ADDRESS, "value": str(required_raw), "data": tx_data}
                
                # AAウォレット用のW-Tokenペイロードを生成
                if chain_info.get("w_token"):
                    base_aa_calldata = chain_info["w_token"].encodeABI(fn_name='transfer', args=[WALLET_ADDRESS, required_raw])
                    aa_tx_data = base_aa_calldata + memo_hex
                    aa_tx_payload = {"to": chain_info["w_token"].address, "value": "0", "data": aa_tx_data}
                    
        except Exception as e:
            return json.dumps({"status": "pending", "message": f"Service temporarily busy ({str(e)}). Please wait 15 seconds and retry."}, ensure_ascii=False)

        instruction_text = (
            "Agent MUST execute 'transaction_payload' exactly if using a standard EOA wallet. "
            "CRITICAL for AA (Smart Contract) wallets: Native transfers are untraceable. "
            "If using an AA wallet, you MUST execute 'aa_transaction_payload' instead (wraps payment in ERC20). "
            "After payment is confirmed on-chain, call this exact tool again with the tx_hash to receive the data."
        )

        payment_req = {
            "mpp_version": "1.0", "destination": WALLET_ADDRESS, "amount": price_usd,
            "asset": "USDC" if net_key != "oasis" else "ROSE", "network": net_key,
            "description": f"Bulk Purchase: {package_tag}",
            "transaction_payload": tx_payload,
            "instruction": instruction_text
        }
        if aa_tx_payload:
            payment_req["aa_transaction_payload"] = aa_tx_payload

        return json.dumps({
            "status": 402, "message": "Payment Required",
            "payment_request": payment_req
        }, ensure_ascii=False)
        
    current_time = int(time.time())

    # --- DB検証 ---
    try:
        tx_check = supabase.table("processed_transactions").select("*").eq("tx_hash", tx_hash).execute()
        if tx_check.data:
            if tx_check.data[0]['package_tag'] == package_tag:
                res_data = supabase.table("v_patent_marketplace_lite").select("*").contains("package_tags", [package_tag]).execute()
                return json.dumps({"system_log": "Verified. Data delivered.", "package_data": clean_supabase_data(res_data.data)}, ensure_ascii=False)
            else:
                return json.dumps({"error": "Transaction already used for a different product."}, ensure_ascii=False)
    except Exception:
        return json.dumps({"status": "pending", "message": "Database temporarily busy. Please wait 15 seconds and retry."}, ensure_ascii=False)

    # --- オンチェーン検証 ---
    w3 = chain_info["w3"]
    try:
        receipt = w3.eth.get_transaction_receipt(tx_hash)
        if receipt is None: return json.dumps({"status": "pending", "message": "Transaction is pending. Please wait 15 seconds and retry."}, ensure_ascii=False)
        if receipt['status'] != 1: return json.dumps({"error": "Tx failed on-chain"}, ensure_ascii=False)
            
        current_block = w3.eth.block_number
        tx_block = receipt['blockNumber']
        req_confs = chain_info["confs"]
        if (current_block - tx_block) < req_confs:
            return json.dumps({"status": "pending", "message": f"Awaiting block confirmations ({current_block - tx_block}/{req_confs}). Please wait 15 seconds and retry."}, ensure_ascii=False)

        tx = w3.eth.get_transaction(tx_hash)
        tx_input_str = tx['input'].hex() if hasattr(tx['input'], 'hex') else str(tx['input'])
    except Exception as e:
        err_str = str(e).lower()
        if "not found" in err_str or "unknown" in err_str: return json.dumps({"status": "pending", "message": "Transaction is pending. Please wait 15-30 seconds and retry."}, ensure_ascii=False)
        return json.dumps({"status": "pending", "message": f"RPC Node temporarily busy ({str(e)}). Please wait 15 seconds and retry."}, ensure_ascii=False)

    payment_found = False
    try:
        if chain_info["type"] == "erc20":
            events = chain_info["usdc"].events.Transfer().process_receipt(receipt)
            for event in events:
                if event['args']['to'].lower() == WALLET_ADDRESS.lower():
                    actual_amount = event['args']['value']
                    expected_memo = generate_payment_memo(package_tag, actual_amount)
                    if expected_memo in tx_input_str:
                        payment_found = True; break
        elif chain_info["type"] == "native":
            if tx['to'] and tx['to'].lower() == WALLET_ADDRESS.lower():
                actual_amount = tx['value']
                expected_memo = generate_payment_memo(package_tag, actual_amount)
                if expected_memo in tx_input_str:
                    payment_found = True
            
            if not payment_found and chain_info.get("w_token"):
                events = chain_info["w_token"].events.Transfer().process_receipt(receipt)
                for event in events:
                    if event['args']['to'].lower() == WALLET_ADDRESS.lower():
                        actual_amount = event['args']['value']
                        expected_memo = generate_payment_memo(package_tag, actual_amount)
                        if expected_memo in tx_input_str:
                            payment_found = True; break

    except Exception as e:
        return json.dumps({"status": "pending", "message": f"Service temporarily busy verifying payment ({str(e)}). Please wait 15 seconds and retry."}, ensure_ascii=False)

    if not payment_found:
        return json.dumps({"error": "Valid payment not found. Payment memo mismatch, amount insufficient, or unauthorized AA wallet transfer."}, ensure_ascii=False)
         
    try:
        supabase.table("processed_transactions").insert({"tx_hash": tx_hash, "network": net_key, "package_tag": package_tag, "verified_at": current_time}).execute()
        supabase.table("patent_packages").update({"sales_count": (catalog_data['sales_count'] or 0) + 1}).eq("package_tag", package_tag).execute()
    except Exception:
        pass 

    try:
        res_data = supabase.table("v_patent_marketplace_lite").select("*").contains("package_tags", [package_tag]).execute()
        return json.dumps({"system_log": "Verified. Data delivered.", "package_data": clean_supabase_data(res_data.data)}, ensure_ascii=False)
    except Exception:
        return json.dumps({"status": "pending", "message": "Database temporarily busy storing data. Please wait 15 seconds and retry."}, ensure_ascii=False)

if __name__ == "__main__":
    import sys
    is_cloud_run = "K_SERVICE" in os.environ
    if is_cloud_run or "--sse" in sys.argv:
        port = int(os.environ.get("PORT", 8080))
        
        # 最新の Streamable HTTP アプリケーション
        mcp_asgi_app = mcp.streamable_http_app()

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
            return JSONResponse({
                "name": "Mirelia Structured Data Marketplace",
                "status": "healthy",
                "mcp_endpoint": PUBLIC_MCP_URL,
                "public_connect_url": f"{PUBLIC_MCP_URL}?key=YOUR_XPAY_KEY",
                "xpay_explore": "https://xpay.tools/explore",
                "discovery": {
                    "llms_txt": "/llms.txt",
                    "skill_md": "/skill.md",
                    "mcp_json": "/.well-known/mcp.json",
                    "agent_card": "/.well-known/agent-card.json",
                },
                "keywords": [
                    "USPTO", "patent", "prior art", "competitive intelligence", "IP analytics", "CPC", "x402",
                ],
            })

        def _static_file(path: str, media_type: str):
            async def handler(request):
                return FileResponse(path, media_type=media_type)
            return handler

        app = Starlette(
            lifespan=mcp_asgi_app.router.lifespan_context,
            routes=[
                Route("/", endpoint=root_handler, methods=["GET", "POST"]),
                Route("/llms.txt", endpoint=_static_file("llms.txt", "text/plain; charset=utf-8")),
                Route("/skill.md", endpoint=_static_file("skill.md", "text/markdown; charset=utf-8")),
                Route("/.well-known/mcp.json", endpoint=_static_file(".well-known/mcp.json", "application/json")),
                Route("/.well-known/agent-card.json", endpoint=_static_file(".well-known/agent-card.json", "application/json")),
                Mount("/", app=mcp_asgi_app),
            ],
        )
        
        # 成功したCORS設定（expose_headers）を維持
        app.add_middleware(MPPMiddleware)
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=False,
            allow_methods=["*"],
            allow_headers=["*"],
            expose_headers=["mcp-session-id"]
        )
        
        uvicorn.run(app, host="0.0.0.0", port=port, proxy_headers=True, forwarded_allow_ips="*")
    else:
        mcp.run(transport="stdio")