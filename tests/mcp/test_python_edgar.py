import pytest

import asyncio
from mcp_servers.python_edgar_server.server import PythonEdgarServer
import os

async def verify():
    server = PythonEdgarServer()
    print("--- Verifying Python-Edgar (EdgarTools) Server ---")
    print(f"Total Tools: {len(server.get_tools())}")

    # 1. Test Profile (AAPL)
    print("\n--- 1. Testing Company Profile (AAPL) ---")
    try:
        handler = server._handlers["analyze_company_profile"]
        res = await handler({"ticker": "AAPL"})
        if not res.isError:
             print("SUCCESS snippet:", res.content[0].text[:500])
        else:
             print("FAILED:", res.content[0].text)
    except Exception as e:
        print(f"Error: {e}")

    # 2. Test Content (Markdown 10-K)
    print("\n--- 2. Testing Filing Text (Markdown) ---")
    try:
        handler = server._handlers["get_filing_text"]
        res = await handler({"ticker": "AAPL", "form": "10-K"})
        if not res.isError:
             print("SUCCESS snippet:", res.content[0].text[:500])
        else:
             print("FAILED:", res.content[0].text)
    except Exception as e:
        print(f"Error: {e}")

    # 3. Test Financials (Income)
    print("\n--- 3. Testing Financials (Income) ---")
    try:
        handler = server._handlers["get_financial_statements"]
        # Use AAPL
        res = await handler({"ticker": "AAPL", "statement": "Income"})
        if not res.isError:
             print("SUCCESS snippet:", res.content[0].text[:500])
        else:
             print("FAILED:", res.content[0].text)
    except Exception as e:
        print(f"Error: {e}")

    # 4. Test Ownership (Insider Trades)
    print("\n--- 4. Testing Insider Trades (Form 4) ---")
    try:
        handler = server._handlers["get_insider_trades"]
        res = await handler({"ticker": "AAPL", "limit": 2})
        if not res.isError:
             print("SUCCESS snippet:", res.content[0].text[:500])
        else:
             print("FAILED:", res.content[0].text)
    except Exception as e:
        print(f"Error: {e}")

    # 5. Test Section Extraction (Item 1A)
    print("\n--- 5. Testing Section (Item 1A) ---")
    try:
        # Item 1A = Risk Factors
        handler = server._handlers["get_filing_section_content"]
        res = await handler({"ticker": "AAPL", "form": "10-K", "item": "Item 1A"})
        if not res.isError:
             print("SUCCESS snippet:", res.content[0].text[:300])
        else:
             print("FAILED:", res.content[0].text)
    except Exception as e:
        print(f"Error: {e}")

    # 6. Test Bulk Facts (AAPL, MSFT)
    print("\n--- 6. Testing Bulk Facts (AAPL, MSFT) ---")
    try:
        handler = server._handlers["get_bulk_company_facts"]
        res = await handler({"tickers": "AAPL, MSFT"})
        if not res.isError:
             print("SUCCESS snippet:", res.content[0].text[:500])
        else:
             print("FAILED:", res.content[0].text)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(verify())


@pytest.mark.asyncio
async def test_main():
    await verify()

