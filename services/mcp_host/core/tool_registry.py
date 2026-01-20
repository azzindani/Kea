"""
Persistent Tool Registry.

Manages a scalable catalog of MCP tools using PostgreSQL and pgvector.
"""
from __future__ import annotations

import os
from typing import Any, List, Dict

from shared.logging import get_logger
from services.mcp_host.core.postgres_registry import PostgresToolRegistry

logger = get_logger(__name__)


_registry_instance = None

async def get_tool_registry() -> PostgresToolRegistry:
    """Get singleton tool registry (Postgres Only)."""
    global _registry_instance
    
    if _registry_instance is None:
        if not os.getenv("DATABASE_URL"):
            raise ValueError("DATABASE_URL is required for Tool Registry")
            
        try:
            _registry_instance = PostgresToolRegistry()
            logger.info("ToolRegistry initialized (Postgres)")
        except Exception as e:
            logger.error(f"Failed to initialize ToolRegistry: {e}")
            raise

    return _registry_instance

