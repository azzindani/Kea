"""
Episodic Memory System.

Provides long-term recall of past sessions, learnings, and outcomes.
Connects to the Vault Service for vector storage and retrieval.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import httpx

from shared.logging import get_logger
from shared.service_registry import ServiceName, ServiceRegistry

logger = get_logger(__name__)


@dataclass
class Episode:
    """A single unit of episodic memory (one task/session)."""
    
    query: str
    outcome: str
    confidence: float = 0.0
    # Metadata
    job_id: str = ""
    domain: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    # Granular facts
    facts: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "outcome": self.outcome,
            "confidence": self.confidence,
            "job_id": self.job_id,
            "domain": self.domain,
            "created_at": self.created_at.isoformat(),
            "facts": self.facts,
        }


class EpisodicMemory:
    """
    Interface to the Vault Service for long-term episodic recall.
    """

    def __init__(self) -> None:
        self.enabled = True
        self._vault_url = ServiceRegistry.get_url(ServiceName.VAULT)

    async def search(
        self,
        query: str,
        limit: int = 3,
        domain: str | None = None,
    ) -> list[Episode]:
        """
        Recall similar past episodes based on semantic similarity.
        """
        if not self.enabled:
            return []

        try:
            params = {"q": query, "limit": limit}
            if domain:
                params["domain"] = domain

            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(
                    f"{self._vault_url}/research/query",
                    params=params,
                )
                
                if resp.status_code != 200:
                    logger.warning(
                        f"Episodic recall failed: Vault returned {resp.status_code}"
                    )
                    return []

                data = resp.json()
                results = []
                
                # Vault returns a flat list of 'facts' (chunks).
                # ideally we want grouped episodes, but for now we unwrap facts.
                # The Vault API seems to return 'facts' which are document chunks.
                
                for item in data.get("facts", []):
                    # Construct pseudo-episode from finding
                    meta = item.get("metadata", {})
                    results.append(Episode(
                        query=meta.get("query", ""),
                        outcome=item.get("text", ""),
                        confidence=item.get("confidence", 0.0),
                        job_id=meta.get("job_id", ""),
                        domain=meta.get("domain", ""),
                    ))
                
                return results

        except Exception as e:
            logger.warning(f"Episodic recall error: {e}")
            return []

    async def store_episode(self, episode: Episode) -> bool:
        """
        Commit a completed episode to long-term memory.
        """
        if not self.enabled:
            return False

        try:
            payload = {
                "query": episode.query,
                "job_id": episode.job_id,
                "content": episode.outcome,
                "confidence": episode.confidence,
                "facts": episode.facts,
                # Domain is not explicitly supported in /research/sessions payload schema
                # but might be in metadata if we extend it. 
                # For now, simplistic mapping.
            }

            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.post(
                    f"{self._vault_url}/research/sessions",
                    json=payload,
                )
                
                if resp.status_code in (200, 201):
                    logger.info(f"Stored episode {episode.job_id} to Vault")
                    return True
                else:
                    logger.warning(
                        f"Failed to store episode: Vault returned {resp.status_code}"
                    )
                    return False

        except Exception as e:
            logger.warning(f"Episodic store error: {e}")
            return False
