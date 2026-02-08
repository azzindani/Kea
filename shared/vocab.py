"""
Vocabulary Loader.

Loads YAML configuration files from configs/vocab/ to replace hardcoded keywords.
"""

from __future__ import annotations

import yaml
from functools import lru_cache
from pathlib import Path
from typing import Any

from shared.logging import get_logger

logger = get_logger(__name__)

# Base directory for vocabulary files
VOCAB_DIR = Path("configs/vocab")


@lru_cache()
def load_vocab(name: str) -> dict[str, Any]:
    """
    Load a vocabulary file by name (without extension).
    
    Args:
        name: Filename without .yaml extension (e.g. 'query_classifier')
        
    Returns:
        Dictionary containing the vocabulary data.
        Returns empty dict if file not found or invalid.
    """
    file_path = VOCAB_DIR / f"{name}.yaml"
    
    if not file_path.exists():
        logger.warning(f"Vocab file not found: {file_path}")
        return {}
        
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            return data or {}
    except Exception as e:
        logger.error(f"Failed to load vocab {name}: {e}")
        return {}


def get_vocab_list(vocab_name: str, key: str, default: list[str] = None) -> list[str]:
    """
    Helper to get a list from a vocab file.
    
    Args:
        vocab_name: Name of the vocab file
        key: Key path in dot notation (e.g. 'patterns.casual') or simple key
        default: Default list if not found
        
    Returns:
        List of strings
    """
    data = load_vocab(vocab_name)
    
    # Handle dot notation for nested keys
    if "." in key:
        parts = key.split(".")
        current = data
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            else:
                return default or []
        
        if isinstance(current, list):
            return current
        return default or []
        
    val = data.get(key)
    if isinstance(val, list):
        return val
        
    return default or []
