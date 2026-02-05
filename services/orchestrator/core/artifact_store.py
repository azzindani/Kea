"""
Artifact Store Module.

Moved from assembler.py to avoid circular imports.
"""

from __future__ import annotations

import re
from collections import defaultdict
from typing import Any

from shared.logging import get_logger
from shared.context_pool import TaskContextPool

logger = get_logger(__name__)


# ============================================================================
# Artifact Store
# ============================================================================

class ArtifactStore:
    """
    Job-scoped artifact storage for node outputs.
    
    Wraps TaskContextPool to provide typed artifact access with the
    `{{step_id.artifacts.key}}` convention.
    
    Example:
        store = ArtifactStore(context_pool)
        store.store("fetch_data", "prices_csv", "/vault/bbca.csv")
        path = store.get("fetch_data.artifacts.prices_csv")  # -> "/vault/bbca.csv"
    """
    
    def __init__(self, context_pool: TaskContextPool | None = None):
        self._pool = context_pool
        self._artifacts: dict[str, dict[str, Any]] = defaultdict(dict)
        
    def store(self, step_id: str, key: str, value: Any) -> None:
        """Store an artifact from a completed step."""
        self._artifacts[step_id][key] = value
        
        # Also store in TaskContextPool if available
        if self._pool:
            storage_key = f"{step_id}.artifacts.{key}"
            self._pool.store_data(storage_key, value, f"Artifact from {step_id}")
            
        logger.info(f"📦 Stored artifact: {step_id}.artifacts.{key} = {str(value)[:100]}")
        
    def get(self, reference: str) -> Any | None:
        """
        Get an artifact by reference string.

        Args:
            reference: Reference in format "step_id.artifacts.key" or just "step_id.key"

        Returns:
            The artifact value, or None if not found
        """
        # Parse reference: "step_id.artifacts.key" or "step_id.key"
        parts = reference.split(".")

        if len(parts) >= 3 and parts[1] == "artifacts":
            step_id = parts[0]
            key = ".".join(parts[2:])
        elif len(parts) >= 2:
            step_id = parts[0]
            key = ".".join(parts[1:])
        else:
            logger.warning(f"Invalid artifact reference: {reference}")
            return None

        # Try local store first
        if step_id in self._artifacts and key in self._artifacts[step_id]:
            return self._artifacts[step_id][key]

        # Fallback: If key is a generic term like "artifact", resolve to the
        # step's stored artifact(s). This handles LLM-generated references like
        # "s1.artifact" when the actual stored key is "income_annual".
        if step_id in self._artifacts and key in ("artifact", "output", "result", "data"):
            step_artifacts = self._artifacts[step_id]
            if len(step_artifacts) == 1:
                resolved_key = next(iter(step_artifacts))
                logger.info(
                    f"🔗 Auto-resolved generic ref '{reference}' -> "
                    f"'{step_id}.artifacts.{resolved_key}'"
                )
                return step_artifacts[resolved_key]
            elif len(step_artifacts) > 1:
                # Multiple artifacts: return the first one and warn
                resolved_key = next(iter(step_artifacts))
                logger.warning(
                    f"⚠️ Ambiguous generic ref '{reference}' resolved to first "
                    f"artifact '{resolved_key}' (step has {len(step_artifacts)} artifacts)"
                )
                return step_artifacts[resolved_key]

        # Try TaskContextPool
        if self._pool:
            return self._pool.get_data(reference)

        return None
        
    def list_artifacts(self, step_id: str | None = None) -> dict[str, dict[str, Any]]:
        """List all artifacts, optionally filtered by step_id."""
        if step_id:
            return {step_id: self._artifacts.get(step_id, {})}
        return dict(self._artifacts)
        
    def has_artifact(self, step_id: str, key: str) -> bool:
        """Check if an artifact exists."""
        return step_id in self._artifacts and key in self._artifacts[step_id]
