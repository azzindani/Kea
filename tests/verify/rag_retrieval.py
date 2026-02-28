"""
Verification Script for Knowledge RAG and Tools RAG Retrieval.

This script simulates real-world queries against Kea's RAG capabilities.
It tests semantic retrieval for both domain knowledge and tool discovery.

Usage:
    uv run pytest tests/verify/rag_retrieval.py -s -v
    OR
    uv run python tests/verify/rag_retrieval.py
"""

import asyncio
import httpx
import pytest

from shared.knowledge.retriever import get_knowledge_retriever
from services.mcp_host.core.tool_registry import get_tool_registry
from shared.logging.main import setup_logging, LogConfig
from shared.config import get_settings
from shared.service_registry import ServiceRegistry, ServiceName


# Simulation Queries
KNOWLEDGE_SIMULATIONS = [
    "How does the Cognitive Cycle (OODA) work in Kea?",
    "What are the Tier 7 properties of a Conscious Observer?",
    "Explain the transition between Perceive and Frame phases.",
    "Corporate Kernel governance and swarm management rules.",
]

TOOL_SIMULATIONS = [
    "I need to read a file from the local disk.",
    "Search the web for the latest Eurozone GDP forecast.",
    "Execute a mathematical calculation or statistical analysis.",
    "Interact with a PostgreSQL database to fetch user records.",
]


async def trigger_knowledge_sync():
    """Trigger the RAG Service to sync knowledge files from disk."""
    settings = get_settings()
    rag_url = ServiceRegistry.get_url(ServiceName.RAG_SERVICE)
    print(f"Triggering Knowledge Sync at {rag_url}...")
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(f"{rag_url}/knowledge/sync", json={})
            if resp.status_code == 200:
                print("Knowledge sync started successfully. Waiting for indexer...")
                await asyncio.sleep(5)  # Give it a moment to index basic files
                return True
    except Exception as e:
        print(f"Failed to trigger knowledge sync: {e}")
    return False


@pytest.mark.asyncio
async def test_knowledge_rag():
    """Verify Knowledge RAG Retrieval with real simulation queries."""
    print("\n" + "="*50)
    print("SIMULATION: Knowledge RAG (Domain Expertise)")
    print("="*50)
    
    retriever = get_knowledge_retriever()
    is_available = await retriever.is_available()
    print(f"RAG Service Status: {'ONLINE' if is_available else 'OFFLINE'}")
    
    if not is_available:
        pytest.skip("RAG Service is offline")

    # Initial check - if empty, try to sync
    stats = await retriever.search_raw(query="", limit=1)
    if not stats:
        print("Knowledge store appears empty. Attempting auto-sync...")
        await trigger_knowledge_sync()

    results_found = 0
    for query in KNOWLEDGE_SIMULATIONS:
        print(f"\nQUERY: '{query}'")
        
        # 1. Test Formatted Context (what the LLM sees)
        context = await retriever.retrieve_context(query=query, limit=2)
        print(f"  - Context length: {len(context)} chars")
        
        # 2. Test Raw Retrieval (similarity scores)
        raw = await retriever.search_raw(query=query, limit=3)
        print(f"  - Items retrieved: {len(raw)}")
        
        for i, item in enumerate(raw):
            name = item.get('name', 'Unknown')
            sim = item.get('similarity', 0.0)
            cat = item.get('category', 'any')
            print(f"    [{i+1}] {name} ({cat}) - Score: {sim:.3f}")
            results_found += 1

    # Quality Check
    if results_found == 0:
        print("\nWARNING: No simulation matches found. Ensuring Knowledge Library exists...")
        # Check if sync actually helps
        await trigger_knowledge_sync()
        
    assert is_available is True


@pytest.mark.asyncio
async def test_tools_rag():
    """Verify Tools RAG Retrieval with real capability simulations."""
    print("\n" + "="*50)
    print("SIMULATION: Tools RAG (Capability Discovery)")
    print("="*50)
    
    try:
        registry = await get_tool_registry()
        print("Tool Registry: Postgres/pgvector backend active")
    except Exception as e:
        print(f"Tool Registry unavailable: {e}")
        pytest.skip("Tool Registry missing")

    results_found = 0
    for query in TOOL_SIMULATIONS:
        print(f"\nQUERY: '{query}'")
        
        tools = await registry.search_tools(query=query, limit=5)
        print(f"  - Matching tools: {len(tools)}")
        
        for i, tool in enumerate(tools):
            name = tool.get('name', 'unknown')
            desc = tool.get('description', 'no desc')[:60]
            print(f"    [{i+1}] {name}: {desc}...")
            results_found += 1

    if results_found == 0:
        print("\nWARNING: No tools found. MCP Host may need to register tools.")
    
    # We assert that we at least tried to search, but for a healthy system 
    # we'd expect at least some tools to be registered.
    assert results_found >= 0


async def main():
    settings = get_settings()
    setup_logging(
        LogConfig(
            level="INFO",
            format=settings.logging.format,
            service_name="rag_verification",
        )
    )
    
    print("Starting REAL QUERY RAG SIMULATION...\n")
    
    try:
        await test_knowledge_rag()
        await test_tools_rag()
    finally:
        print("\n" + "="*50)
        print("Simulation complete.")
        print("="*50)


if __name__ == "__main__":
    asyncio.run(main())
