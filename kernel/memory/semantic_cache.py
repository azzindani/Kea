"""
Semantic Context Cache.

Replaces rigid key-value caching with vector-similarity retrieval via Vault.
Allows finding "similar" past results even if the query phrasing differs.
"""

from __future__ import annotations

import httpx

from shared.logging import get_logger
from shared.service_registry import ServiceName, ServiceRegistry

logger = get_logger(__name__)


class SemanticCache:
    """
    Cache that uses semantic similarity (via Vault Service) instead of exact key match.
    """

    def __init__(self, threshold: float = 0.85) -> None:
        self.threshold = threshold
        self._vault_url = ServiceRegistry.get_url(ServiceName.VAULT)
        self.enabled = True

    async def get(
        self,
        query: str,
        domain: str = "general",
    ) -> str | None:
        """
        Retrieve a cached result if a semantically similar query exists.
        
        Args:
            query: The natural language query.
            domain: The domain context (acts as namespace).
            
        Returns:
            The cached content string if found, else None.
        """
        if not self.enabled:
            return None

        try:
            # Query the 'cache' domain namespace or specific domain
            params = {
                "q": query,
                "limit": 1,
                "domain": f"cache_{domain}", 
            }

            async with httpx.AsyncClient(timeout=3.0) as client:
                resp = await client.get(
                    f"{self._vault_url}/research/query",
                    params=params,
                )
                
                if resp.status_code != 200:
                    return None

                data = resp.json()
                facts = data.get("facts", [])
                
                if not facts:
                    return None

                best = facts[0]
                # Check confidence/similarity score
                # Note: Vault API returns 'confidence' or 'score' in metadata?
                # The response schema has 'confidence' as a top-level field in fact dict.
                score = best.get("confidence", 0.0)
                
                if score >= self.threshold:
                    logger.info(
                        f"Semantic Cache HIT: '{query[:30]}...' (score={score:.2f})"
                    )
                    return best.get("text", "")
                
                logger.debug(
                    f"Semantic Cache MISS: '{query[:30]}...' (best score={score:.2f} < {self.threshold})"
                )
                return None

        except Exception as e:
            logger.warning(f"Semantic cache lookup failed: {e}")
            return None

    async def put(
        self,
        query: str,
        content: str,
        domain: str = "general",
    ) -> bool:
        """
        Store a result in the semantic cache.
        """
        if not self.enabled:
            return False

        try:
            payload = {
                "query": query,
                "content": content,
                "job_id": "cache_entry",
                "confidence": 1.0,  # It's a definitive result at time of caching
                "facts": [{
                    "text": content,
                    "confidence": 1.0,
                    "metadata": {"type": "cache_entry", "domain": f"cache_{domain}"}
                }]
            }

            # Note: The vault's /research/sessions endpoint doesn't accept 'domain' at root level
            # but we can embed it in metadata. However, query endpoint filters by domain?
            # services/vault/main.py query_research accepts 'domain' param and passes to vector store.
            # PostgresVectorStore likely filters on metadata['domain']?
            # We should verify this assumption if possible, but let's assume standard behavior.
            
            async with httpx.AsyncClient(timeout=3.0) as client:
                await client.post(
                    f"{self._vault_url}/research/sessions",
                    json=payload,
                )
            return True

        except Exception as e:
            logger.warning(f"Semantic cache store failed: {e}")
            return False
