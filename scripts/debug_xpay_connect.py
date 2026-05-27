import asyncio
import os
import traceback

from dotenv import load_dotenv
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

load_dotenv()
key = os.environ.get("XPAY_API_KEY", "").strip()
url = f"https://sec-edgar-filings.mcp.xpay.sh/mcp?key={key}"


async def main() -> None:
    try:
        async with streamablehttp_client(url) as (r, w, _):
            async with ClientSession(r, w) as s:
                await s.initialize()
                t = await s.list_tools()
                print("OK", [x.name for x in t.tools])
    except Exception as e:
        print("ERR", type(e).__name__, e)
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
