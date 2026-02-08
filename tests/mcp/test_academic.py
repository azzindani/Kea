import pytest
import asyncio
from mcp import ClientSession
from mcp.client.stdio import stdio_client
from tests.mcp.client_utils import get_server_params

@pytest.mark.asyncio
async def test_academic_real_simulation():
    """
    REAL SIMULATION: Verify Academic Server tools with real queries.
    """
    params = get_server_params("academic_server", extra_dependencies=["requests", "beautifulsoup4"])
    
    print(f"\n--- Starting Real-World Simulation: Academic Server ---")
    
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # 1. Discover
            tools_res = await session.list_tools()
            tool_names = [t.name for t in tools_res.tools]
            print(f"Discovered {len(tool_names)} tools: {tool_names}")
            
            # 2. PubMed Search
            if "pubmed_search" in tool_names:
                query = "CRISPR"
                print(f"1. Testing PubMed Search ('{query}')...")
                res = await session.call_tool("pubmed_search", arguments={"query": query, "max_results": 3})
                if res.isError:
                    print(f" \033[91m[FAIL]\033[0m {res.content[0].text}")
                else:
                    print(f" \033[92m[PASS]\033[0m Got results length: {len(res.content[0].text)}")

            # 3. ArXiv Search
            if "arxiv_search" in tool_names:
                query = "transformer model"
                print(f"2. Testing ArXiv Search ('{query}')...")
                res = await session.call_tool("arxiv_search", arguments={"query": query, "max_results": 2})
                if res.isError:
                    print(f" \033[91m[FAIL]\033[0m {res.content[0].text}")
                else:
                    print(f" \033[92m[PASS]\033[0m Got results length: {len(res.content[0].text)}")

            # 4. Semantic Scholar
            if "semantic_scholar_search" in tool_names:
                query = "agentic ai"
                print(f"3. Testing Semantic Scholar ('{query}')...")
                res = await session.call_tool("semantic_scholar_search", arguments={"query": query, "max_results": 2})
                if res.isError:
                    # Semantic Scholar API might be strict or require key, accept fail/warn
                    print(f" [WARN/FAIL] {res.content[0].text}")
                else:
                    print(f" \033[92m[PASS]\033[0m Got results: {res.content[0].text[:100]}...")

            # 5. Crossref (Metadata)
            if "crossref_lookup" in tool_names:
                doi = "10.1038/s41586-020-2003-7"
                print(f"4. Testing Crossref Lookup ('{doi}')...")
                res = await session.call_tool("crossref_lookup", arguments={"doi": doi})
                if not res.isError:
                     print(f" \033[92m[PASS]\033[0m Found metadata")
                else:
                     print(f" \033[91m[FAIL]\033[0m {res.content[0].text}")

            # 6. Paper Downloader
            if "paper_downloader" in tool_names:
                # Use open access DOI
                doi = "10.1371/journal.pcbi.1004668" 
                print(f"5. Testing Paper Downloader ('{doi}')...")
                res = await session.call_tool("paper_downloader", arguments={"doi": doi})
                if not res.isError:
                     print(f" \033[92m[PASS]\033[0m Result: {res.content[0].text}")
                else:
                     print(f" [WARN] Download failed (expected in some envs): {res.content[0].text}")

    print("--- Academic Simulation Complete ---")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
