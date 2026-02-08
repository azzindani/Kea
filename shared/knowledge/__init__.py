"""
Knowledge Package.

Context engineering for Kea - provides dynamic knowledge retrieval
from the knowledge/ directory (skills, rules, personas) using pgvector
semantic search, mirroring the RAG tool retrieval pattern.
"""

from shared.knowledge.registry import PostgresKnowledgeRegistry
from shared.knowledge.retriever import KnowledgeRetriever, get_knowledge_retriever

__all__ = [
    "PostgresKnowledgeRegistry",
    "KnowledgeRetriever",
    "get_knowledge_retriever",
]
