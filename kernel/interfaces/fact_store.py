
"""
Fact Store Interface.

Defines the protocol for storing and retrieving facts, allowing
the kernel to use RAG without depending on the RAG Service implementation.
"""
from typing import Any, Protocol, List, Dict, Optional, runtime_checkable
from shared.schemas import AtomicFact

@runtime_checkable
class FactStore(Protocol):
    """Protocol for interacting with the fact store."""
    
    async def search(self, query: str, limit: int = 10) -> List[AtomicFact]:
        """Search for facts matching a query."""
        ...
        
    async def add(self, fact: AtomicFact) -> None:
        """Add a fact to the store."""
        ...

# Global store instance
_store: Optional[FactStore] = None

def register_fact_store(store: FactStore) -> None:
    """Register the global fact store implementation."""
    global _store
    _store = store

def get_fact_store() -> Optional[FactStore]:
    """Get the global fact store."""
    return _store
