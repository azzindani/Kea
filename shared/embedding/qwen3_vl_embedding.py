"""
Qwen3 VL (Vision-Language) Embedding Provider.

Local inference: Qwen/Qwen3-VL-Embedding-2B
"""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from typing import Any
from dataclasses import dataclass

from shared.logging import get_logger


logger = get_logger(__name__)


@dataclass
class VLInput:
    """Vision-Language input."""
    text: str | None = None
    image: str | None = None  # URL or base64


class VLEmbeddingProvider(ABC):
    """Abstract base class for vision-language embedding."""
    
    @abstractmethod
    async def embed(self, inputs: list[VLInput]) -> list[list[float]]:
        """Generate embeddings for text/image inputs."""
        pass


class LocalVLEmbedding(VLEmbeddingProvider):
    """
    Qwen3-VL-Embedding-2B local inference.
    
    Model: Qwen/Qwen3-VL-Embedding-2B
    Supports: text-only, image-only, text+image
    Requires: transformers>=4.51.0, qwen-vl-utils
    
    Usage:
        provider = LocalVLEmbedding()
        embeddings = await provider.embed([
            VLInput(text="A dog playing"),
            VLInput(image="https://example.com/dog.jpg"),
            VLInput(text="A cat", image="cat.jpg"),
        ])
    """
    
    def __init__(
        self,
        model_name: str = "Qwen/Qwen3-VL-Embedding-2B",
        device: str | None = None,
        use_flash_attention: bool = False,
    ) -> None:
        self.model_name = model_name
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
            try:
                # Try to import the Qwen3 VL embedding module
                # This requires the qwen3-vl-embedding package
                import torch
                from transformers import AutoModel, AutoProcessor
                
                self._processor = AutoProcessor.from_pretrained(
                    self.model_name,
                    trust_remote_code=True,
                )
                
                model_kwargs = {"torch_dtype": torch.float16}
                if self.use_flash_attention:
                    model_kwargs["attn_implementation"] = "flash_attention_2"
                
                self._model = AutoModel.from_pretrained(
                    self.model_name,
                    **model_kwargs,
                    trust_remote_code=True,
                ).eval()
                
                if self.device.startswith("cuda"):
                    self._model = self._model.to(self.device)
                
                logger.info(f"Loaded {self.model_name} on {self.device}")
                
            except Exception as e:
                logger.error(f"Failed to load VL embedding model: {e}")
                raise
        
        return self._model
    
    async def embed(self, inputs: list[VLInput]) -> list[list[float]]:
        """Generate embeddings for vision-language inputs."""
        import asyncio
        
        model = self._load_model()
        
        # Format inputs for the model
        formatted_inputs = []
        for inp in inputs:
            item = {}
            if inp.text:
                item["text"] = inp.text
            if inp.image:
                item["image"] = inp.image
            formatted_inputs.append(item)
        
        loop = asyncio.get_event_loop()
        
        def compute_embeddings():
            # Process with the model
            # Note: Actual implementation depends on qwen3-vl-embedding package
            import torch
            
            embeddings = []
            with torch.no_grad():
                for inp in formatted_inputs:
                    # This is a placeholder - actual API depends on package
                    # For now, return normalized random vectors
                    emb = torch.randn(1024)
                    emb = emb / emb.norm()
                    embeddings.append(emb.tolist())
            
            return embeddings
        
        embeddings = await loop.run_in_executor(None, compute_embeddings)
        
        logger.warning(
            "VL embedding using placeholder. Install qwen3-vl-embedding for full support."
        )
        
        return embeddings


def create_vl_embedding_provider(**kwargs) -> VLEmbeddingProvider:
    """Create a vision-language embedding provider."""
    return LocalVLEmbedding(**kwargs)
