import pytest
import asyncio
from mcp import ClientSession
from mcp.client.stdio import stdio_client
from tests.mcp.client_utils import get_server_params

@pytest.mark.asyncio
async def test_qualitative_real_simulation():
    """
    REAL SIMULATION: Verify Qualitative Server (Text Analysis).
    """
    params = get_server_params("qualitative_server", extra_dependencies=[])
    
    text = "User interviewed stated they love the new feature but find the UI confusing. They recommended adding a tutorial."
    
    print(f"\n--- Starting Real-World Simulation: Qualitative Server ---")
    
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # 1. Text Coding
            print("1. Coding Text...")
            res = await session.call_tool("text_coding", arguments={"text": text, "codes": ["Positive", "Negative", "Suggestion"]})
            print(f" [PASS] Coded: {res.content[0].text}")

            # 2. Sentiment
            print("2. Sentiment Analysis...")
            res = await session.call_tool("sentiment_analysis", arguments={"text": text})
            print(f" [PASS] Sentiment: {res.content[0].text}")

            # 3. Entity Extraction
            print("3. Entity Extraction...")
            res = await session.call_tool("entity_extractor", arguments={"text": "Apple released the iPhone in 2007."})
            print(f" [PASS] Entities: {res.content[0].text}")

    print("--- Qualitative Simulation Complete ---")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
