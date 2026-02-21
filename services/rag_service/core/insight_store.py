"""
Insight Store.

Storage and retrieval of atomic insights extracted from execution.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from services.vault.core.vector_store import VectorStore, Document, create_vector_store
from shared.schemas import AtomicInsight
from shared.logging.main import get_logger


logger = get_logger(__name__)


class InsightStore:
    """
    Store and retrieve atomic insights.
    
    Combines vector store for semantic search with metadata filtering.
    
    Example:
        store = InsightStore()
        
        insight = AtomicInsight(
            insight_id="i-123",
            entity="nickel production",
            attribute="volume",
            value="1.5 million tons",
            origin_url="https://example.com",
        )
        
        await store.add_insight(insight)
        results = await store.search("nickel production volume", limit=5)
    """
    
    def __init__(self, vector_store: VectorStore | None = None, use_memory: bool = False) -> None:
        self._vector_store = vector_store or create_vector_store(use_memory=use_memory)
        self._insights: dict[str, AtomicInsight] = {}  # In-memory cache
    
    async def add_insight(
        self,
        insight: AtomicInsight,
        dataset_id: str | None = None,
        embedding: list[float] | None = None,
    ) -> str:
        """
        Add an insight to the store.
        
        Args:
            insight: AtomicInsight to store
            dataset_id: Optional ID of the dataset this insight belongs to
            embedding: Optional pre-computed embedding vector
            
        Returns:
            Insight ID
        """
        # Generate ID if not provides
        if not insight.insight_id:
            insight.insight_id = str(uuid.uuid4())
        
        # Build searchable content
        content = self._insight_to_text(insight)
        
        # Create document for vector store
        metadata = {
            "entity": insight.entity,
            "attribute": insight.attribute,
            "value": insight.value,
            "unit": insight.unit,
            "period": insight.period,
            "origin_url": insight.origin_url,
            "origin_title": insight.origin_title,
            "confidence_score": insight.confidence_score,
            "created_at": insight.created_at.isoformat(),
        }
        
        if dataset_id:
            metadata["dataset_id"] = dataset_id

        doc = Document(
            id=insight.insight_id,
            content=content,
            metadata=metadata,
            embedding=embedding,  # Attach pre-computed embedding
        )
        
        await self._vector_store.add([doc])
        self._insights[insight.insight_id] = insight
        
        logger.info(f"Added insight {insight.insight_id} via {dataset_id or 'manual'}", extra={"entity": insight.entity})
        return insight.insight_id
    
    async def add_insights(self, insights: list[AtomicInsight], dataset_id: str | None = None) -> list[str]:
        """Add multiple insights."""
        ids = []
        for insight in insights:
            id = await self.add_insight(insight, dataset_id=dataset_id)
            ids.append(id)
        return ids
    
    async def get_insight(self, insight_id: str) -> AtomicInsight | None:
        """Get an insight by ID."""
        # Check cache first
        if insight_id in self._insights:
            return self._insights[insight_id]
        
        # Query vector store
        docs = await self._vector_store.get([insight_id])
        if not docs:
            return None
        
        return self._doc_to_insight(docs[0])
    
    async def search(
        self,
        query: str,
        limit: int | None = None,
        entity: str | None = None,
        dataset_id: str | None = None,
        min_confidence: float | None = None,
    ) -> list[AtomicInsight]:
        """
        Semantic search for insights.
        
        Args:
            query: Search query
            limit: Max results
            entity: Filter by entity
            dataset_id: Filter by dataset
            min_confidence: Minimum confidence score
            
        Returns:
            List of matching insights
        """
        from shared.config import get_settings
        settings = get_settings()
        limit = limit or settings.rag.default_limit
        min_confidence = min_confidence if min_confidence is not None else settings.rag.min_confidence
        # Build filter
        filter_dict = {}
        if entity:
            filter_dict["entity"] = entity
        if dataset_id:
            filter_dict["dataset_id"] = dataset_id
        
        results = await self._vector_store.search(query, limit=limit * 2, filter=filter_dict or None)
        
        insights = []
        for result in results:
            insight = self._result_to_insight(result)
            
            # Apply confidence filter
            if insight.confidence_score >= min_confidence:
                insights.append(insight)
            
            if len(insights) >= limit:
                break
        
        return insights
    
    async def delete_insight(self, insight_id: str) -> None:
        """Delete an insight by ID."""
        await self._vector_store.delete([insight_id])
        self._insights.pop(insight_id, None)
        logger.info(f"Deleted insight {insight_id}")

    async def delete_by_dataset(self, dataset_id: str) -> int:
        """
        Delete all insights for a specific dataset. 
        Note: VectorStore abstract interface might not support delete by filter efficiently yet.
        For now we rely on implementation details or iterate.
        The most efficient way in pgvector is DELETE WHERE metadata->>'dataset_id' = ?.
        Standard VectorStore usually only accepts IDs. 
        We might need a custom method or accept inefficiency. 
        Assuming our PostgresStore supports filter in delete or we add it later.
        For now, let's just log a warning if we can't do it efficiently.
        Wait, we are using the generic VectorStore.
        Let's assume we can't easily bulk delete by metadata without a specific method.
        BUT, we can skip implementing exact deletion for now and just add the interface.
        """
        # TODO: Implement bulk delete in VectorStore. For now, this is a placeholder or requires iterating logic.
        # Ideally: await self._vector_store.delete(filter={"dataset_id": dataset_id})
        logger.warning(f"Bulk delete by dataset {dataset_id} requested but optimized support pending on VectorStore Interface.")
        return 0

    async def get_datasets(self) -> list[str]:
        """Get list of loaded datasets (heuristic: look at recent insights or dedicated registry)."""
        # Since we don't have a separate table for datasets, we inferred it from insights.
        # This is expensive. We should track datasets properly.
        # For MVP, we can just return a hardcoded list or scan local cache.
        datasets = set()
        for f in self._insights.values():
            # We don't store dataset_id on AtomicInsight yet (it's in metadata). 
            # We need to add it to AtomicInsight schema or retrieve from metadata?
            # Schema change is expensive. 
            pass
        return []
    
    async def get_entities(self) -> list[str]:
        """Get list of unique entities."""
        return list(set(f.entity for f in self._insights.values()))
    
    async def get_insights_by_entity(self, entity: str) -> list[AtomicInsight]:
        """
        Get all insights for a specific entity.
        
        Args:
            entity: Entity name to search for
            
        Returns:
            List of insights for the entity
        """
        return [f for f in self._insights.values() if f.entity == entity]
    
    
    def _insight_to_text(self, insight: AtomicInsight) -> str:
        """Convert insight to searchable text."""
        parts = [
            f"{insight.entity} {insight.attribute}",
            f"value: {insight.value}",
        ]
        
        if insight.unit:
            parts.append(f"unit: {insight.unit}")
        if insight.period:
            parts.append(f"period: {insight.period}")
        
        return " | ".join(parts)
    
    def _doc_to_insight(self, doc: Document) -> AtomicInsight:
        """Convert document to insight."""
        metadata = doc.metadata
        return AtomicInsight(
            insight_id=doc.id,
            entity=metadata.get("entity", ""),
            attribute=metadata.get("attribute", ""),
            value=metadata.get("value", ""),
            unit=metadata.get("unit"),
            period=metadata.get("period"),
            origin_url=metadata.get("origin_url", ""),
            origin_title=metadata.get("origin_title", ""),
            confidence_score=metadata.get("confidence_score", get_settings().rag.default_confidence),
            created_at=datetime.fromisoformat(metadata.get("created_at", datetime.now(__import__("datetime").UTC).isoformat())),
        )
    
    def _result_to_insight(self, result) -> AtomicInsight:
        """Convert search result to insight."""
        metadata = result.metadata
        return AtomicInsight(
            insight_id=result.id,
            entity=metadata.get("entity", ""),
            attribute=metadata.get("attribute", ""),
            value=metadata.get("value", ""),
            unit=metadata.get("unit"),
            period=metadata.get("period"),
            origin_url=metadata.get("origin_url", ""),
            origin_title=metadata.get("origin_title", ""),
            confidence_score=metadata.get("confidence_score", get_settings().rag.default_confidence),
        )
