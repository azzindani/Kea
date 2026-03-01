"""
Model Manager.

Singleton manager for embedding and reranker models.
Loads models once, shares across the system.
"""

from __future__ import annotations

from shared.logging.main import get_logger

logger = get_logger(__name__)

# Singletons
_embedding_provider = None
_reranker_provider = None


def get_embedding_provider(use_local: bool | None = None):
    """
    Get or create singleton embedding provider.
    
    Args:
        use_local: Force local (True) or API (False). None = use config default.
        
    Returns:
        EmbeddingProvider instance
    """
    global _embedding_provider
    
    # Get config
    from shared.config import get_settings
    config = get_settings()
    
    # Determine local vs api
    if use_local is None:
        use_local = config.embedding.use_local
        
        # Fallback to hardware check if config says use_local=True but no GPU?
        if use_local:
             from shared.hardware.detector import detect_hardware
             hw = detect_hardware()
             if not hw.can_use_gpu_embedding():
                 # Config requested local but hardware sucks? 
                 # We'll try anyway, let CPU handle it or fail gracefully.
                 logger.info("Model Manager: Using local embedding as configured (Hardware check skipped)")
    
    if _embedding_provider is None:
        from shared.embedding.qwen3_embedding import (
            create_embedding_provider, 
            EmbeddingProvider
        )
        
        # Define Fallback Wrapper
        class FallbackEmbeddingProvider(EmbeddingProvider):
            """Wrapper that tries primary (Local) and falls back to secondary (API)."""
            
            def __init__(self, primary: EmbeddingProvider, secondary: EmbeddingProvider):
                self.primary = primary
                self.secondary = secondary
                self.using_secondary = False
                self._dim = primary.dimension
                
            @property
            def dimension(self) -> int:
                return self._dim
                
            async def embed(self, texts: list[str]) -> list[list[float]]:
                if self.using_secondary:
                    return await self.secondary.embed(texts)
                
                try:
                    return await self.primary.embed(texts)
                except Exception as e:
                    logger.error(f"Start-up/Runtime Error in Local Embedding: {e}")
                    logger.warning(">> SWITCHING TO API FALLBACK (OpenRouter) <<")
                    self.using_secondary = True
                    return await self.secondary.embed(texts)
            
            async def embed_query(self, query: str) -> list[float]:
                if self.using_secondary:
                    return await self.secondary.embed_query(query)
                
                try:
                    return await self.primary.embed_query(query)
                except Exception as e:
                    logger.error(f"Start-up/Runtime Error in Local Embedding: {e}")
                    logger.warning(">> SWITCHING TO API FALLBACK (OpenRouter) <<")
                    self.using_secondary = True
                    return await self.secondary.embed_query(query)

        if use_local:
            # Create BOTH local and API providers
            # We initialize them but local load is lazy, so it won't crash yet.
            log_msg = f"Model Manager: Initializing Primary (Local: {config.embedding.model_name}) + Fallback (API: {config.embedding.api_model})"
            logger.info(log_msg)
            
            try:
                primary = create_embedding_provider(
                    use_local=True,
                    model_name=config.embedding.model_name,
                    dimension=config.embedding.dimension
                )
                
                secondary = create_embedding_provider(
                    use_local=False, # Force API
                    dimension=config.embedding.dimension # Must match local dim (1024)
                )
                
                _embedding_provider = FallbackEmbeddingProvider(primary, secondary)
                
            except Exception as e:
                # If even initialization fails (e.g. import error), fall back immediately
                logger.error(f"Model Manager: Failed to initialize Local provider: {e}")
                logger.warning("Model Manager: Falling back to API provider immediately.")
                _embedding_provider = create_embedding_provider(
                    use_local=False,
                    dimension=config.embedding.dimension
                )
        else:
            # API Only requested
            _embedding_provider = create_embedding_provider(
                use_local=False,
                dimension=config.embedding.dimension
            )
            logger.info(f"Model Manager: Embedding provider initialized (API Only)")
    
    return _embedding_provider


def get_reranker_provider():
    """
    Get or create singleton reranker provider.
    
    Returns:
        RerankerProvider instance
    """
    global _reranker_provider
    
    # Get config
    from shared.config import get_settings
    config = get_settings()
    
    if _reranker_provider is None:
        from shared.embedding.qwen3_reranker import create_reranker_provider
        
        _reranker_provider = create_reranker_provider(
            model_name=config.reranker.model_name
        )
        logger.info(f"Model Manager: Reranker provider initialized ({config.reranker.model_name})")
    
    return _reranker_provider



def reset_providers():
    """Reset all providers (for testing)."""
    global _embedding_provider, _reranker_provider, _model_manager
    _embedding_provider = None
    _reranker_provider = None
    _model_manager = None



def switch_reranker_device(new_device: str):
    """
    Switch reranker to new device (e.g., 'cuda:1', 'cpu').
    
    Args:
        new_device: Target device
    """
    global _reranker_provider
    if _reranker_provider and hasattr(_reranker_provider, "move_to_device"):
        _reranker_provider.move_to_device(new_device)
        logger.info(f"Model Manager: Reranker switched to {new_device}")
    else:
        logger.warning("Model Manager: Cannot switch device (Provider not initialized or incapable)")


# ============================================================================
# ModelManager Facade
# ============================================================================

_model_manager = None


class ModelManager:
    """Convenience facade over embedding + reranker providers.

    Exposes ``embed_single`` / ``embed_batch`` / ``rerank_single`` so
    kernel engines can call a consistent API without worrying about
    the underlying provider topology.  Lazy-initialises providers on
    first use.
    """

    def __init__(self) -> None:
        self._embedding = None
        self._reranker = None

    # -- lazy accessors ---------------------------------------------------

    def _get_embedding(self):
        if self._embedding is None:
            self._embedding = get_embedding_provider()
        return self._embedding

    def _get_reranker(self):
        if self._reranker is None:
            try:
                self._reranker = get_reranker_provider()
            except Exception as exc:
                logger.warning(
                    "ModelManager: Reranker unavailable",
                    extra={"error": str(exc)},
                )
                self._reranker = None
        return self._reranker

    # -- public API -------------------------------------------------------

    async def embed_single(self, text: str) -> list[float]:
        """Embed a single text string and return its vector."""
        provider = self._get_embedding()
        return await provider.embed_query(text)

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of texts and return their vectors."""
        provider = self._get_embedding()
        return await provider.embed(texts)

    async def rerank_single(self, query: str, document: str) -> float:
        """Score a single query-document pair via the reranker.

        Returns a relevance score in roughly [0, 1].  Falls back to
        0.5 if the reranker is unavailable.
        """
        reranker = self._get_reranker()
        if reranker is None:
            return 0.5

        results = await reranker.rerank(query, [document], top_k=1)
        if results:
            return float(results[0].score)
        return 0.5

    @property
    def dimension(self) -> int:
        """Return the embedding dimension from the underlying provider."""
        return self._get_embedding().dimension


def get_model_manager() -> ModelManager:
    """Return the singleton ModelManager instance."""
    global _model_manager
    if _model_manager is None:
        _model_manager = ModelManager()
        logger.info("ModelManager facade initialised")
    return _model_manager
