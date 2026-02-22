"""
Qwen3 VL (Vision-Language) Reranker Provider.

Local inference: Qwen/Qwen3-VL-Embedding-2B (uses embedding similarity for reranking)

Based on official Qwen3 VL usage patterns.
"""

from __future__ import annotations

from dataclasses import dataclass

from shared.logging.main import get_logger
from shared.embedding.qwen3_vl_embedding import VLInput, LocalVLEmbedding


logger = get_logger(__name__)


@dataclass
class VLRerankResult:
    """Result from vision-language reranking."""
    index: int
    score: float
    input: VLInput


class VLRerankerProvider:
    """
    Qwen3 VL Reranker using embedding similarity.
    
    Uses Qwen/Qwen3-VL-Embedding-2B to compute query-document similarity.
    
    Usage:
        reranker = VLRerankerProvider()
        results = await reranker.rerank(
            query="A dog on a beach",
            documents=[
                VLInput(image="beach_dog.jpg"),
                VLInput(text="Cat in garden"),
            ]
        )
    """
    
    def __init__(
        self,
        model_name: str | None = None,
        device: str | None = None,
        use_flash_attention: bool = False,
    ) -> None:
        from shared.config import get_settings
        settings = get_settings()
        # VLReranker uses the VL Embedding model for similarity-based scoring
        self.model_name = model_name or settings.vl_reranker.model_name or settings.vl_embedding.model_name
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
    
    def _load_embedder(self) -> LocalVLEmbedding:
        """Lazy load the VL embedding model."""
        if self._embedder is None:
            self._embedder = LocalVLEmbedding(
                model_name=self.model_name,
                device=self.device,
                use_flash_attention=self.use_flash_attention,
            )
            logger.info(f"VL Reranker using {self.model_name} for embedding-based scoring")
        return self._embedder
    
    async def rerank(
        self,
        query: str,
        documents: list[VLInput],
        top_k: int | None = None,
        task: str | None = None,
    ) -> list[VLRerankResult]:
        """
        Rerank vision-language documents by relevance to query.
        
        Uses embedding similarity between query and documents.
        
        Args:
            query: Text query
            documents: List of VLInput documents (text/image/both)
            top_k: Return only top_k results
            task: Optional task description for query formatting
            
        Returns:
            Sorted list of VLRerankResult by score descending
        """
        import torch
        
        if not documents:
            return []
        
        embedder = self._load_embedder()
        
        # Get query embedding
        query_emb = await embedder.embed_query(query, task)
        query_tensor = torch.tensor(query_emb).unsqueeze(0)
        
        # Get document embeddings
        doc_embs = await embedder.embed(documents)
        doc_tensor = torch.tensor(doc_embs)
        
        # Compute similarity scores (cosine similarity since embeddings are normalized)
        scores = (query_tensor @ doc_tensor.T).squeeze(0).tolist()
        
        # Handle single document case
        if not isinstance(scores, list):
            scores = [scores]
        
        # Build results
        results = [
            VLRerankResult(index=i, score=score, input=documents[i])
            for i, score in enumerate(scores)
        ]
        
        # Sort by score descending
        results.sort(key=lambda x: x.score, reverse=True)
        
        if top_k:
            results = results[:top_k]
        
        return results


def create_vl_reranker_provider(**kwargs) -> VLRerankerProvider:
    """Create a vision-language reranker provider."""
    return VLRerankerProvider(**kwargs)
