# Embedding Package
"""
Embedding and reranking providers for RAG.

Models:
- Qwen3-Embedding-8B (OpenRouter API)
- Qwen3-Embedding-0.6B (Local)
- Qwen3-Reranker-0.6B (Local)
- Qwen3-VL-Embedding-2B (Local, Vision-Language)
- Qwen3-VL-Reranker-2B (Local, Vision-Language)
"""

from shared.embedding.qwen3_embedding import (
    EmbeddingProvider,
    OpenRouterEmbedding,
    LocalEmbedding,
    create_embedding_provider,
)
from shared.embedding.qwen3_reranker import (
    RerankerProvider,
    LocalReranker,
    RerankResult,
    create_reranker_provider,
)
from shared.embedding.qwen3_vl_embedding import (
    VLEmbeddingProvider,
    LocalVLEmbedding,
    VLInput,
    create_vl_embedding_provider,
)
from shared.embedding.qwen3_vl_reranker import (
    VLRerankerProvider,
    VLRerankResult,
    create_vl_reranker_provider,
)
from shared.embedding.model_manager import (
    get_embedding_provider,
    get_reranker_provider,
    reset_providers,
)

__all__ = [
    # Text Embedding
    "EmbeddingProvider",
    "OpenRouterEmbedding",
    "LocalEmbedding",
    "create_embedding_provider",
    # Text Reranking
    "RerankerProvider",
    "LocalReranker",
    "RerankResult",
    "create_reranker_provider",
    # Vision-Language Embedding
    "VLEmbeddingProvider",
    "LocalVLEmbedding",
    "VLInput",
    "create_vl_embedding_provider",
    # Vision-Language Reranking
    "VLRerankerProvider",
    "VLRerankResult",
    "create_vl_reranker_provider",
    # Model Manager (Singletons)
    "get_embedding_provider",
    "get_reranker_provider",
    "reset_providers",
]

