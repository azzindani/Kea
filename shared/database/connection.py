"""
Database Connection Management.

Production-ready PostgreSQL connection pool with health checks.
Falls back to SQLite for development/testing.
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any, AsyncIterator

from shared.logging import get_logger
from shared.environment import get_environment_config


logger = get_logger(__name__)


@dataclass
class DatabaseConfig:
    """Database configuration."""
    url: str
    min_connections: int = 2
    max_connections: int = 10
    connection_timeout: float = 30.0
    idle_timeout: float = 300.0
    
    @classmethod
    def from_environment(cls) -> "DatabaseConfig":
        """Create config from environment."""
        env_config = get_environment_config()
        
        url = os.getenv("DATABASE_URL", "")
        
        if env_config.is_production:
            return cls(
                url=url,
                min_connections=5,
                max_connections=20,
                connection_timeout=10.0,
                idle_timeout=600.0,
            )
        else:
            return cls(
                url=url or "sqlite:///data/dev.db",
                min_connections=1,
                max_connections=5,
                connection_timeout=30.0,
                idle_timeout=300.0,
            )


class DatabasePool:
    """
    Async database connection pool.
    
    Supports:
    - PostgreSQL (asyncpg)
    - SQLite fallback (aiosqlite)
    """
    
    def __init__(self, config: DatabaseConfig = None):
        self.config = config or DatabaseConfig.from_environment()
        self._pool = None
        self._is_postgres = "postgres" in self.config.url
        self._is_initialized = False
    
    async def initialize(self):
        """Initialize connection pool."""
        if self._is_initialized:
            return
        
        if self._is_postgres:
            await self._init_postgres()
        else:
            await self._init_sqlite()
        
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
            
        except ImportError:
            logger.error("asyncpg not installed, falling back to SQLite")
            self._is_postgres = False
            await self._init_sqlite()
        except Exception as e:
            logger.error(f"PostgreSQL connection failed: {e}")
            raise
    
    async def _init_sqlite(self):
        """Initialize SQLite (for development)."""
        import os
        
        # Extract path from URL
        path = self.config.url.replace("sqlite:///", "")
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        
        logger.info(f"SQLite initialized: {path}")
    
    async def close(self):
        """Close connection pool."""
        if self._pool and self._is_postgres:
            await self._pool.close()
            logger.info("Database pool closed")
        self._is_initialized = False
    
    @asynccontextmanager
    async def acquire(self) -> AsyncIterator[Any]:
        """Acquire database connection."""
        if not self._is_initialized:
            await self.initialize()
        
        if self._is_postgres:
            async with self._pool.acquire() as conn:
                yield conn
        else:
            import aiosqlite
            path = self.config.url.replace("sqlite:///", "")
            async with aiosqlite.connect(path) as conn:
                conn.row_factory = aiosqlite.Row
                yield conn
    
    async def execute(self, query: str, *args) -> Any:
        """Execute query."""
        async with self.acquire() as conn:
            if self._is_postgres:
                return await conn.execute(query, *args)
            else:
                await conn.execute(query, args)
                await conn.commit()
    
    async def fetch(self, query: str, *args) -> list:
        """Fetch all rows."""
        async with self.acquire() as conn:
            if self._is_postgres:
                return await conn.fetch(query, *args)
            else:
                async with conn.execute(query, args) as cursor:
                    return await cursor.fetchall()
    
    async def fetchrow(self, query: str, *args) -> Any:
        """Fetch single row."""
        async with self.acquire() as conn:
            if self._is_postgres:
                return await conn.fetchrow(query, *args)
            else:
                async with conn.execute(query, args) as cursor:
                    return await cursor.fetchone()
    
    async def health_check(self) -> dict:
        """Check database health."""
        try:
            if not self._is_initialized:
                await self.initialize()
            
            async with self.acquire() as conn:
                if self._is_postgres:
                    result = await conn.fetchval("SELECT 1")
                    pool_size = self._pool.get_size()
                    pool_free = self._pool.get_idle_size()
                else:
                    async with conn.execute("SELECT 1") as cursor:
                        result = await cursor.fetchone()
                    pool_size = 1
                    pool_free = 1
            
            return {
                "status": "healthy",
                "type": "postgresql" if self._is_postgres else "sqlite",
                "pool_size": pool_size,
                "pool_free": pool_free,
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
            }


# ============================================================================
# Singleton
# ============================================================================

_database_pool: DatabasePool | None = None


async def get_database_pool() -> DatabasePool:
    """Get singleton database pool."""
    global _database_pool
    if _database_pool is None:
        _database_pool = DatabasePool()
        await _database_pool.initialize()
    return _database_pool


async def close_database_pool():
    """Close database pool."""
    global _database_pool
    if _database_pool:
        await _database_pool.close()
        _database_pool = None
