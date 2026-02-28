"""
Verification Script for Knowledge RAG and Tools RAG Retrieval.

This script manually verifies the RAG capabilities for both Knowledge and Tools.
"""

import asyncio

from shared.knowledge.retriever import get_knowledge_retriever
from services.mcp_host.core.tool_registry import get_tool_registry
from shared.logging.main import setup_logging, LogConfig
from shared.config import get_settings


async def verify_knowledge_rag():
    """Verify Knowledge RAG Retrieval."""
    print("--- Verifying Knowledge RAG Retrieval ---")
    retriever = get_knowledge_retriever()
    
    is_available = await retriever.is_available()
    print(f"RAG Service Available: {is_available}")
    
    if is_available:
        print("Retrieving context for 'analyze data' (limit 1)...")
        context = await retriever.retrieve_context(query="analyze data", limit=1)
        print("Formatted Context output length:", len(context))
        
        print("Raw search for 'analyze data'...")
        raw_results = await retriever.search_raw(query="analyze data", limit=1)
        print("Raw search results count:", len(raw_results))
        if raw_results:
            print(f"Top result ID: {raw_results[0].get('knowledge_id')}")
    else:
        print("Skipping retrieval checks since RAG service is unavailable.")


async def verify_tools_rag():
    """Verify Tools RAG Retrieval."""
    print("\n--- Verifying Tools RAG Retrieval ---")
    try:
        registry = await get_tool_registry()
        print("Tool Registry initialized successfully.")
        
        # Searching 50 or more as per user description
        query = "fetch data or analyze information"
        print(f"Searching tools for '{query}' (limit 50)...")
        tools = await registry.search_tools(query=query, limit=50)
        
        print(f"Discovered {len(tools)} tools via pgvector retrieval.")
        if tools:
            print("Top tool returned:", tools[0].get("name", "Unknown"))
    except ValueError as e:
        print(f"Could not initialize tool registry: {e}")
    except Exception as e:
        print(f"Tool registry search failed: {e}")


async def main():
    settings = get_settings()
    setup_logging(
        LogConfig(
            level=settings.logging.level,
            format=settings.logging.format,
            service_name="verification_script",
        )
    )
    print("Starting RAG Retrieval Verification...\n")
    
    try:
        await verify_knowledge_rag()
        await verify_tools_rag()
    finally:
        print("\nVerification process complete.")


if __name__ == "__main__":
    asyncio.run(main())
