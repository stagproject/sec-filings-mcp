import asyncio
import os

from dotenv import load_dotenv
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

load_dotenv()
key = os.environ["XPAY_API_KEY"].strip()
url = f"https://sec-edgar-filings.mcp.xpay.sh/mcp?key={key}"


async def main() -> None:
    async with streamablehttp_client(url) as (r, w, _):
        async with ClientSession(r, w) as s:
            await s.initialize()
            print("1 init ok")
            await s.list_tools()
            print("2 list ok")
            res = await s.call_tool("search_filings", {"ticker": "ADM", "limit": 1})
            print("3 search ok", res.content[0].text[:80])
            res = await s.call_tool("get_filing_sample", {})
            print("4 sample ok", res.content[0].text[:80])


if __name__ == "__main__":
    asyncio.run(main())
