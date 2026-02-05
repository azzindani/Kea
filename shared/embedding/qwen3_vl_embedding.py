"""
Qwen3 VL (Vision-Language) Embedding Provider.

Local inference: Qwen/Qwen3-VL-Embedding-2B

Uses the official Qwen3VLEmbedder pattern from scripts/qwen3_vl_embedding.
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
    image: str | None = None  # URL or file path


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
        if self.device == "cuda":
            self.device = "cuda:0"
        self.use_flash_attention = use_flash_attention
        self._embedder = None
    
    def _has_cuda(self) -> bool:
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            return False
    
    def _load_model(self):
        """Lazy load the Qwen3VLEmbedder model."""
        if self._embedder is None:
            try:
                import torch
                
                # Try to import the official Qwen3VLEmbedder
                try:
                    from scripts.qwen3_vl_embedding import Qwen3VLEmbedder
                except ImportError:
                    # Fall back to transformers-based implementation
                    logger.warning(
                        "scripts.qwen3_vl_embedding not found. "
                        "Using transformers-based fallback."
                    )
                    self._embedder = self._create_fallback_embedder()
                    return self._embedder
                
                # Use official Qwen3VLEmbedder
                model_kwargs = {}
                if self.use_flash_attention:
                    model_kwargs["attn_implementation"] = "flash_attention_2"
                    model_kwargs["torch_dtype"] = torch.float16
                
                self._embedder = Qwen3VLEmbedder(
                    model_name_or_path=self.model_name,
                    **model_kwargs,
                )
                
                logger.info(f"Loaded {self.model_name} with Qwen3VLEmbedder")
                
            except Exception as e:
                logger.error(f"Failed to load VL embedding model: {e}")
                raise
        
        return self._embedder
    
    def _create_fallback_embedder(self):
        """Create a fallback embedder using transformers directly."""
        import torch
        from transformers import AutoModel, AutoProcessor
        
        class FallbackVLEmbedder:
            def __init__(self, model_name: str, device: str, use_flash_attention: bool):
                self.device = device
                
                self.processor = AutoProcessor.from_pretrained(
                    model_name,
                    trust_remote_code=True,
                )
                
                model_kwargs = {"torch_dtype": torch.float16}
                if use_flash_attention:
                    model_kwargs["attn_implementation"] = "flash_attention_2"
                
                self.model = AutoModel.from_pretrained(
                    model_name,
                    **model_kwargs,
                    trust_remote_code=True,
                ).eval()
                
                if device.startswith("cuda"):
                    self.model = self.model.to(device)
            
            def process(self, inputs: list[dict]) -> torch.Tensor:
                """Process inputs and return embeddings."""
                import torch.nn.functional as F
                
                embeddings_list = []
                
                with torch.no_grad():
                    for inp in inputs:
                        # Build messages for processor
                        content = []
                        if "image" in inp:
                            content.append({"type": "image", "image": inp["image"]})
                        if "text" in inp:
                            content.append({"type": "text", "text": inp["text"]})
                        
                        if not content:
                            # Empty input, return zero embedding
                            embeddings_list.append(torch.zeros(1024))
                            continue
                        
                        messages = [{"role": "user", "content": content}]
                        
                        try:
                            # Process input
                            processed = self.processor(
                                text=self.processor.apply_chat_template(messages, tokenize=False),
                                images=[inp.get("image")] if "image" in inp else None,
                                return_tensors="pt",
                            )
                            processed = {k: v.to(self.model.device) for k, v in processed.items()}
                            
                            # Get embedding
                            outputs = self.model(**processed)
                            # Use last hidden state mean pooling
                            emb = outputs.last_hidden_state.mean(dim=1).squeeze()
                            emb = F.normalize(emb, p=2, dim=0)
                            embeddings_list.append(emb.cpu())
                        except Exception as e:
                            logger.warning(f"VL embedding failed for input: {e}")
                            embeddings_list.append(torch.zeros(1024))
                
                return torch.stack(embeddings_list)
        
        return FallbackVLEmbedder(self.model_name, self.device, self.use_flash_attention)
    
    async def embed(self, inputs: list[VLInput]) -> list[list[float]]:
        """Generate embeddings for vision-language inputs."""
        import asyncio
        
        embedder = self._load_model()
        
        # Format inputs as dicts (official format)
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
            return embedder.process(formatted_inputs).tolist()
        
        embeddings = await loop.run_in_executor(None, compute_embeddings)
        return embeddings
    
    async def embed_query(self, query: str, task: str | None = None) -> list[float]:
        """Generate embedding for a text query."""
        if task is None:
            task = "Given a web search query, retrieve relevant passages that answer the query"
        
        formatted_query = f"Instruct: {task}\nQuery: {query}"
        result = await self.embed([VLInput(text=formatted_query)])
        return result[0]


def create_vl_embedding_provider(**kwargs) -> VLEmbeddingProvider:
    """Create a vision-language embedding provider."""
    return LocalVLEmbedding(**kwargs)
