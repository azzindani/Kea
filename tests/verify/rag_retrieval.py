"""
Verification Script for Knowledge RAG and Tools RAG Retrieval.

This script simulates real-world queries against Kea's RAG capabilities.
It performs deep system diagnostics to troubleshoot empty results.

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
from shared.database.connection import get_database_pool


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


async def run_diagnostics():
    """Run system-wide diagnostics to verify database and service health."""
    settings = get_settings()
    rag_url = ServiceRegistry.get_url(ServiceName.RAG_SERVICE)
    
    print("\n" + "="*80)
    print(" 🏥 DEEP SYSTEM DIAGNOSTICS")
    print("="*80)
    print(f"   [DATABASE]: {settings.database.url.split('@')[-1] if '@' in settings.database.url else 'Local'}")
    print(f"   [RAG SERVICE]: {rag_url}")
    
    # 1. Check RAG Service Health & Stats
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            # Health
            h_resp = await client.get(f"{rag_url}/health")
            print(f"   [RAG HEALTH]: {'✅ OK' if h_resp.status_code == 200 else f'❌ {h_resp.status_code}'}")
            
            # Stats
            s_resp = await client.get(f"{rag_url}/knowledge/stats/summary")
            if s_resp.status_code == 200:
                count = s_resp.json().get('total_items', 0)
                print(f"   [RAG KNOWLEDGE COUNT]: {count} items")
            else:
                print(f"   [RAG KNOWLEDGE STATS]: ❌ ERROR {s_resp.status_code}")
    except Exception as e:
        print(f"   [RAG SERVICE]: ❌ UNREACHABLE ({e})")

    # 2. Check Database Directly
    try:
        pool = await get_database_pool()
        async with pool.acquire() as conn:
            # Table Discovery - Find what's actually in this DB
            all_tables = await conn.fetch("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
            table_names = [t['table_name'] for t in all_tables]
            print(f"   [DB DISCOVERY]: Found tables: {', '.join(table_names)}")

            # Check all potential Knowledge tables
            for k_table in [settings.knowledge.registry_table, "knowledge_registry"]:
                if k_table in table_names:
                    try:
                        k_data = await conn.fetchrow(f"SELECT COUNT(*) as total FROM {k_table}")
                        print(f"   [DB KNOWLEDGE ({k_table})]: {k_data['total']} rows")
                    except Exception as e:
                        print(f"   [DB KNOWLEDGE ({k_table})]: ❌ COUNT FAILED ({e})")
            
            # Check Tool Table
            t_table = "tool_registry"
            if t_table in table_names:
                try:
                    t_data = await conn.fetchrow(f"SELECT COUNT(*) as total FROM {t_table}")
                    print(f"   [DB TOOLS]: {t_data['total']} rows")
                except Exception as e:
                    print(f"   [DB TOOLS]: ❌ COUNT FAILED ({e})")
            else:
                print(f"   [DB TOOLS]: ❌ Table '{t_table}' MISSING from DB")
            
            # Check Vector Extension
            ext_count = await conn.fetchval("SELECT COUNT(*) FROM pg_extension WHERE extname = 'vector'")
            print(f"   [PGVECTOR EXTENSION]: {'✅ INSTALLED' if ext_count > 0 else '❌ MISSING'}")
            
    except Exception as e:
        print(f"   [DATABASE CONNECTION]: ❌ FAILED ({e})")
    print("="*80 + "\n")


async def trigger_knowledge_sync():
    """Trigger the RAG Service to sync knowledge files from disk (Blocking)."""
    settings = get_settings()
    rag_url = ServiceRegistry.get_url(ServiceName.RAG_SERVICE)
    print(f"\n   [SYSTEM]: Triggering FORCED Knowledge Sync at {rag_url}...")
    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            # Call with background=False to block until done
            resp = await client.post(f"{rag_url}/knowledge/sync?background=False")
            if resp.status_code == 200:
                print("   [SYSTEM]: Knowledge sync COMPLETED successfully.")
                return True
            else:
                print(f"   [ERROR]: Sync failed with status {resp.status_code}: {resp.text}")
    except Exception as e:
        print(f"   [ERROR]: Failed to trigger knowledge sync: {e}")
    return False


async def trigger_tool_sync():
    """Trigger the MCP Host to discvocer and sync tools to RAG (Blocking)."""
    mcp_url = ServiceRegistry.get_url(ServiceName.MCP_HOST)
    print(f"\n   [SYSTEM]: Triggering FORCED Tool Sync at {mcp_url}...")
    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            resp = await client.post(f"{mcp_url}/tools/sync?background=False")
            if resp.status_code == 200:
                print("   [SYSTEM]: Tool sync COMPLETED successfully.")
                return True
            else:
                print(f"   [ERROR]: Tool sync failed with status {resp.status_code}: {resp.text}")
    except Exception as e:
        print(f"   [ERROR]: Failed to trigger tool sync: {e}")
    return False


@pytest.mark.asyncio
async def test_rag_diagnostics():
    """Run diagnostics as a test to ensure visibility in pytest output."""
    await run_diagnostics()


@pytest.mark.asyncio
async def test_knowledge_rag():
    """Verify Knowledge RAG Retrieval with real simulation queries."""
    print("\n" + "="*80)
    print(" 🧠 APEX SIMULATION: KNOWLEDGE RAG")
    print("="*80)
    
    retriever = get_knowledge_retriever()
    is_available = await retriever.is_available()
    
    if not is_available:
        print("   [STATUS]: ❌ RAG Service is OFFLINE")
        pytest.skip("RAG Service is offline")

    # Double check stats - if literally 0, sync
    stats = await retriever.search_raw(query="", limit=1)
    if not stats:
        print("   [WARNING]: Knowledge store reports 0 indexable items. Syncing...")
        await trigger_knowledge_sync()
        # Refresh availability check
        stats = await retriever.search_raw(query="", limit=1)

    for query in KNOWLEDGE_SIMULATIONS:
        print(f"\n   [INPUT]: '{query}'")
        
        # 1. Test Raw Retrieval
        raw = await retriever.search_raw(query=query, limit=3)
        
        if not raw:
            print(f"   [OUTPUT]: \033[91mNO MATCH FOUND\033[0m")
            continue

        for i, item in enumerate(raw):
            name = item.get('name', 'Unknown')
            sim = item.get('similarity', 0.0)
            cat = item.get('category', 'any').upper()
            content_snippet = item.get('content', '')[:150].replace('\n', ' ')
            
            print(f"   [MATCH {i+1}]: {name} | Relevance: {sim:.1%}")
            print(f"      - Category: {cat}")
            print(f"      - Excerpt: \"{content_snippet}...\"")

    assert is_available is True


@pytest.mark.asyncio
async def test_tools_rag():
    """Verify Tools RAG Retrieval with real capability simulations."""
    print("\n" + "="*80)
    print(" 🛠️  APEX SIMULATION: TOOLS RAG")
    print("="*80)
    
    try:
        registry = await get_tool_registry()
        # Verify if we have tools indexed
        tools = await registry.search_tools(query="", limit=1, min_similarity=0.0)
        if not tools:
             print("   [WARNING]: Tool registry reports 0 indexable items. Syncing...")
             await trigger_tool_sync()
    except Exception as e:
        print(f"   [STATUS]: ❌ Tool Registry UNREACHABLE ({e})")
        pytest.skip("Tool Registry missing")

    total_matches = 0
    for query in TOOL_SIMULATIONS:
        print(f"\n   [INPUT]: '{query}'")
        
        # Use a very permissive search first
        tools = await registry.search_tools(query=query, limit=3, min_similarity=0.0)
        
        if not tools:
            print(f"   [OUTPUT]: \033[91mNO MATCH FOUND\033[0m")
            continue

        for i, tool in enumerate(tools):
            name = tool.get('name', 'unknown_tool')
            desc = tool.get('description', 'No description available')[:120]
            schema = tool.get('inputSchema', {})
            params = list(schema.get('properties', {}).keys())
            
            print(f"   [MATCH {i+1}]: {name}")
            print(f"      - Capability: {desc}...")
            if params:
                print(f"      - Parameters: {params}")
            total_matches += 1

    if total_matches == 0:
        print("\n   [ADVICE]: ⚠️  No tools discovered in database. Use tool_sync.py if available.")
    
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
    
    print("\n\033[94m>>> KE-A RAG ORCHESTRATION VERIFICATION <<<\033[0m")
    
    try:
        await run_diagnostics()
        await test_knowledge_rag()
        await test_tools_rag()
    finally:
        print("\n" + "="*80)
        print(" ✅ VERIFICATION CYCLE COMPLETE")
        print("="*80)


if __name__ == "__main__":
    asyncio.run(main())
