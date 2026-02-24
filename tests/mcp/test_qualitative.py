
import pytest
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

    print("\n--- Starting Real-World Simulation: Qualitative Server ---")

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # 1. Text Coding
            print("1. Coding Text...")
            res = await session.call_tool("text_coding", arguments={"text": text, "codes": ["Positive", "Negative", "Suggestion"]})
            print(f" \033[92m[PASS]\033[0m Coded: {res.content[0].text}")

            # 2. Sentiment
            print("2. Sentiment Analysis...")
            res = await session.call_tool("sentiment_analysis", arguments={"text": text})
            print(f" \033[92m[PASS]\033[0m Sentiment: {res.content[0].text}")

            # 3. Entity Extraction
            print("3. Entity Extraction...")
            res = await session.call_tool("entity_extractor", arguments={"text": "Apple released the iPhone in 2007."})
            print(f" \033[92m[PASS]\033[0m Entities: {res.content[0].text}")

            # 4. Themes & Connections
            print("4. Themes & Connections...")
            await session.call_tool("theme_extractor", arguments={"texts": [text, "User found UI difficult."]})
            await session.call_tool("connection_mapper", arguments={"entities": ["Alice", "Bob"], "context": "Alice knows Bob."})

            # 5. Investigation Graph
            print("5. Investigation Graph...")
            await session.call_tool("investigation_graph_add", arguments={"entity_type": "Person", "entity_name": "John Doe"})
            await session.call_tool("investigation_graph_query", arguments={"entity_name": "John Doe"})

            # 6. Timeline & Sampling
            print("6. Timeline & Sampling...")
            await session.call_tool("event_timeline", arguments={"events": [{"date": "2023-01-01", "event": "Start"}]})
            await session.call_tool("snowball_sampling", arguments={"seed_entities": ["John Doe"]})

            # 7. Triangulation
            print("7. Triangulation...")
            sources = [{"source": "Interview", "claim": "UI is bad"}, {"source": "Survey", "claim": "UI needs work"}]
            await session.call_tool("triangulation_check", arguments={"claim": "UI is poor", "sources": sources})

    print("--- Qualitative Simulation Complete ---")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
