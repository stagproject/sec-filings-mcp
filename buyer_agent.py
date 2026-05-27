import os
import asyncio
import json
from typing import Any
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from web3 import Web3
from dotenv import load_dotenv

try:
    from web3.middleware import ExtraDataToPOAMiddleware as poa_middleware
except ImportError:
    from web3.middleware import geth_poa_middleware as poa_middleware

load_dotenv()

CLIENT_PRIVATE_KEY = os.environ.get("CLIENT_PRIVATE_KEY")
_xpay_key = os.environ.get("XPAY_API_KEY", "")
_base_mcp = os.environ.get(
    "MCP_SERVER_URL",
    os.environ.get("PUBLIC_MCP_URL", "https://sec-edgar-filings.mcp.xpay.sh/mcp"),
)
MCP_SERVER_URL = (
    _base_mcp if "key=" in _base_mcp or not _xpay_key
    else f"{_base_mcp.rstrip('/')}?key={_xpay_key}"
)
# 動的ネットワーク設定
ACTIVE_NETWORK = "polygon"
search_single_call_count = 0  # 追加: 検索ツールの呼び出し回数を保持

def get_w3_provider(network: str) -> Web3:
    rpc_env_map = {"polygon": "POLYGON_MAINNET", "base": "BASE_MAINNET", "oasis": "OASIS_MAINNET"}
    rpc_url = os.environ.get(rpc_env_map.get(network, ""))
    if not rpc_url:
        raise ValueError(f".env に {rpc_env_map.get(network)} が設定されていません。")
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    w3.middleware_onion.inject(poa_middleware, layer=0)
    return w3

def save_result(test_name: str, data: Any):
    filename = f"test_result_{ACTIVE_NETWORK}_{test_name}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\n[✔] 結果を {filename} に保存しました。")

def to_dict(obj: Any) -> dict:
    if hasattr(obj, "model_dump"): return obj.model_dump()
    if hasattr(obj, "dict"): return obj.dict()
    return {"raw_data": str(obj)}

async def execute_payload(w3: Web3, account, payload: dict, tamper_hmac: bool = False, insufficient_funds: bool = False) -> str:
    print(f"  [Tx実行準備] 宛先: {payload['to']}, 要求額(Wei): {payload['value']}")
    
    tx_data = payload['data']
    tx_value = payload['value']

    # --- 異常系攻撃シミュレーション ---
    if tamper_hmac:
        print("  [!] 攻撃: ペイロード末尾のHMACを破壊（ゼロパディング）します。")
        tx_data = tx_data[:-64] + ("0" * 64)
        
    if insufficient_funds:
        print("  [!] 攻撃: 送金額を 1 Wei に改ざんして送信します。")
        if tx_value != "0" and tx_value != 0:
            # Native Token (ROSE等) の場合
            tx_value = "1"
        else:
            # ERC20 / W-Token の場合 (Calldataの金額部分のみを改ざん)
            # 構造: 0x + MethodID(8) + Address(64) + Amount(64) + HMAC(64)
            # Amountの位置: 74文字目 ～ 138文字目
            if len(tx_data) >= 138:
                tx_data = tx_data[:74] + ("0" * 63 + "1") + tx_data[138:]

    nonce = w3.eth.get_transaction_count(account.address, 'pending')
    tx_draft = {
        'nonce': nonce,
        'to': w3.to_checksum_address(payload['to']),
        'value': int(tx_value),
        'data': tx_data,
        'gasPrice': w3.eth.gas_price,
        'chainId': w3.eth.chain_id,
    }
    
    try:
        tx_draft['gas'] = int(w3.eth.estimate_gas(tx_draft) * 1.2)
    except Exception:
        tx_draft['gas'] = 200000
        
    signed_tx = account.sign_transaction(tx_draft)
    tx_hash_raw = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    tx_hash_hex = w3.to_hex(tx_hash_raw)
    print(f"  -> Tx送信完了 (Hash: {tx_hash_hex})。承認待機中...")
    
    while True:
        try:
            receipt = w3.eth.get_transaction_receipt(tx_hash_raw)
            if receipt is not None:
                if receipt['status'] == 1:
                    print("  -> トランザクションがオンチェーンで成功しました。")
                else:
                    print("  -> [Reverted] トランザクションが失敗しました（オンチェーンで弾かれました）。")
                break
        except Exception: pass
        await asyncio.sleep(2)
        
    return tx_hash_hex

async def await_delivery(session, tool_name: str, args: dict, max_retries=15):
    for i in range(max_retries):
        res = await session.call_tool(tool_name, arguments=args)
        data = json.loads(res.content[0].text.split("\n---")[0])
        if data.get("status") == "pending":
            print(f"  -> サーバー応答: Pending ({data.get('message')}). 10秒待機...")
            await asyncio.sleep(10)
        else:
            return data
    return {"error": "Timeout waiting for block confirmations."}

async def dynamic_fetch_id(session, is_package=False, count=1) -> list:
    print(f"  [動的取得] データベースから {'パッケージタグ' if is_package else '特許ID'} を取得中...")
    if is_package:
        res = await session.call_tool("search_packages", arguments={"limit": max(5, count)})
        data = json.loads(res.content[0].text.split("\n---")[0])
        ids = [item['package_tag'] for item in data] if isinstance(data, list) else []
    else:
        res = await session.call_tool("search_single_patents", arguments={"primary_cpc": "G06", "limit": max(5, count)})
        data = json.loads(res.content[0].text.split("\n---")[0])
        ids = [item['patent_id'] for item in data] if isinstance(data, list) else []
    
    if len(ids) < count:
        print("  [エラー] テストに必要な数のIDが取得できませんでした。")
        return []
    print(f"  -> 取得成功: {ids[:count]}")
    return ids[:count]

def print_menu():
    print(f"""
=================================================
 MCP Server Exhaustive Test Suite (Network: {ACTIVE_NETWORK.upper()})
=================================================
[Settings]
  0.  Change Network (polygon / base / oasis)

[Tool 1 & 3: Discovery]
  1.  Search Single Patents (Min & Max Args)
  2.  Search Packages (Min & Max Args)

[Tool 2 & 4: E2E Dynamic Purchase (Happy Paths)]
  3.  E2E Purchase Patent (EOA Standard Wallet)
  4.  E2E Purchase Patent (AA Wallet / W-Token Payload)
  5.  E2E Purchase Package (EOA Standard Wallet)
  6.  E2E Purchase Package (AA Wallet / W-Token Payload)

[Advanced / Edge Cases]
  7.  Grace Period Test (Re-claim data without repurchasing)

[Security / Negative Tests (Must Fail gracefully)]
  8.  Tamper Attack: Modify HMAC to steal data
  9.  Replay Attack: Reuse successful tx_hash for a DIFFERENT product
 10.  Insufficient Funds Attack: Pay only 1 Wei with valid HMAC

[Prompts & Resources]
 11.  Fetch Prompts & Capabilities
=================================================
""")

async def run_buyer_agent():
    global ACTIVE_NETWORK
    if not CLIENT_PRIVATE_KEY: return print("エラー: CLIENT_PRIVATE_KEY が未設定です。")

    print("MCPサーバーに接続中...")
    async with streamablehttp_client(MCP_SERVER_URL) as (read_stream, write_stream, _):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            print("接続成功。")
            
            while True:
                try: w3 = get_w3_provider(ACTIVE_NETWORK)
                except ValueError as e: return print(e)
                account = w3.eth.account.from_key(CLIENT_PRIVATE_KEY)

                print_menu()
                choice = input("Select a test number (0-11): ").strip()
                
                if choice == "0":
                    net = input("Enter network (polygon, base, oasis): ").strip().lower()
                    if net in ["polygon", "base", "oasis"]: ACTIVE_NETWORK = net
                    continue
                    
                # -----------------------------------------------------
                # Discovery Tools
                # -----------------------------------------------------
                elif choice == "1":
                    global search_single_call_count
                    search_single_call_count += 1

                    if search_single_call_count == 1:
                        limit, offset, suffix = 20, 0, ""
                    elif search_single_call_count == 2:
                        limit, offset, suffix = 20, 20, "_2"
                    elif search_single_call_count == 3:
                        limit, offset, suffix = 20, 40, "_3"
                    else:
                        # 4回目でlimitを50に増加、以降は50件ずつページング
                        limit = 50
                        offset = 60 + (search_single_call_count - 4) * 50
                        suffix = f"_{search_single_call_count}"

                    print(f"Executing search_single_patents (Call {search_single_call_count}: limit={limit}, offset={offset})...")
                    
                    args_min = {"primary_cpc": "G06", "limit": limit, "offset": offset}
                    args_max = {"primary_cpc": "H02", "cross_domain_cpc": "G06", "keyword": "data", "limit": limit, "offset": offset}

                    res_min = await session.call_tool("search_single_patents", arguments=args_min)
                    res_max = await session.call_tool("search_single_patents", arguments=args_max)

                    # xpayのウォーターマーク（\n---）以降を物理的に切断して純粋なJSON文字列に戻す
                    raw_min = res_min.content[0].text.split("\n---")[0]
                    raw_max = res_max.content[0].text.split("\n---")[0]

                    try:
                        min_data = json.loads(raw_min)
                    except Exception:
                        min_data = {"raw_error": raw_min}

                    try:
                        max_data = json.loads(raw_max)
                    except Exception:
                        max_data = {"raw_error": raw_max}

                    save_result(f"1_search_single{suffix}", {"min": min_data, "max": max_data})
                elif choice == "2":
                    print("Executing search_packages...")
                    res_min = await session.call_tool("search_packages", arguments={})
                    res_max = await session.call_tool("search_packages", arguments={"search_query": "G06", "limit": 2})

                    # xpayのウォーターマーク（\n---）以降を物理的に切断して純粋なJSON文字列に戻す
                    raw_min = res_min.content[0].text.split("\n---")[0]
                    raw_max = res_max.content[0].text.split("\n---")[0]

                    try:
                        min_data = json.loads(raw_min)
                    except Exception:
                        min_data = {"raw_error": raw_min}

                    try:
                        max_data = json.loads(raw_max)
                    except Exception:
                        max_data = {"raw_error": raw_max}

                    save_result("2_search_packages", {"min": min_data, "max": max_data})
                # -----------------------------------------------------
                # E2E Dynamic Purchase Flows
                # -----------------------------------------------------
                elif choice in ["3", "4", "5", "6"]:
                    is_package = choice in ["5", "6"]
                    is_aa = choice in ["4", "6"]
                    tool_name = "verify_crypto_payment_and_deliver" if is_package else "purchase_single_patent"
                    
                    ids = await dynamic_fetch_id(session, is_package=is_package, count=1)
                    if not ids: continue
                    target_id = ids[0]
                    
                    args_s1 = {"package_tag": target_id} if is_package else {"patent_id": target_id}
                    args_s1["network"] = ACTIVE_NETWORK

                    print(f"Step 1: Requesting 402 for {target_id}...")
                    res1 = await session.call_tool(tool_name, arguments=args_s1)
                    data1 = json.loads(res1.content[0].text.split("\n---")[0])
                    
                    if data1.get("status") == 402:
                        req = data1["payment_request"]
                        payload_key = "aa_transaction_payload" if is_aa and "aa_transaction_payload" in req else "transaction_payload"
                        payload = req[payload_key]
                        
                        print(f"Step 2: Executing {'AA (W-Token)' if payload_key == 'aa_transaction_payload' else 'EOA (Standard)'} Payload...")
                        tx_hash = await execute_payload(w3, account, payload)
                        
                        print("Step 3: Claiming Data...")
                        args_s3 = args_s1.copy()
                        args_s3["tx_hash"] = tx_hash
                        final_data = await await_delivery(session, tool_name, args_s3)
                        save_result(f"{choice}_e2e_purchase_success", final_data)
                    else:
                        print(f"Failed to get 402: {data1}")

                # -----------------------------------------------------
                # Advanced: Grace Period Test
                # -----------------------------------------------------
                elif choice == "7":
                    print("--- 正常系: Grace Period (再取得) テスト ---")
                    ids = await dynamic_fetch_id(session, is_package=False, count=1)
                    if not ids: continue
                    target_id = ids[0]
                    args = {"patent_id": target_id, "network": ACTIVE_NETWORK}

                    print(f"Step A: 通常通り購入処理を行います...")
                    res = await session.call_tool("purchase_single_patent", arguments=args)
                    data1 = json.loads(res.content[0].text.split("\n---")[0])
                    tx_hash = await execute_payload(w3, account, data1["payment_request"]["transaction_payload"])
                    args["tx_hash"] = tx_hash
                    
                    claim_1 = await await_delivery(session, "purchase_single_patent", args)
                    print("  -> 初回データ取得成功。")
                    
                    print(f"Step B: 直後に同じ tx_hash で再要求します (料金は引かれないはずです)...")
                    claim_2 = await await_delivery(session, "purchase_single_patent", args)
                    print(f"  -> 結果: {'成功 (データ再取得)' if 'data' in claim_2 else '失敗'}")
                    save_result("7_grace_period_reclaim", {"claim_1": claim_1, "claim_2": claim_2})

                # -----------------------------------------------------
                # Security / Negative Tests
                # -----------------------------------------------------
                elif choice == "8":
                    print("--- 異常系: HMAC改ざん（タダ乗り）テスト ---")
                    ids = await dynamic_fetch_id(session, is_package=False, count=1)
                    if not ids: continue
                    
                    args = {"patent_id": ids[0], "network": ACTIVE_NETWORK}
                    res = await session.call_tool("purchase_single_patent", arguments=args)
                    data1 = json.loads(res.content[0].text.split("\n---")[0])
                    
                    if data1.get("status") == 402:
                        payload = data1["payment_request"]["transaction_payload"]
                        tx_hash = await execute_payload(w3, account, payload, tamper_hmac=True) # HMAC破壊
                        
                        print("サーバーに改ざんTxの検証を要求します（弾かれるのが正解）...")
                        args["tx_hash"] = tx_hash
                        final_data = await await_delivery(session, "purchase_single_patent", args)
                        print(f"結果: {final_data.get('error', final_data)}")
                        save_result("8_security_tamper", final_data)

                elif choice == "9":
                    print("--- 異常系: リプレイ攻撃（Tx流用）テスト ---")
                    ids = await dynamic_fetch_id(session, is_package=False, count=2)
                    if not ids or len(ids) < 2: continue
                    id_a, id_b = ids[0], ids[1]
                    
                    print(f"Step A: 正規に商品A ({id_a}) を購入...")
                    args_a = {"patent_id": id_a, "network": ACTIVE_NETWORK}
                    res_a = await session.call_tool("purchase_single_patent", arguments=args_a)
                    data_a = json.loads(res_a.content[0].text.split("\n---")[0])
                    tx_hash = await execute_payload(w3, account, data_a["payment_request"]["transaction_payload"])
                    args_a["tx_hash"] = tx_hash
                    await await_delivery(session, "purchase_single_patent", args_a)
                    
                    print(f"Step B: 成功した tx_hash を流用し、未購入の商品B ({id_b}) を要求...")
                    args_b = {"patent_id": id_b, "network": ACTIVE_NETWORK, "tx_hash": tx_hash}
                    final_data = await await_delivery(session, "purchase_single_patent", args_b)
                    
                    print(f"結果: {final_data.get('error', final_data)}")
                    save_result("9_security_replay", final_data)

                elif choice == "10":
                    print("--- 異常系: 送金額不足（1 Wei攻撃）テスト ---")
                    ids = await dynamic_fetch_id(session, is_package=False, count=1)
                    if not ids: continue
                    
                    args = {"patent_id": ids[0], "network": ACTIVE_NETWORK}
                    res = await session.call_tool("purchase_single_patent", arguments=args)
                    data1 = json.loads(res.content[0].text.split("\n---")[0])
                    if data1.get("status") == 402:
                        payload = data1["payment_request"]["transaction_payload"]
                        tx_hash = await execute_payload(w3, account, payload, insufficient_funds=True) # 1Wei送信
                        
                        print("サーバーに金額不足Txの検証を要求します（弾かれるのが正解）...")
                        args["tx_hash"] = tx_hash
                        final_data = await await_delivery(session, "purchase_single_patent", args)
                        print(f"結果: {final_data.get('error', final_data)}")
                        save_result("10_security_insufficient_funds", final_data)

                # -----------------------------------------------------
                # Prompts & Resources
                # -----------------------------------------------------
                elif choice == "11":
                    print("Fetching Prompts & Capabilities...")
                    p1 = await session.get_prompt("analyze_commercial_value", arguments={"package_tag": "G01"})
                    p2 = await session.get_prompt("analyze_technical_breakthroughs", arguments={"package_tag": "G01"})
                    r1 = await session.read_resource("system://capabilities")
                    cap_data = json.loads(r1.contents[0].text.split("\n---")[0]) if r1.contents else {}
                    save_result("11_prompts_and_resources", {"commercial": to_dict(p1), "technical": to_dict(p2), "capabilities": cap_data})

if __name__ == "__main__":
    asyncio.run(run_buyer_agent())