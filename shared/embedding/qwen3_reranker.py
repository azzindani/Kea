"""
Qwen3 Reranker Provider.

Local inference: Qwen/Qwen3-Reranker-0.6B
"""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from typing import Any
from dataclasses import dataclass

from shared.logging import get_logger


logger = get_logger(__name__)


@dataclass
class RerankResult:
    """Result from reranking."""
    index: int
    score: float
    text: str


class RerankerProvider(ABC):
    """Abstract base class for reranker providers."""
    
    @abstractmethod
    async def rerank(
        self,
        query: str,
        documents: list[str],
        top_k: int | None = None,
    ) -> list[RerankResult]:
        """Rerank documents by relevance to query."""
        pass


class LocalReranker(RerankerProvider):
    """
    Qwen3-Reranker-0.6B local inference.
    
    Model: Qwen/Qwen3-Reranker-0.6B
    Max Length: 32768 tokens
    Requires: transformers>=4.51.0
    
    Usage:
        reranker = LocalReranker()
        results = await reranker.rerank("query", ["doc1", "doc2"])
    """
    
    # Class-level cache for model singleton (shared across all instances)
    _shared_model = None
    _shared_tokenizer = None
    _shared_lock = None
    _shared_token_true_id = None
    _shared_token_false_id = None
    _shared_prefix_tokens = None
    _shared_suffix_tokens = None
    
    def __init__(
        self,
        model_name: str = "Qwen/Qwen3-Reranker-0.6B",
        device: str | None = None,
        max_length: int = 32768,
        use_flash_attention: bool = False,
    ) -> None:
        self.model_name = model_name
        self.device = device or ("cuda" if self._has_cuda() else "cpu")
        if self.device == "cuda":
            self.device = "cuda:0"
        self.max_length = max_length
        self.use_flash_attention = use_flash_attention
    
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
        if LocalReranker._shared_model is not None:
            return LocalReranker._shared_model, LocalReranker._shared_tokenizer
        
        # Create class-level lock if not exists
        if LocalReranker._shared_lock is None:
            LocalReranker._shared_lock = threading.Lock()
        
        with LocalReranker._shared_lock:
            # Double-check pattern
            if LocalReranker._shared_model is not None:
                return LocalReranker._shared_model, LocalReranker._shared_tokenizer
            
            from transformers import AutoTokenizer, AutoModelForCausalLM
            
            # Load tokenizer - simple like official code
            LocalReranker._shared_tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                padding_side='left',
            )
            
            # Load model - keep it SIMPLE like official Qwen3 code
            if self.use_flash_attention:
                LocalReranker._shared_model = AutoModelForCausalLM.from_pretrained(
                    self.model_name,
                    torch_dtype=torch.float16,
                    attn_implementation="flash_attention_2",
                ).cuda().eval()
            else:
                # Simple load - exactly like official Qwen3 code
                LocalReranker._shared_model = AutoModelForCausalLM.from_pretrained(
                    self.model_name
                ).eval()
                
                # Move to GPU if requested
                if self.device.startswith("cuda"):
                    LocalReranker._shared_model = LocalReranker._shared_model.to(self.device)
            
            # Setup token IDs
            LocalReranker._shared_token_false_id = LocalReranker._shared_tokenizer.convert_tokens_to_ids("no")
            LocalReranker._shared_token_true_id = LocalReranker._shared_tokenizer.convert_tokens_to_ids("yes")
            
            # Setup prefix/suffix
            prefix = "<|im_start|>system\nJudge whether the Document meets the requirements based on the Query and the Instruct provided. Note that the answer can only be \"yes\" or \"no\".<|im_end|>\n<|im_start|>user\n"
            suffix = "<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n"
            
            LocalReranker._shared_prefix_tokens = LocalReranker._shared_tokenizer.encode(prefix, add_special_tokens=False)
            LocalReranker._shared_suffix_tokens = LocalReranker._shared_tokenizer.encode(suffix, add_special_tokens=False)
            
            logger.info(f"Loaded {self.model_name} on {LocalReranker._shared_model.device}")
        
        return LocalReranker._shared_model, LocalReranker._shared_tokenizer
    
    def move_to_device(self, new_device: str):
        """
        Move model to new device (e.g., 'cuda:1', 'cpu').
        
        Args:
            new_device: Target device string
        """
        if LocalReranker._shared_model:
            LocalReranker._shared_model = LocalReranker._shared_model.to(new_device)
        self.device = new_device
        logger.info(f"Model moved to {new_device}")
    
    def _format_instruction(
        self,
        query: str,
        doc: str,
        instruction: str | None = None,
    ) -> str:
        """Format input for reranker."""
        if instruction is None:
            instruction = "Given a web search query, retrieve relevant passages that answer the query"
        
        return f"<Instruct>: {instruction}\n<Query>: {query}\n<Document>: {doc}"
    
    def _process_inputs(self, pairs: list[str]):
        """Tokenize and process inputs using fast path."""
        import torch
        
        model, tokenizer = self._load_model()
        
        # Build complete prompts with prefix and suffix
        full_texts = []
        prefix = "<|im_start|>system\nJudge whether the Document meets the requirements based on the Query and the Instruct provided. Note that the answer can only be \"yes\" or \"no\".<|im_end|>\n<|im_start|>user\n"
        suffix = "<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n"
        
        for pair in pairs:
            # Truncate pair content if needed
            max_pair_len = self.max_length - len(LocalReranker._shared_prefix_tokens) - len(LocalReranker._shared_suffix_tokens)
            pair_tokens = tokenizer.encode(pair, add_special_tokens=False)
            if len(pair_tokens) > max_pair_len:
                pair_tokens = pair_tokens[:max_pair_len]
                pair = tokenizer.decode(pair_tokens)
            
            full_texts.append(prefix + pair + suffix)
        
        # Use __call__ directly (fast path - avoids warning)
        inputs = tokenizer(
            full_texts,
            padding=True,
            truncation=True,
            max_length=self.max_length,
            return_tensors="pt",
        )
        
        for key in inputs:
            inputs[key] = inputs[key].to(model.device)
        
        return inputs
    
    async def rerank(
        self,
        query: str,
        documents: list[str],
        top_k: int | None = None,
        instruction: str | None = None,
    ) -> list[RerankResult]:
        """Rerank documents by relevance to query."""
        import asyncio
        import torch
        
        if not documents:
            return []
        
        model, _ = self._load_model()
        
        # Batching configuration (to prevent OOM)
        BATCH_SIZE = 16 
        
        all_scores = []
        
        # Process in batches
        for i in range(0, len(documents), BATCH_SIZE):
            batch_docs = documents[i : i + BATCH_SIZE]
            
            # Format pairs for this batch
            pairs = [self._format_instruction(query, doc, instruction) for doc in batch_docs]
            
            # Process in executor (CPU/GPU bound)
            loop = asyncio.get_event_loop()
            
            def compute_batch_scores(batch_pairs):
                # Ensure we handle empty batch (unlikely)
                if not batch_pairs: return []
                
                inputs = self._process_inputs(batch_pairs)
                
                with torch.no_grad():
                    # Move inputs to device (redundant if process_inputs does it, but safe)
                    for k, v in inputs.items():
                        inputs[k] = v.to(model.device)
                        
                    batch_logits = model(**inputs).logits[:, -1, :]
                    true_vector = batch_logits[:, LocalReranker._shared_token_true_id]
                    false_vector = batch_logits[:, LocalReranker._shared_token_false_id]
                    stacked_scores = torch.stack([false_vector, true_vector], dim=1)
                    log_probs = torch.nn.functional.log_softmax(stacked_scores, dim=1)
                    return log_probs[:, 1].exp().tolist()
            
            # Run batch
            batch_scores = await loop.run_in_executor(None, compute_batch_scores, pairs)
            all_scores.extend(batch_scores)
            
            # Optional: Clear cache after every few batches if very large
            if len(documents) > 100 and i % (BATCH_SIZE * 4) == 0:
                torch.cuda.empty_cache() if torch.cuda.is_available() else None
        
        # Build results
        results = [
            RerankResult(index=i, score=score, text=documents[i])
            for i, score in enumerate(all_scores)
        ]
        
        # Sort by score descending
        results.sort(key=lambda x: x.score, reverse=True)
        
        if top_k:
            results = results[:top_k]
        
        return results


def create_reranker_provider(**kwargs) -> RerankerProvider:
    """Create a reranker provider."""
    return LocalReranker(**kwargs)
