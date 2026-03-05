"""
GPU Isolation Lock.

Provides a global singleton lock to ensure that multiple models/services 
on the same CPU/GPU do not execute CUDA kernels concurrently in ways 
that trigger illegal memory access or context conflicts.
"""

from __future__ import annotations
import threading
import asyncio

# Global Module Lock for the singleton itself
_SINGLETON_LOCK = threading.Lock()
_GLOBAL_GPU_LOCK: threading.Lock | None = None

def get_gpu_inference_lock() -> threading.Lock:
    """Get the global threading lock for GPU inference serialization."""
    global _GLOBAL_GPU_LOCK
    if _GLOBAL_GPU_LOCK is None:
        with _SINGLETON_LOCK:
            if _GLOBAL_GPU_LOCK is None:
                _GLOBAL_GPU_LOCK = threading.Lock()
    return _GLOBAL_GPU_LOCK

# Async wrapper if needed
_GLOBAL_ASYNC_GPU_LOCK: asyncio.Lock | None = None

async def get_async_gpu_lock() -> asyncio.Lock:
    """Get the global async lock for GPU inference serialization."""
    global _GLOBAL_ASYNC_GPU_LOCK
    if _GLOBAL_ASYNC_GPU_LOCK is None:
        # Note: asyncio.Lock must be created in the running loop
        _GLOBAL_ASYNC_GPU_LOCK = asyncio.Lock()
    return _GLOBAL_ASYNC_GPU_LOCK
