"""
Adaptive Executor Configuration.

Auto-tune execution parameters based on hardware profile.
"""

from __future__ import annotations

from dataclasses import dataclass

from .detector import HardwareProfile, detect_hardware
from shared.logging.main import get_logger


logger = get_logger(__name__)


@dataclass
class ExecutorConfig:
    """Executor configuration based on hardware."""
    
    # Parallelism
    max_parallel_scrapers: int = 3
    max_parallel_llm_calls: int = 2
    max_parallel_db_writers: int = 2
    max_parallel_embedders: int = 1
    
    # Batch sizes
    batch_size: int = 1000
    chunk_size_mb: int = 10
    
    # GPU
    use_gpu_embedding: bool = False
    embedding_device: str = "cpu"
    
    # Timeouts
    scraper_timeout_seconds: int = 30
    llm_timeout_seconds: int = 60
    
    # Memory management
    checkpoint_every_items: int = 100
    max_memory_percent: float = 80.0


def get_optimal_config(profile: HardwareProfile | None = None) -> ExecutorConfig:
    """
    Generate optimal executor config based on hardware.
    
    Args:
        profile: Hardware profile (auto-detected if None)
        
    Returns:
        Optimized ExecutorConfig
    """
    if profile is None:
        profile = detect_hardware()
    
    config = ExecutorConfig()
    
    # === Parallelism ===
    
    # Scrapers: Network-bound, can have more
    config.max_parallel_scrapers = min(
        profile.optimal_workers() * 2,
        10 if profile.environment == "kaggle" else 5
    )
    
    # LLM calls: API rate-limited
    if profile.environment == "colab":
        config.max_parallel_llm_calls = 2  # Colab has session limits
    elif profile.environment == "kaggle":
        config.max_parallel_llm_calls = 3
    else:
        config.max_parallel_llm_calls = min(profile.optimal_workers(), 4)
    
    # DB writers: Disk-bound
    config.max_parallel_db_writers = max(1, profile.optimal_workers() // 2)
    
    # Embedders: GPU or CPU heavy
    if profile.can_use_gpu_embedding():
        config.max_parallel_embedders = 2
        config.use_gpu_embedding = True
        config.embedding_device = "cuda"
    else:
        config.max_parallel_embedders = 1
        config.use_gpu_embedding = False
        config.embedding_device = "cpu"
    
    # === Batch sizes ===
    
    config.batch_size = profile.optimal_batch_size()
    
    # Chunk size for streaming
    if profile.ram_available_gb >= 8:
        config.chunk_size_mb = 50
    elif profile.ram_available_gb >= 4:
        config.chunk_size_mb = 20
    else:
        config.chunk_size_mb = 10
    
    # === Timeouts ===
    
    # Constrained environments need longer timeouts
    if profile.is_constrained():
        config.scraper_timeout_seconds = 60
        config.llm_timeout_seconds = 120
    
    # === Memory management ===
    
    if profile.environment in ("colab", "kaggle"):
        config.max_memory_percent = 75.0  # Leave room for notebook
        config.checkpoint_every_items = 50  # More frequent checkpoints
    else:
        config.max_memory_percent = 85.0
        config.checkpoint_every_items = 100
    
    logger.info(
        f"Executor config: "
        f"scrapers={config.max_parallel_scrapers}, "
        f"llm={config.max_parallel_llm_calls}, "
        f"batch={config.batch_size}, "
        f"gpu_embed={config.use_gpu_embedding}"
    )
    
    return config
