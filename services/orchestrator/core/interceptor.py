"""
Memory Interceptor.

The "Autonomic Wire" that connects Tool Outputs -> Long Term Memory.
Intercepts every tool/node execution and saves it to the Vector Store.
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime
from typing import Any

from shared.schemas import NodeOutput, AtomicFact
from shared.logging import get_logger
from services.rag_service.core.fact_store import FactStore, FactStore

# Singleton lazy loader for storing connection
_fact_store: FactStore | None = None

logger = get_logger(__name__)

async def get_fact_store() -> FactStore:
    global _fact_store
    if _fact_store is None:
        # Initialize FactStore which will use PostgresVectorStore via environment config
        # We import here to avoid circular dependencies at module level if any
        from services.rag_service.core.fact_store import FactStore
        _fact_store = FactStore()
    return _fact_store

class MemoryInterceptor:
    """
    Intercepts and stores all system outputs.
    """
    
    @staticmethod
    async def intercept(
        trace_id: str,
        source_node: str,
        result: Any,
        inputs: dict[str, Any] | None = None
    ) -> NodeOutput:
        """
        Intercept a result, wrap it, and fire-and-forget store it.
        """
        # 1. Standardize formatting
        content = {}
        
        # Handle string output
        if isinstance(result, str):
            content["text"] = result
        # Handle dict output
        elif isinstance(result, dict):
            content["data"] = result
            # Heuristic to find text for embedding
            if "text" in result:
                content["text"] = result["text"]
            elif "content" in result:
                content["text"] = str(result["content"])
        # Handle MCP ToolResult object
        elif hasattr(result, "content") and isinstance(result.content, list):
            # MCP ToolResult
            text_parts = []
            for item in result.content:
                if hasattr(item, "text"):
                    text_parts.append(item.text)
            content["text"] = "\n".join(text_parts)
            content["mcp_result"] = True
        else:
            content["data"] = str(result)
            content["text"] = str(result)

        # 2. Create NodeOutput
        output = NodeOutput(
            trace_id=trace_id,
            source_node=source_node,
            content=content,
            metadata={
                "inputs": inputs or {},
                "captured_at": datetime.utcnow().isoformat()
            }
        )
        
        # 3. Async Store (Fire and Forget)
        # We don't await this to keep the "Brain" (Orchestrator) fast.
        # Ideally this goes to a queue, but here we spawn a background task.
        asyncio.create_task(MemoryInterceptor._store_async(output))
        
        return output

    @staticmethod
    async def _store_async(output: NodeOutput):
        """Internal storage logic with embedding generation."""
        try:
            store = await get_fact_store()
            
            # Get the text content to embed
            text_content = output.content.get("text", "")[:4000]
            
            if not text_content:
                logger.debug(f"No text content to store from {output.source_node}")
                return
            
            # Generate embedding for semantic search
            embedding = None
            try:
                from shared.embedding.model_manager import get_embedding_provider
                provider = get_embedding_provider()
                embeddings = await provider.embed([text_content])
                embedding = embeddings[0] if embeddings else None
                logger.debug(f"🧠 Generated embedding for {output.source_node} ({len(embedding)} dims)")
            except Exception as e:
                logger.warning(f"Embedding generation failed: {e}, storing without embedding")
            
            # Create AtomicFact with embedding
            fact = AtomicFact(
                fact_id="",  # Auto-generate
                entity=f"Tool Execution: {output.source_node}",
                attribute="output",
                value=text_content,
                source_url=f"kea://trace/{output.trace_id}/{output.source_node}",
                source_title=f"Execution of {output.source_node}",
                confidence_score=1.0,
                extracted_at=output.timestamp
            )
            
            # Store with embedding if available
            await store.add_fact(fact, embedding=embedding)
            
            logger.debug(f"🧠 Autonomic Memory: Stored output from {output.source_node}")
            
        except Exception as e:
            logger.warning(f"Failed to auto-store memory: {e}")

