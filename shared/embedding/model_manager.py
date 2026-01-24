"""
Model Manager.

Singleton manager for embedding and reranker models.
Loads models once, shares across the system.
"""

from __future__ import annotations

from shared.logging import get_logger

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
        # Or trust config. Let's trust config but maybe warning if no GPU.
        if use_local:
             from shared.hardware.detector import detect_hardware
             hw = detect_hardware()
             if not hw.can_use_gpu_embedding():
                 # Config requested local but hardware sucks? 
                 # We'll try anyway, let CPU handle it or fail gracefully.
                 logger.info("Model Manager: Using local embedding as configured (Hardware check skipped)")
    
    if _embedding_provider is None:
        from shared.embedding.qwen3_embedding import create_embedding_provider
        
        _embedding_provider = create_embedding_provider(
            use_local=use_local,
            model_name=config.embedding.model_name
        )
        logger.info(f"Model Manager: Embedding provider initialized (local={use_local})")
    
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
    global _embedding_provider, _reranker_provider
    _embedding_provider = None
    _reranker_provider = None



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
