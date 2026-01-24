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
        self._model = None
        self._tokenizer = None
        self._token_true_id = None
        self._token_false_id = None
        self._prefix_tokens = None
        self._suffix_tokens = None
    
    def _has_cuda(self) -> bool:
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            return False
    
    def _load_model(self):
        """Lazy load model and tokenizer."""
        if self._model is None:
            import torch
            from transformers import AutoTokenizer, AutoModelForCausalLM
            
            self._tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                padding_side='left',
                trust_remote_code=True,
            )
            
            model_kwargs = {"torch_dtype": torch.float16}
            if self.use_flash_attention:
                model_kwargs["attn_implementation"] = "flash_attention_2"
            
            self._model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                **model_kwargs,
                trust_remote_code=True,
            ).eval()
            
            # Move to GPU if cuda device specified
            if self.device.startswith("cuda"):
                self._model = self._model.to(self.device)
            
            # Setup token IDs
            self._token_false_id = self._tokenizer.convert_tokens_to_ids("no")
            self._token_true_id = self._tokenizer.convert_tokens_to_ids("yes")
            
            # Setup prefix/suffix
            prefix = "<|im_start|>system\nJudge whether the Document meets the requirements based on the Query and the Instruct provided. Note that the answer can only be \"yes\" or \"no\".<|im_end|>\n<|im_start|>user\n"
            suffix = "<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n"
            
            self._prefix_tokens = self._tokenizer.encode(prefix, add_special_tokens=False)
            self._suffix_tokens = self._tokenizer.encode(suffix, add_special_tokens=False)
            
            logger.info(f"Loaded {self.model_name} on {self.device}")
        
        return self._model, self._tokenizer
    
    def move_to_device(self, new_device: str):
        """
        Move model to new device (e.g., 'cuda:1', 'cpu').
        
        Args:
            new_device: Target device string
        """
        if self._model:
            self._model = self._model.to(new_device)
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
            max_pair_len = self.max_length - len(self._prefix_tokens) - len(self._suffix_tokens)
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
        
        # Format pairs
        pairs = [self._format_instruction(query, doc, instruction) for doc in documents]
        
        # Process in executor
        loop = asyncio.get_event_loop()
        
        def compute_scores():
            inputs = self._process_inputs(pairs)
            
            with torch.no_grad():
                batch_scores = model(**inputs).logits[:, -1, :]
                true_vector = batch_scores[:, self._token_true_id]
                false_vector = batch_scores[:, self._token_false_id]
                batch_scores = torch.stack([false_vector, true_vector], dim=1)
                batch_scores = torch.nn.functional.log_softmax(batch_scores, dim=1)
                scores = batch_scores[:, 1].exp().tolist()
            
            return scores
        
        scores = await loop.run_in_executor(None, compute_scores)
        
        # Build results
        results = [
            RerankResult(index=i, score=score, text=documents[i])
            for i, score in enumerate(scores)
        ]
        
        # Sort by score descending
        results.sort(key=lambda x: x.score, reverse=True)
        
        if top_k:
            results = results[:top_k]
        
        return results


def create_reranker_provider(**kwargs) -> RerankerProvider:
    """Create a reranker provider."""
    return LocalReranker(**kwargs)
