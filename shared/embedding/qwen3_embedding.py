"""
Qwen3 Embedding Provider.

Supports:
- OpenRouter API: qwen/qwen3-embedding-8b
- Local: Qwen/Qwen3-Embedding-0.6B (via transformers)

Uses official Qwen3 embedding pattern with last_token_pool.
"""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from typing import Any

from shared.logging import get_logger

# Pre-import transformers to avoid threading issues in Colab/Kaggle
# These imports happen at module load time, before any threads spawn
try:
    from transformers import AutoTokenizer, AutoModel
    _TRANSFORMERS_AVAILABLE = True
except ImportError:
    _TRANSFORMERS_AVAILABLE = False
    AutoTokenizer = None
    AutoModel = None


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
        dimension: int = 4096,
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
    Qwen3-Embedding-0.6B local inference using official pattern.
    
    Model: Qwen/Qwen3-Embedding-0.6B
    Dimension: up to 1024
    Requires: transformers>=4.51.0
    
    Uses last_token_pool pattern as per official Qwen3 documentation.
    
    Usage:
        provider = LocalEmbedding()
        embeddings = await provider.embed(["Hello world"])
    """
    
    # Class-level cache for model singleton (shared across all instances)
    _shared_model = None
    _shared_tokenizer = None
    _shared_lock = None  # Will be created on first use
    _shared_device = None
    
    def __init__(
        self,
        model_name: str = "Qwen/Qwen3-Embedding-0.6B",
        dimension: int = 1024,
        device: str | None = None,
        use_flash_attention: bool = False,
        max_length: int = 32768,
    ) -> None:
        self.model_name = model_name
        self._dimension = dimension
        self.device = device or ("cuda" if self._has_cuda() else "cpu")
        self.use_flash_attention = use_flash_attention
        self.max_length = max_length
    
    def _has_cuda(self) -> bool:
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            return False
    
    def _load_model(self):
        """Lazy load model and tokenizer with thread safety (class-level singleton)."""
        import threading
        import torch
        
        # Fast path: model already loaded
        if LocalEmbedding._shared_model is not None:
            return LocalEmbedding._shared_model, LocalEmbedding._shared_tokenizer
        
        if not _TRANSFORMERS_AVAILABLE:
            raise ImportError("transformers library is required for local embedding")
        
        # Create class-level lock if not exists
        if LocalEmbedding._shared_lock is None:
            LocalEmbedding._shared_lock = threading.Lock()
        
        with LocalEmbedding._shared_lock:
            # Double-check pattern
            if LocalEmbedding._shared_model is not None:
                return LocalEmbedding._shared_model, LocalEmbedding._shared_tokenizer
            
            # Pin to specific device
            device = self.device
            if device == "cuda":
                device = "cuda:0"
            
            # Load tokenizer (matches working test code)
            LocalEmbedding._shared_tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                padding_side='left',  # Required for Qwen3 embedding
            )
            
            # Load model - keep it SIMPLE like the user's working test code
            # Don't add extra parameters that cause meta tensor issues
            if self.use_flash_attention:
                LocalEmbedding._shared_model = AutoModel.from_pretrained(
                    self.model_name,
                    attn_implementation="flash_attention_2",
                    torch_dtype=torch.float16,
                ).cuda()
            else:
                # Simple load - exactly like user's working code
                LocalEmbedding._shared_model = AutoModel.from_pretrained(self.model_name)
                
                # Move to GPU if requested
                if device.startswith("cuda"):
                    LocalEmbedding._shared_model = LocalEmbedding._shared_model.to(device)
            
            LocalEmbedding._shared_model.eval()  # Set to eval mode
            LocalEmbedding._shared_device = device
            logger.info(f"Loaded {self.model_name} on {LocalEmbedding._shared_model.device}")
        
        return LocalEmbedding._shared_model, LocalEmbedding._shared_tokenizer
    
    def _last_token_pool(self, last_hidden_states, attention_mask):
        """
        Pool the last token representation (official Qwen3 pattern).
        
        Handles both left-padding and right-padding cases.
        """
        import torch
        
        left_padding = (attention_mask[:, -1].sum() == attention_mask.shape[0])
        if left_padding:
            return last_hidden_states[:, -1]
        else:
            sequence_lengths = attention_mask.sum(dim=1) - 1
            batch_size = last_hidden_states.shape[0]
            return last_hidden_states[
                torch.arange(batch_size, device=last_hidden_states.device),
                sequence_lengths
            ]
    
    def _get_detailed_instruct(self, task_description: str, query: str) -> str:
        """Format query with instruction (official Qwen3 pattern)."""
        return f'Instruct: {task_description}\nQuery:{query}'
    
    @property
    def dimension(self) -> int:
        return self._dimension
    
    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for documents using official Qwen3 pattern."""
        import asyncio
        import torch
        import torch.nn.functional as F
        
        model, tokenizer = self._load_model()
        loop = asyncio.get_event_loop()
        
        # Check VRAM pressure and adjust batch size
        batch_size = 32  # Default batch size
        try:
            from shared.hardware.detector import detect_hardware
            hw = detect_hardware()
            if hw.cuda_available:
                hw.refresh_vram()
                if hw.vram_pressure() > 0.8:
                    batch_size = 8
                    logger.warning(f"VRAM pressure high ({hw.vram_pressure()*100:.1f}%), reducing batch to {batch_size}")
                elif hw.vram_pressure() > 0.6:
                    batch_size = 16
        except Exception:
            pass
        
        def encode_batch(batch_texts: list[str]) -> list[list[float]]:
            """Encode a batch of texts using official pattern."""
            # Tokenize with __call__ method (fast path)
            batch_dict = tokenizer(
                batch_texts,
                padding=True,
                truncation=True,
                max_length=self.max_length,
                return_tensors="pt",
            )
            batch_dict = {k: v.to(model.device) for k, v in batch_dict.items()}
            
            with torch.no_grad():
                outputs = model(**batch_dict)
                embeddings = self._last_token_pool(
                    outputs.last_hidden_state,
                    batch_dict['attention_mask']
                )
                # Normalize embeddings
                embeddings = F.normalize(embeddings, p=2, dim=1)
            
            return embeddings.cpu().tolist()
        
        def process_all():
            """Process all texts in batches."""
            all_embeddings = []
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                embs = encode_batch(batch)
                all_embeddings.extend(embs)
                # Clear cache after each batch
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            return all_embeddings
        
        embeddings = await loop.run_in_executor(None, process_all)
        return embeddings
    
    async def embed_query(self, query: str, task: str | None = None) -> list[float]:
        """Generate embedding for query with instruction (official Qwen3 pattern)."""
        if task is None:
            task = "Given a web search query, retrieve relevant passages that answer the query"
        
        # Format query with instruction
        formatted_query = self._get_detailed_instruct(task, query)
        
        embeddings = await self.embed([formatted_query])
        return embeddings[0]


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
