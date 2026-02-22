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
    
    # Parallelism (Default values from centralized settings)
    # Parallelism
    max_parallel_scrapers: int | None = None
    max_parallel_llm_calls: int | None = None
    max_parallel_db_writers: int | None = None
    max_parallel_embedders: int | None = None
    
    # Batch sizes
    batch_size: int | None = None
    chunk_size_mb: int | None = None
    
    # GPU
    use_gpu_embedding: bool = False
    embedding_device: str = "cpu"
    
    # Timeouts
    # Timeouts
    scraper_timeout_seconds: int | None = None
    llm_timeout_seconds: int | None = None
    
    # Memory management
    checkpoint_every_items: int | None = None
    max_memory_percent: float | None = None

    def __post_init__(self):
        """Initialize with centralized settings for any missing values."""
        from shared.config import get_settings
        settings = get_settings().hardware
        
        self.max_parallel_scrapers = self.max_parallel_scrapers if self.max_parallel_scrapers is not None else settings.max_parallel_scrapers
        self.max_parallel_llm_calls = self.max_parallel_llm_calls if self.max_parallel_llm_calls is not None else settings.max_parallel_llm_calls
        self.max_parallel_db_writers = self.max_parallel_db_writers if self.max_parallel_db_writers is not None else settings.max_parallel_db_writers
        self.max_parallel_embedders = self.max_parallel_embedders if self.max_parallel_embedders is not None else settings.max_parallel_embedders
        
        self.batch_size = self.batch_size if self.batch_size is not None else settings.batch_size
        self.chunk_size_mb = self.chunk_size_mb if self.chunk_size_mb is not None else settings.chunk_size_mb
        
        self.scraper_timeout_seconds = self.scraper_timeout_seconds if self.scraper_timeout_seconds is not None else settings.scraper_timeout_seconds
        self.llm_timeout_seconds = self.llm_timeout_seconds if self.llm_timeout_seconds is not None else settings.llm_timeout_seconds
        
        self.checkpoint_every_items = self.checkpoint_every_items if self.checkpoint_every_items is not None else settings.checkpoint_every_items
        self.max_memory_percent = self.max_memory_percent if self.max_memory_percent is not None else settings.max_memory_percent


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
    
    from shared.config import get_settings
    settings = get_settings().hardware
    
    # Scrapers: Network-bound, can have more
    config.max_parallel_scrapers = min(
        profile.optimal_workers() * settings.scraper_worker_multiplier,
        settings.kaggle_scraper_limit if profile.environment == "kaggle" else settings.default_scraper_limit
    )
    
    # LLM calls: API rate-limited
    if profile.environment == "colab":
        config.max_parallel_llm_calls = settings.colab_llm_limit
    elif profile.environment == "kaggle":
        config.max_parallel_llm_calls = settings.kaggle_llm_limit
    else:
        config.max_parallel_llm_calls = min(profile.optimal_workers(), settings.max_llm_limit)
    
    # DB writers: Disk-bound
    config.max_parallel_db_writers = max(1, profile.optimal_workers() // settings.db_writer_worker_divisor)
    
    # Embedders: GPU or CPU heavy
    if profile.can_use_gpu_embedding():
        config.max_parallel_embedders = settings.gpu_embedder_limit
        config.use_gpu_embedding = True
        config.embedding_device = "cuda"
    else:
        config.max_parallel_embedders = settings.cpu_embedder_limit
        config.use_gpu_embedding = False
        config.embedding_device = "cpu"
    
    # === Batch sizes ===
    
    config.batch_size = profile.optimal_batch_size()
    
    # Chunk size for streaming
    if profile.ram_available_gb >= settings.high_ram_threshold_gb:
        config.chunk_size_mb = settings.high_ram_chunk_mb
    elif profile.ram_available_gb >= settings.med_ram_threshold_gb:
        config.chunk_size_mb = settings.med_ram_chunk_mb
    else:
        config.chunk_size_mb = settings.low_ram_chunk_mb
    
    # === Timeouts ===
    
    # Constrained environments need longer timeouts
    if profile.is_constrained():
        config.scraper_timeout_seconds = settings.constrained_scraper_timeout
        config.llm_timeout_seconds = settings.constrained_llm_timeout
    
    # === Memory management ===
    
    if profile.environment in ("colab", "kaggle"):
        config.max_memory_percent = settings.notebook_max_memory_percent
        config.checkpoint_every_items = settings.notebook_checkpoint_items
    else:
        config.max_memory_percent = settings.default_max_memory_percent
        config.checkpoint_every_items = settings.default_checkpoint_items
    
    logger.info(
        f"Executor config: "
        f"scrapers={config.max_parallel_scrapers}, "
        f"llm={config.max_parallel_llm_calls}, "
        f"batch={config.batch_size}, "
        f"gpu_embed={config.use_gpu_embedding}"
    )
    
    return config
