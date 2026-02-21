"""
Database Connection Management.

Production-ready PostgreSQL connection pool with health checks.
"""

from __future__ import annotations

import os
import asyncio
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any, AsyncIterator

from shared.logging.main import get_logger
from shared.environment import get_environment_config


logger = get_logger(__name__)


@dataclass
class DatabaseConfig:
    """Database configuration."""
    url: str
    min_connections: int = 5
    max_connections: int = 20
    connection_timeout: float = 30.0
    idle_timeout: float = 300.0
    
    @classmethod
    def from_environment(cls) -> "DatabaseConfig":
        """Create config from centralized settings."""
        from shared.config import get_settings
        settings = get_settings()
        db_settings = settings.database
        
        url = db_settings.url
        
        if not url:
            logger.warning("DATABASE_URL not set in centralized settings. Database features will be unavailable.")
        
        return cls(
            url=url or "",
            min_connections=db_settings.min_connections,
            max_connections=db_settings.max_connections,
            connection_timeout=db_settings.connection_timeout,
            idle_timeout=db_settings.idle_timeout,
        )


class DatabasePool:
    """
    Async database connection pool.
    
    Supports:
    - PostgreSQL (asyncpg) ONLY
    """
    
    def __init__(self, config: DatabaseConfig = None):
        self.config = config or DatabaseConfig.from_environment()
        self._pool = None
        self._is_initialized = False
    
    async def initialize(self):
        """Initialize connection pool."""
        if self._is_initialized:
            return
        
        if not self.config.url:
            raise ValueError("Cannot initialize DatabasePool: DATABASE_URL is missing")
            
        await self._init_postgres()
        self._is_initialized = True
    
    async def _init_postgres(self):
        """Initialize PostgreSQL pool."""
        try:
            import asyncpg
            
            self._pool = await asyncpg.create_pool(
                self.config.url,
                min_size=self.config.min_connections,
                max_size=self.config.max_connections,
                timeout=self.config.connection_timeout,
                command_timeout=60.0,
            )
            
            logger.info(f"PostgreSQL pool initialized: {self.config.min_connections}-{self.config.max_connections} connections")
            
        except Exception as e:
            logger.error(f"PostgreSQL connection failed: {e}")
            raise
    
    async def close(self):
        """Close connection pool."""
        if self._pool:
            await self._pool.close()
            logger.info("Database pool closed")
        self._is_initialized = False
    
    @asynccontextmanager
    async def acquire(self) -> AsyncIterator[Any]:
        """Acquire database connection."""
        if not self._is_initialized:
            await self.initialize()
        
        async with self._pool.acquire() as conn:
            yield conn
    
    async def execute(self, query: str, *args) -> Any:
        """Execute query."""
        async with self.acquire() as conn:
            return await conn.execute(query, *args)
    
    async def fetch(self, query: str, *args) -> list:
        """Fetch all rows."""
        async with self.acquire() as conn:
            return await conn.fetch(query, *args)
    
    async def fetchrow(self, query: str, *args) -> Any:
        """Fetch single row."""
        async with self.acquire() as conn:
            return await conn.fetchrow(query, *args)
    
    async def health_check(self) -> dict:
        """Check database health."""
        try:
            if not self._is_initialized:
                # Don't auto-init if no URL to avoid noise
                if not self.config.url:
                     return {"status": "unhealthy", "error": "DATABASE_URL missing"}
                await self.initialize()
            
            async with self.acquire() as conn:
                result = await conn.fetchval("SELECT 1")
                pool_size = self._pool.get_size()
                pool_free = self._pool.get_idle_size()
            
            return {
                "status": "healthy",
                "type": "postgresql",
                "pool_size": pool_size,
                "pool_free": pool_free,
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
            }



# ============================================================================
# Singleton (Per Loop)
# ============================================================================

_loop_pools: dict[asyncio.AbstractEventLoop, DatabasePool] = {}

async def get_database_pool() -> DatabasePool:
    """Get database pool for the current event loop."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # Should not happen in async context
        return None
        
    if loop not in _loop_pools:
        # Create new pool for this loop
        pool = DatabasePool()
        if pool.config.url:
            await pool.initialize()
        _loop_pools[loop] = pool
        
    return _loop_pools[loop]


async def close_database_pool():
    """Close pool for current loop."""
    try:
        loop = asyncio.get_running_loop()
        if loop in _loop_pools:
            await _loop_pools[loop].close()
            del _loop_pools[loop]
    except RuntimeError:
        pass

# Compatibility Alias
get_db_pool = get_database_pool
