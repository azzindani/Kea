"""
Storage Abstraction Package.

Provides:
- Local file storage
- HuggingFace Hub sync
"""

from .hf_sync import (
    HuggingFaceSync,
    HFConfig,
    get_hf_sync,
)

__all__ = [
    "HuggingFaceSync",
    "HFConfig",
    "get_hf_sync",
]
