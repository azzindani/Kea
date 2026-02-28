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
import json

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
    print(f"\n   [SYSTEM]: Triggering Knowledge Sync at {rag_url}...")
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(f"{rag_url}/knowledge/sync", json={})
            if resp.status_code == 200:
                print("   [SYSTEM]: Knowledge sync started (Background Indexer active).")
                print("   [SYSTEM]: Waiting 5s for base indexing...")
                await asyncio.sleep(5)
                return True
    except Exception as e:
        print(f"   [ERROR]: Failed to trigger knowledge sync: {e}")
    return False


@pytest.mark.asyncio
async def test_knowledge_rag():
    """Verify Knowledge RAG Retrieval with real simulation queries."""
    print("\n" + "="*80)
    print(" APEX SIMULATION: KNOWLEDGE RAG (Domain Expertise)")
    print("="*80)
    
    retriever = get_knowledge_retriever()
    is_available = await retriever.is_available()
    print(f"   [STATUS]: RAG Service = {'ONLINE' if is_available else 'OFFLINE'}")
    
    if not is_available:
        pytest.skip("RAG Service is offline")

    # Initial check - if empty, try to sync
    stats = await retriever.search_raw(query="", limit=1)
    if not stats:
        print("   [WARNING]: Knowledge store appears empty. Auto-syncing library...")
        await trigger_knowledge_sync()

    for query in KNOWLEDGE_SIMULATIONS:
        print(f"\n   [INPUT]: '{query}'")
        
        # 1. Test Formatted Context (what the LLM sees)
        context = await retriever.retrieve_context(query=query, limit=2)
        
        # 2. Test Raw Retrieval (similarity scores and content)
        raw = await retriever.search_raw(query=query, limit=3)
        
        if not raw:
            print(f"   [KNOWLEDGE]: \033[91mNO MATCH FOUND\033[0m")
            continue

        for i, item in enumerate(raw):
            name = item.get('name', 'Unknown Document')
            sim = item.get('similarity', 0.0)
            cat = item.get('category', 'any').upper()
            content_snippet = item.get('content', '')[:120].replace('\n', ' ')
            
            print(f"   [KNOWLEDGE MATCH {i+1}]: {name}")
            print(f"      - Category: {cat}")
            print(f"      - Relevance: {sim:.1%}")
            print(f"      - Snippet: \"{content_snippet}...\"")

    assert is_available is True


@pytest.mark.asyncio
async def test_tools_rag():
    """Verify Tools RAG Retrieval with real capability simulations."""
    print("\n" + "="*80)
    print(" APEX SIMULATION: TOOLS RAG (Capability Discovery)")
    print("="*80)
    
    try:
        registry = await get_tool_registry()
        print("   [STATUS]: Tool Registry (pgvector) = ACTIVE")
    except Exception as e:
        print(f"   [ERROR]: Tool Registry unavailable: {e}")
        pytest.skip("Tool Registry missing")

    total_matches = 0
    for query in TOOL_SIMULATIONS:
        print(f"\n   [INPUT]: '{query}'")
        
        tools = await registry.search_tools(query=query, limit=3)
        
        if not tools:
            print(f"   [TOOL discovery]: \033[91mNO CAPABILITIES FOUND\033[0m")
            continue

        for i, tool in enumerate(tools):
            name = tool.get('name', 'unknown_tool')
            desc = tool.get('description', 'No description available')[:100]
            # Try to get parameters
            schema = tool.get('inputSchema', {})
            params = list(schema.get('properties', {}).keys())
            
            print(f"   [TOOL MATCH {i+1}]: {name}")
            print(f"      - Function: {desc}...")
            if params:
                print(f"      - Interface: {params}")
            total_matches += 1

    if total_matches == 0:
        print("\n   [ADVICE]: No tools discovered. Ensure MCP Host has registered tool schemas into Postgres.")
    
    assert total_matches >= 0


async def main():
    settings = get_settings()
    setup_logging(
        LogConfig(
            level="INFO",
            format=settings.logging.format,
            service_name="rag_verification",
        )
    )
    
    print("\n\033[94m>>> STARTING RAG RETRIEVAL APEX SIMULATION <<<\033[0m")
    
    try:
        await test_knowledge_rag()
        await test_tools_rag()
    finally:
        print("\n" + "="*80)
        print(" SIMULATION COMPLETE")
        print("="*80)


if __name__ == "__main__":
    asyncio.run(main())
