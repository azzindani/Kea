"""
Fact Store.

Storage and retrieval of atomic facts extracted from research.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from services.vault.core.vector_store import VectorStore, Document, create_vector_store
from shared.schemas import AtomicFact
from shared.logging import get_logger


logger = get_logger(__name__)


class FactStore:
    """
    Store and retrieve atomic facts.
    
    Combines vector store for semantic search with metadata filtering.
    
    Example:
        store = FactStore()
        
        fact = AtomicFact(
            fact_id="f-123",
            entity="nickel production",
            attribute="volume",
            value="1.5 million tons",
            source_url="https://example.com",
        )
        
        await store.add_fact(fact)
        results = await store.search("nickel production volume", limit=5)
    """
    
    def __init__(self, vector_store: VectorStore | None = None, use_memory: bool = False) -> None:
        self._vector_store = vector_store or create_vector_store(use_memory=use_memory)
        self._facts: dict[str, AtomicFact] = {}  # In-memory cache
    
    async def add_fact(
        self,
        fact: AtomicFact,
        dataset_id: str | None = None,
        embedding: list[float] | None = None,
    ) -> str:
        """
        Add a fact to the store.
        
        Args:
            fact: AtomicFact to store
            dataset_id: Optional ID of the dataset this fact belongs to
            embedding: Optional pre-computed embedding vector
            
        Returns:
            Fact ID
        """
        # Generate ID if not provides
        if not fact.fact_id:
            fact.fact_id = str(uuid.uuid4())
        
        # Build searchable content
        content = self._fact_to_text(fact)
        
        # Create document for vector store
        metadata = {
            "entity": fact.entity,
            "attribute": fact.attribute,
            "value": fact.value,
            "unit": fact.unit,
            "period": fact.period,
            "source_url": fact.source_url,
            "source_title": fact.source_title,
            "confidence_score": fact.confidence_score,
            "extracted_at": fact.extracted_at.isoformat(),
        }
        
        if dataset_id:
            metadata["dataset_id"] = dataset_id

        doc = Document(
            id=fact.fact_id,
            content=content,
            metadata=metadata,
            embedding=embedding,  # Attach pre-computed embedding
        )
        
        await self._vector_store.add([doc])
        self._facts[fact.fact_id] = fact
        
        logger.info(f"Added fact {fact.fact_id} via {dataset_id or 'manual'}", extra={"entity": fact.entity})
        return fact.fact_id
    
    async def add_facts(self, facts: list[AtomicFact], dataset_id: str | None = None) -> list[str]:
        """Add multiple facts."""
        ids = []
        for fact in facts:
            id = await self.add_fact(fact, dataset_id=dataset_id)
            ids.append(id)
        return ids
    
    async def get_fact(self, fact_id: str) -> AtomicFact | None:
        """Get a fact by ID."""
        # Check cache first
        if fact_id in self._facts:
            return self._facts[fact_id]
        
        # Query vector store
        docs = await self._vector_store.get([fact_id])
        if not docs:
            return None
        
        return self._doc_to_fact(docs[0])
    
    async def search(
        self,
        query: str,
        limit: int = 10,
        entity: str | None = None,
        dataset_id: str | None = None,
        min_confidence: float = 0.0,
    ) -> list[AtomicFact]:
        """
        Semantic search for facts.
        
        Args:
            query: Search query
            limit: Max results
            entity: Filter by entity
            dataset_id: Filter by dataset
            min_confidence: Minimum confidence score
            
        Returns:
            List of matching facts
        """
        # Build filter
        filter_dict = {}
        if entity:
            filter_dict["entity"] = entity
        if dataset_id:
            filter_dict["dataset_id"] = dataset_id
        
        results = await self._vector_store.search(query, limit=limit * 2, filter=filter_dict or None)
        
        facts = []
        for result in results:
            fact = self._result_to_fact(result)
            
            # Apply confidence filter
            if fact.confidence_score >= min_confidence:
                facts.append(fact)
            
            if len(facts) >= limit:
                break
        
        return facts
    
    async def delete_fact(self, fact_id: str) -> None:
        """Delete a fact by ID."""
        await self._vector_store.delete([fact_id])
        self._facts.pop(fact_id, None)
        logger.info(f"Deleted fact {fact_id}")

    async def delete_by_dataset(self, dataset_id: str) -> int:
        """
        Delete all facts for a specific dataset. 
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
        """Get list of loaded datasets (heuristic: look at recent facts or dedicated registry)."""
        # Since we don't have a separate table for datasets, we inferred it from facts.
        # This is expensive. We should track datasets properly.
        # For MVP, we can just return a hardcoded list or scan local cache.
        datasets = set()
        for f in self._facts.values():
            # We don't store dataset_id on AtomicFact yet (it's in metadata). 
            # We need to add it to AtomicFact schema or retrieve from metadata?
            # Schema change is expensive. 
            pass
        return []
    
    async def get_entities(self) -> list[str]:
        """Get list of unique entities."""
        return list(set(f.entity for f in self._facts.values()))
    
    async def get_facts_by_entity(self, entity: str) -> list[AtomicFact]:
        """
        Get all facts for a specific entity.
        
        Args:
            entity: Entity name to search for
            
        Returns:
            List of facts for the entity
        """
        return [f for f in self._facts.values() if f.entity == entity]
    
    
    def _fact_to_text(self, fact: AtomicFact) -> str:
        """Convert fact to searchable text."""
        parts = [
            f"{fact.entity} {fact.attribute}",
            f"value: {fact.value}",
        ]
        
        if fact.unit:
            parts.append(f"unit: {fact.unit}")
        if fact.period:
            parts.append(f"period: {fact.period}")
        
        return " | ".join(parts)
    
    def _doc_to_fact(self, doc: Document) -> AtomicFact:
        """Convert document to fact."""
        metadata = doc.metadata
        return AtomicFact(
            fact_id=doc.id,
            entity=metadata.get("entity", ""),
            attribute=metadata.get("attribute", ""),
            value=metadata.get("value", ""),
            unit=metadata.get("unit"),
            period=metadata.get("period"),
            source_url=metadata.get("source_url", ""),
            source_title=metadata.get("source_title", ""),
            confidence_score=metadata.get("confidence_score", 0.5),
            extracted_at=datetime.fromisoformat(metadata.get("extracted_at", datetime.utcnow().isoformat())),
        )
    
    def _result_to_fact(self, result) -> AtomicFact:
        """Convert search result to fact."""
        metadata = result.metadata
        return AtomicFact(
            fact_id=result.id,
            entity=metadata.get("entity", ""),
            attribute=metadata.get("attribute", ""),
            value=metadata.get("value", ""),
            unit=metadata.get("unit"),
            period=metadata.get("period"),
            source_url=metadata.get("source_url", ""),
            source_title=metadata.get("source_title", ""),
            confidence_score=metadata.get("confidence_score", 0.5),
        )
