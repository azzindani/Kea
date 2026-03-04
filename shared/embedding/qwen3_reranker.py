"""
Qwen3 Reranker Provider.

Local inference: Qwen/Qwen3-Reranker-0.6B
"""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from typing import Any
from dataclasses import dataclass

from shared.logging.main import get_logger


from shared.logging.main import get_logger
from shared.hardware.gpu_lock import get_gpu_inference_lock
 
import threading
_MODULE_LOCK = threading.Lock()


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
        
    async def load(self) -> None:
        """Pre-load the model."""
        pass


class LocalReranker(RerankerProvider):
    """
    Qwen3-Reranker-0.6B local inference.
    """
    
    # Class-level cache for model singleton (shared across all instances)
    _shared_model = None
    _shared_tokenizer = None
    _shared_lock = None
    _shared_prefix_tokens = None
    _shared_suffix_tokens = None
    _shared_token_true_id = None
    _shared_token_false_id = None
    _shared_execution_lock_DEBUG_REMOVED = None # REMOVED
    _shared_inference_lock = None # Threading lock for multi-service cross-thread inference
    
    def __init__(
        self,
        model_name: str | None = None,
        device: str | None = None,
        max_length: int | None = None,
        use_flash_attention: bool = False,
        **kwargs: Any,
    ) -> None:
        from shared.config import get_settings
        settings = get_settings()
        self.model_name = model_name or settings.reranker.model_name
        self.device = device or ("cuda" if self._has_cuda() else "cpu")
        self.max_length = max_length or settings.reranker.max_length
        self.use_flash_attention = use_flash_attention
        
        self._exec_lock = None
    
    def _has_cuda(self) -> bool:
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            return False

    async def load(self) -> None:
        """Force the model to load into memory/GPU now."""
        import asyncio
        if self._exec_lock is None:
            self._exec_lock = asyncio.Lock()
            
        async with self._exec_lock:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, self._load_model)

    def _get_locks(self):
        """Thread-safe acquisition of class-level locks."""
        if LocalReranker._shared_lock is None:
            with _MODULE_LOCK:
                if LocalReranker._shared_lock is None:
                    LocalReranker._shared_lock = threading.Lock()
        
        # Share the global GPU lock across models
        return LocalReranker._shared_lock, get_gpu_inference_lock()

    def _load_model(self):
        """Lazy load model and tokenizer with thread safety (class-level singleton)."""
        import torch
        from transformers import AutoTokenizer, AutoModelForCausalLM
        
        # Fast path
        if LocalReranker._shared_model is not None:
            return LocalReranker._shared_model, LocalReranker._shared_tokenizer
        
        load_lock, _ = self._get_locks()
        
        with load_lock:
            if LocalReranker._shared_model is not None:
                return LocalReranker._shared_model, LocalReranker._shared_tokenizer
            
            device = self.device
            logger.info(f"Loading {self.model_name} on {device} (Thread: {threading.get_ident()})")
            
            # Explicit cache clear before loading
            if "cuda" in device:
                torch.cuda.empty_cache()
            
            # Load tokenizer
            LocalReranker._shared_tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                padding_side='left',
            )
            
            # Load model
            torch_dtype = torch.float16 if "cuda" in device else torch.float32
            
            if self.use_flash_attention:
                LocalReranker._shared_model = AutoModelForCausalLM.from_pretrained(
                    self.model_name,
                    torch_dtype=torch_dtype,
                    attn_implementation="flash_attention_2",
                ).to(device)
            else:
                LocalReranker._shared_model = AutoModelForCausalLM.from_pretrained(
                    self.model_name,
                )
                if device.startswith("cuda"):
                    LocalReranker._shared_model = LocalReranker._shared_model.to(device)
                    LocalReranker._shared_model = LocalReranker._shared_model.half()
            
            LocalReranker._shared_model.eval()
            
            # Setup token IDs
            LocalReranker._shared_token_false_id = LocalReranker._shared_tokenizer.convert_tokens_to_ids("no")
            LocalReranker._shared_token_true_id = LocalReranker._shared_tokenizer.convert_tokens_to_ids("yes")
            
            # Setup prefix/suffix
            prefix = "<|im_start|>system\nJudge whether the Document meets the requirements based on the Query and the Instruct provided. Note that the answer can only be \"yes\" or \"no\".<|im_end|>\n<|im_start|>user\n"
            suffix = "<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n"
            
            LocalReranker._shared_prefix_tokens = LocalReranker._shared_tokenizer.encode(prefix, add_special_tokens=False)
            LocalReranker._shared_suffix_tokens = LocalReranker._shared_tokenizer.encode(suffix, add_special_tokens=False)
            
            # Final cache clear
            if "cuda" in device:
                torch.cuda.empty_cache()
                
            logger.info(f"Loaded {self.model_name} successfully on {LocalReranker._shared_model.device}")
        
        return LocalReranker._shared_model, LocalReranker._shared_tokenizer
    
    def move_to_device(self, new_device: str):
        """Move model to new device."""
        if LocalReranker._shared_model:
            import torch
            LocalReranker._shared_model = LocalReranker._shared_model.to(new_device)
            self.device = new_device
            logger.info(f"Reranker model moved to {new_device}")

    def _format_instruction(
        self,
        query: str,
        doc: str,
        instruction: str | None = None,
    ) -> str:
        """Format input for reranker."""
        if instruction is None:
            from shared.config import get_settings
            instruction = get_settings().reranker.instruction
        
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
        
        if self._exec_lock is None:
            self._exec_lock = asyncio.Lock()
            
        async with self._exec_lock:
            # Always ensure model is loaded via executor
            if LocalReranker._shared_model is None:
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(None, self._load_model)
                
            model, _ = LocalReranker._shared_model, LocalReranker._shared_tokenizer
            
            from shared.config import get_settings
            settings = get_settings()
            
            # Batching configuration
            BATCH_SIZE = settings.reranker.batch_size or 8
            
            loop = asyncio.get_event_loop()
            
            def compute_all_scores():
                nonlocal BATCH_SIZE
                import math
                out_scores = []
                
                def compute_batch_scores(batch_pairs):
                    if not batch_pairs: return []
                    inputs = self._process_inputs(batch_pairs)
                    # Thread-safe model call
                    # Use Global GPU Lock to prevent conflicts with other models (e.g. embedder)
                    _, gpu_lock = self._get_locks()
                    with gpu_lock:
                        with torch.no_grad():
                            outputs = model(**inputs)
                            batch_logits = outputs.logits[:, -1, :]
                            
                            # Score calculation
                            true_vector = batch_logits[:, LocalReranker._shared_token_true_id]
                            false_vector = batch_logits[:, LocalReranker._shared_token_false_id]
                            
                            # Logits to probabilities (softmax on yes/no)
                            # Using cat + softmax to get normalized score
                            pair_logits = torch.stack([false_vector, true_vector], dim=1)
                            probs = torch.softmax(pair_logits, dim=1)
                            scores = probs[:, 1].cpu().tolist()
                            
                            # Cleanup to prevent OOM
                            del outputs, batch_logits, true_vector, false_vector, pair_logits, probs
                            return scores
                
                i = 0
                while i < len(documents):
                    actual_batch = min(BATCH_SIZE, len(documents) - i)
                    batch_docs = documents[i : i + actual_batch]
                    pairs = [self._format_instruction(query, doc, instruction) for doc in batch_docs]
                    
                    try:
                        batch_scores = compute_batch_scores(pairs)
                        out_scores.extend(batch_scores)
                        i += actual_batch
                    except Exception as e:
                        if "OutOfMemory" in str(type(e).__name__) or "CUDA out of memory" in str(e):
                            logger.warning(f"Reranker OOM error on batch size {actual_batch}. Halving batch size.")
                            if torch.cuda.is_available():
                                torch.cuda.empty_cache()
                            if BATCH_SIZE > 1:
                                BATCH_SIZE = math.ceil(BATCH_SIZE / 2)
                                continue
                            else:
                                raise
                        raise
                return out_scores
                
            all_scores = await loop.run_in_executor(None, compute_all_scores)
        
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
