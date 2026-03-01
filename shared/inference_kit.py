"""
Tier 0 Inference Dependency Injection Kit

Provides a structured container for passing LLM, embedding, and reranking
capabilities down to kernel modules without creating hard dependencies.
Kernel modules should accept `kit: InferenceKit | None = None` and
gracefully fall back to heuristics if providers are missing.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from pydantic import BaseModel, ConfigDict

if TYPE_CHECKING:
    from shared.llm.provider import LLMProvider, LLMConfig
    from shared.embedding.manager import ModelManager


class InferenceKit(BaseModel):
    """Dependency injection container for inference providers.
    
    This kit maps external LLM and embedding providers into a standard
    interface for kernel modules. Instantiated by the Orchestrator service
    layer and passed through the DAG.
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    # LLM Provider Configuration
    llm: Any | None = None # Typed as Any to avoid hard dependency, validated when used
    llm_config: Any | None = None
    
    # Embedding/Reranking Provider
    embedder: Any | None = None
    
    @property
    def has_llm(self) -> bool:
        """Check if an LLM provider is available and configured."""
        return self.llm is not None and self.llm_config is not None
        
    @property
    def has_embedder(self) -> bool:
        """Check if an embedding provider is available."""
        return self.embedder is not None
        
    @property
    def has_reranker(self) -> bool:
        """Check if a reranking provider is available (often the same as embedder)."""
        return self.embedder is not None and hasattr(self.embedder, "rerank_single")

    @classmethod
    def empty(cls) -> "InferenceKit":
        """Create an empty kit (forces all modules to fallback to heuristics)."""
        return cls(llm=None, llm_config=None, embedder=None)

