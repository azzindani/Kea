"""
ML Inference Service — Model Pool.

Singleton manager for embedding and reranker model lifecycle.
Wraps existing shared/embedding providers and manages device assignment,
lazy loading, and health monitoring.

This is the ONLY module in the system that loads PyTorch/Transformers models.
All other services access models via the HTTP API.
"""

from __future__ import annotations

import asyncio
from enum import Enum
from typing import Any

from shared.config import get_settings
from shared.hardware.detector import detect_hardware
from shared.logging.main import get_logger

logger = get_logger(__name__)


class ModelRole(str, Enum):
    """Configurable roles for the ML Inference service."""
    EMBEDDING = "embedding"
    RERANKER = "reranker"
    BOTH = "both"


class ModelPool:
    """
    Singleton pool for embedding and reranker models.

    Manages lazy loading of models based on the configured role and
    detected hardware. Each instance of this class should map to
    exactly one GPU (or CPU) — never share GPUs between processes.
    """

    def __init__(self) -> None:
        self._settings = get_settings()
        self._role = ModelRole(self._settings.ml_inference.role)
        self._device: str = ""
        self._emb_device: str = ""
        self._rerank_device: str = ""
        self._embedding_provider: Any | None = None
        self._reranker_provider: Any | None = None
        self._vl_embedding_provider: Any | None = None
        self._vl_reranker_provider: Any | None = None
        self._loaded = False
        self._load_lock: asyncio.Lock | None = None

    def _get_load_lock(self) -> asyncio.Lock:
        """Get or create the initialization lock, ensuring it's bound to the current loop."""
        if self._load_lock is None:
            self._load_lock = asyncio.Lock()
        return self._load_lock

    @property
    def role(self) -> ModelRole:
        return self._role

    @property
    def device(self) -> str:
        return self._device

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    def _resolve_device(self) -> str:
        """Resolve the compute device from config or hardware detection."""
        configured = self._settings.ml_inference.device
        if configured != "auto":
            logger.info(f"Using configured device: {configured}")
            return configured

        # Auto-detect via hardware detector
        hw = detect_hardware()
        if hw.can_use_gpu_embedding():
            device = "cuda"
            gpu_label = hw.gpu_names[0] if hw.gpu_names else "Unknown"
            logger.info(
                f"Auto-detected GPU: {gpu_label}, "
                f"VRAM: {hw.vram_total_gb:.1f} GB — using {device}"
            )
        else:
            device = "cpu"
            logger.info(
                f"No compatible GPU detected — using {device}. "
                f"Performance will be reduced."
            )
        return device

    async def load_models(self) -> None:
        """
        Load models based on the configured role.

        Thread-safe via async lock. Idempotent — safe to call multiple times.
        """
        async with self._get_load_lock():
            if self._loaded:
                return

            self._device = self._resolve_device()
            role = self._role
            
            self._emb_device = self._device
            self._rerank_device = self._device
            
            # If "both" models are loaded into a single service, natively split them to free GPUs
            if role == ModelRole.BOTH and self._device == "cuda":
                hw = detect_hardware()
                if hw.gpu_count > 1:
                    self._emb_device = "cuda:0"
                    self._rerank_device = "cuda:1"
                    logger.info("Multi-GPU detected! Auto-distributing embedding (cuda:0) and reranker (cuda:1).")

            logger.info(
                f"Model pool initializing: role={role.value}, device={self._device}"
            )

            # Load embedding model
            if role in (ModelRole.EMBEDDING, ModelRole.BOTH):
                await self._load_embedding()

            # Load reranker model
            if role in (ModelRole.RERANKER, ModelRole.BOTH):
                await self._load_reranker()

            # Optionally load VL models
            if self._settings.ml_inference.enable_vl_models:
                if role in (ModelRole.EMBEDDING, ModelRole.BOTH):
                    await self._load_vl_embedding()
                if role in (ModelRole.RERANKER, ModelRole.BOTH):
                    await self._load_vl_reranker()

            self._loaded = True
            logger.info(
                f"Model pool ready: role={role.value}, "
                f"device={self._device}, "
                f"models={self.loaded_model_count}"
            )

    async def _load_embedding(self) -> None:
        """Load the text embedding model."""
        try:
            from shared.embedding.qwen3_embedding import create_embedding_provider

            use_local = self._emb_device != "cpu" or self._settings.embedding.use_local
            self._embedding_provider = create_embedding_provider(
                use_local=use_local, 
                device=self._emb_device,
                use_flash_attention=self._settings.ml_inference.use_flash_attention
            )
            # FORCE LOAD NOW
            logger.info(f"Model Pool: Pre-loading embedding model on {self._emb_device}...")
            await self._embedding_provider.load()
            
            logger.info(
                f"Embedding model loaded: {self._settings.embedding.model_name} on {self._emb_device}"
            )
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise

    async def _load_reranker(self) -> None:
        """Load the reranker model."""
        try:
            from shared.embedding.qwen3_reranker import create_reranker_provider

            self._reranker_provider = create_reranker_provider(
                device=self._rerank_device,
                use_flash_attention=self._settings.ml_inference.use_flash_attention
            )
            # FORCE LOAD NOW
            logger.info(f"Model Pool: Pre-loading reranker model on {self._rerank_device}...")
            await self._reranker_provider.load()
            
            logger.info(
                f"Reranker model loaded: {self._settings.reranker.model_name} on {self._rerank_device}"
            )
        except Exception as e:
            logger.error(f"Failed to load reranker model: {e}")
            raise

    async def _load_vl_embedding(self) -> None:
        """Load the Vision-Language embedding model."""
        try:
            from shared.embedding.qwen3_vl_embedding import create_vl_embedding_provider

            self._vl_embedding_provider = create_vl_embedding_provider()
            logger.info(
                f"VL Embedding model loaded: {self._settings.vl_embedding.model_name}"
            )
        except Exception as e:
            logger.error(f"Failed to load VL embedding model: {e}")
            raise

    async def _load_vl_reranker(self) -> None:
        """Load the Vision-Language reranker model."""
        try:
            from shared.embedding.qwen3_vl_reranker import create_vl_reranker_provider

            self._vl_reranker_provider = create_vl_reranker_provider()
            logger.info(
                f"VL Reranker model loaded: {self._settings.vl_reranker.model_name}"
            )
        except Exception as e:
            logger.error(f"Failed to load VL reranker model: {e}")
            raise

    # -----------------------------------------------------------------------
    # Public Accessors
    # -----------------------------------------------------------------------

    def get_embedding_provider(self) -> Any:
        """Get the embedding provider. Raises if not loaded."""
        if self._embedding_provider is None:
            raise RuntimeError(
                "Embedding model not loaded. "
                f"Service role is '{self._role.value}' — "
                "ensure ML_ROLE includes 'embedding' or 'both'."
            )
        return self._embedding_provider

    def get_reranker_provider(self) -> Any:
        """Get the reranker provider. Raises if not loaded."""
        if self._reranker_provider is None:
            raise RuntimeError(
                "Reranker model not loaded. "
                f"Service role is '{self._role.value}' — "
                "ensure ML_ROLE includes 'reranker' or 'both'."
            )
        return self._reranker_provider

    def get_vl_embedding_provider(self) -> Any:
        """Get the VL embedding provider. Raises if not loaded."""
        if self._vl_embedding_provider is None:
            raise RuntimeError("VL Embedding model not loaded or not enabled.")
        return self._vl_embedding_provider

    def get_vl_reranker_provider(self) -> Any:
        """Get the VL reranker provider. Raises if not loaded."""
        if self._vl_reranker_provider is None:
            raise RuntimeError("VL Reranker model not loaded or not enabled.")
        return self._vl_reranker_provider

    @property
    def loaded_model_count(self) -> int:
        """Count of successfully loaded models."""
        count = 0
        if self._embedding_provider is not None:
            count += 1
        if self._reranker_provider is not None:
            count += 1
        if self._vl_embedding_provider is not None:
            count += 1
        if self._vl_reranker_provider is not None:
            count += 1
        return count

    @property
    def has_embedding(self) -> bool:
        return self._embedding_provider is not None

    @property
    def has_reranker(self) -> bool:
        return self._reranker_provider is not None

    @property
    def has_vl_embedding(self) -> bool:
        return self._vl_embedding_provider is not None

    @property
    def has_vl_reranker(self) -> bool:
        return self._vl_reranker_provider is not None


# ---------------------------------------------------------------------------
# Module-level Singleton
# ---------------------------------------------------------------------------

_pool: ModelPool | None = None


def get_model_pool() -> ModelPool:
    """Get the singleton ModelPool instance."""
    global _pool
    if _pool is None:
        _pool = ModelPool()
    return _pool
