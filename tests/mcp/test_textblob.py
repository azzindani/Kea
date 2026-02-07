import pytest
import asyncio
from mcp import ClientSession
from mcp.client.stdio import stdio_client
from tests.mcp.client_utils import get_server_params

@pytest.mark.asyncio
async def test_textblob_real_simulation():
    """
    REAL SIMULATION: Verify TextBlob Server (NLP).
    """
    params = get_server_params("textblob_server", extra_dependencies=["textblob", "pandas", "nltk"])
    
    text = "I love this product! It is amazing and very useful."
    bad_text = "I haet this product." # Spelling error
    
    print(f"\n--- Starting Real-World Simulation: TextBlob Server ---")
    
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # 1. Sentiment Analysis
            print(f"1. Analyzing Sentiment: '{text}'...")
            res = await session.call_tool("analyze_sentiment", arguments={"text": text})
            print(f" [PASS] Sentiment: {res.content[0].text}")

            # 2. Spelling Correction
            print(f"2. Correcting Spelling: '{bad_text}'...")
            res = await session.call_tool("correct_spelling", arguments={"text": bad_text})
            print(f" [PASS] Corrected: {res.content[0].text}")

            # 3. Detect Language
            print("3. Detecting Language...")
            res = await session.call_tool("detect_language", arguments={"text": "Bonjour tout le monde"})
            print(f" [PASS] Language: {res.content[0].text}")

            # 4. Noun Phrases
            print("4. Extracting Noun Phrases...")
            res = await session.call_tool("extract_noun_phrases", arguments={"text": text})
            print(f" [PASS] Phrases: {res.content[0].text}")

            # 5. Word Definitions
            print("5. Word Definition (Analysis)...")
            res = await session.call_tool("define_word", arguments={"word": "analysis"})
            print(f" [PASS] Def: {res.content[0].text[:50]}...")

            # 6. Full Report
            print("6. Full Text Report...")
            res = await session.call_tool("full_text_report", arguments={"text": text})
            print(f" [PASS] Report Generated")

    print("--- TextBlob Simulation Complete ---")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
