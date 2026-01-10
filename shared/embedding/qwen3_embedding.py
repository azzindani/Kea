"""
Qwen3 Embedding Provider.

Supports:
- OpenRouter API: qwen/qwen3-embedding-8b
- Local: Qwen/Qwen3-Embedding-0.6B (via sentence-transformers)
"""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from typing import Any

from shared.logging import get_logger


logger = get_logger(__name__)


class EmbeddingProvider(ABC):
    """Abstract base class for embedding providers."""
    
    @abstractmethod
    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for texts."""
        pass
    
    @abstractmethod
    async def embed_query(self, query: str) -> list[float]:
        """Generate embedding for a query (with query prompt)."""
        pass
    
    @property
    @abstractmethod
    def dimension(self) -> int:
        """Return embedding dimension."""
        pass


class OpenRouterEmbedding(EmbeddingProvider):
    """
    Qwen3-Embedding-8B via OpenRouter API.
    
    Model: qwen/qwen3-embedding-8b
    Dimension: 4096 (default), supports 32-4096
    Context: 32k tokens
    
    Usage:
        provider = OpenRouterEmbedding()
        embeddings = await provider.embed(["Hello world"])
    """
    
    def __init__(
        self,
        api_key: str | None = None,
        dimension: int = 1024,
    ) -> None:
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY", "")
        self._dimension = dimension
        self.model = "qwen/qwen3-embedding-8b"
        self.base_url = "https://openrouter.ai/api/v1/embeddings"
    
    @property
    def dimension(self) -> int:
        return self._dimension
    
    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for documents."""
        import httpx
        
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY not set")
        
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "input": texts,
                    "dimensions": self._dimension,
                }
            )
            response.raise_for_status()
            data = response.json()
        
        # Extract embeddings in order
        embeddings = [None] * len(texts)
        for item in data["data"]:
            embeddings[item["index"]] = item["embedding"]
        
        return embeddings
    
    async def embed_query(self, query: str) -> list[float]:
        """Generate embedding for query with instruction."""
        # Qwen3 embedding uses instruction prefix for queries
        instruction = "Instruct: Given a web search query, retrieve relevant passages that answer the query\nQuery: "
        formatted_query = instruction + query
        
        embeddings = await self.embed([formatted_query])
        return embeddings[0]


class LocalEmbedding(EmbeddingProvider):
    """
    Qwen3-Embedding-0.6B local inference.
    
    Model: Qwen/Qwen3-Embedding-0.6B
    Dimension: up to 1024
    Requires: transformers>=4.51.0, sentence-transformers>=2.7.0
    
    Usage:
        provider = LocalEmbedding()
        embeddings = await provider.embed(["Hello world"])
    """
    
    def __init__(
        self,
        model_name: str = "Qwen/Qwen3-Embedding-0.6B",
        dimension: int = 1024,
        device: str | None = None,
        use_flash_attention: bool = False,
    ) -> None:
        self.model_name = model_name
        self._dimension = dimension
        self.device = device or ("cuda" if self._has_cuda() else "cpu")
        self.use_flash_attention = use_flash_attention
        self._model = None
    
    def _has_cuda(self) -> bool:
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            return False
    
    def _load_model(self):
        """Lazy load model."""
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            
            model_kwargs = {"device_map": "auto"} if self.device == "cuda" else {}
            
            if self.use_flash_attention:
                model_kwargs["attn_implementation"] = "flash_attention_2"
            
            self._model = SentenceTransformer(
                self.model_name,
                model_kwargs=model_kwargs,
                tokenizer_kwargs={"padding_side": "left"},
                trust_remote_code=True,
            )
            
            logger.info(f"Loaded {self.model_name} on {self.device}")
        
        return self._model
    
    @property
    def dimension(self) -> int:
        return self._dimension
    
    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for documents."""
        import asyncio
        
        model = self._load_model()
        
        # Run in executor to avoid blocking
        loop = asyncio.get_event_loop()
        embeddings = await loop.run_in_executor(
            None,
            lambda: model.encode(texts, normalize_embeddings=True).tolist()
        )
        
        return embeddings
    
    async def embed_query(self, query: str) -> list[float]:
        """Generate embedding for query with prompt."""
        import asyncio
        
        model = self._load_model()
        
        loop = asyncio.get_event_loop()
        embedding = await loop.run_in_executor(
            None,
            lambda: model.encode(
                [query],
                prompt_name="query",
                normalize_embeddings=True
            ).tolist()[0]
        )
        
        return embedding


# Factory function
def create_embedding_provider(
    use_local: bool = False,
    **kwargs
) -> EmbeddingProvider:
    """
    Create an embedding provider.
    
    Args:
        use_local: Use local model instead of API
        **kwargs: Provider-specific arguments
        
    Returns:
        EmbeddingProvider instance
    """
    if use_local:
        return LocalEmbedding(**kwargs)
    else:
        return OpenRouterEmbedding(**kwargs)
