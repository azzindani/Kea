"""
User Manager.

Manages user CRUD operations with PostgreSQL backend.
Falls back to SQLite for development/testing.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
import os

from shared.logging import get_logger
from shared.users.models import User, UserRole, APIKey, USERS_TABLE_SQL, API_KEYS_TABLE_SQL


logger = get_logger(__name__)


class UserManager:
    """
    Manages user operations.
    
    Supports:
    - PostgreSQL (production)
    - SQLite (development/fallback)
    
    Example:
        manager = UserManager()
        await manager.initialize()
        
        user = await manager.create_user("user@example.com", "John Doe")
        user = await manager.authenticate_email("user@example.com", "password")
    """
    
    def __init__(self, database_url: str = None):
        """
        Initialize manager.
        
        Args:
            database_url: PostgreSQL URL or None for SQLite fallback
        """
        self.database_url = database_url or os.getenv("DATABASE_URL")
        self._pool = None
        self._sqlite_path = "data/users.db"
        self._use_postgres = bool(self.database_url and "postgres" in self.database_url)
        
        logger.debug(f"UserManager initialized: postgres={self._use_postgres}")
    
    async def initialize(self):
        """Initialize database connection and tables."""
        if self._use_postgres:
            await self._init_postgres()
        else:
            await self._init_sqlite()
    
    async def _init_postgres(self):
        """Initialize PostgreSQL."""
        try:
            import asyncpg
            
            self._pool = await asyncpg.create_pool(self.database_url)
            
            async with self._pool.acquire() as conn:
                await conn.execute(USERS_TABLE_SQL)
                await conn.execute(API_KEYS_TABLE_SQL)
            
            logger.info("PostgreSQL initialized for users")
            
        except Exception as e:
            logger.warning(f"PostgreSQL init failed, falling back to SQLite: {e}")
            self._use_postgres = False
            await self._init_sqlite()
    
    async def _init_sqlite(self):
        """Initialize SQLite fallback."""
        import aiosqlite
        import os
        
        os.makedirs(os.path.dirname(self._sqlite_path) or ".", exist_ok=True)
        
        # Convert PostgreSQL SQL to SQLite
        sqlite_users = """
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                role TEXT DEFAULT 'user',
                tenant_id TEXT DEFAULT 'default',
                password_hash TEXT,
                email_verified INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                settings TEXT DEFAULT '{}',
                created_at TEXT,
                updated_at TEXT,
                last_login_at TEXT
            )
        """
        
        sqlite_keys = """
            CREATE TABLE IF NOT EXISTS api_keys (
                key_id TEXT PRIMARY KEY,
                user_id TEXT,
                name TEXT NOT NULL,
                key_hash TEXT NOT NULL,
                key_prefix TEXT NOT NULL,
                scopes TEXT DEFAULT 'read,write',
                rate_limit INTEGER DEFAULT 1000,
                is_active INTEGER DEFAULT 1,
                created_at TEXT,
                expires_at TEXT,
                last_used_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """
        
        async with aiosqlite.connect(self._sqlite_path) as db:
            await db.execute(sqlite_users)
            await db.execute(sqlite_keys)
            await db.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
            await db.commit()
        
        logger.info("SQLite initialized for users")
    
    # =========================================================================
    # User CRUD
    # =========================================================================
    
    async def create_user(
        self,
        email: str,
        name: str,
        password: str = "",
        role: UserRole = UserRole.USER,
        tenant_id: str = "default",
    ) -> User:
        """Create new user."""
        user = User.create(email, name, password, role, tenant_id)
        
        if self._use_postgres:
            async with self._pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO users 
                    (user_id, email, name, role, tenant_id, password_hash, 
                     email_verified, is_active, settings, created_at, updated_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                """, user.user_id, user.email, user.name, user.role.value,
                    user.tenant_id, user.password_hash, user.email_verified,
                    user.is_active, str(user.settings), user.created_at, user.updated_at)
        else:
            import aiosqlite
            import json
            
            async with aiosqlite.connect(self._sqlite_path) as db:
                await db.execute("""
                    INSERT INTO users 
                    (user_id, email, name, role, tenant_id, password_hash,
                     email_verified, is_active, settings, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (user.user_id, user.email, user.name, user.role.value,
                      user.tenant_id, user.password_hash, int(user.email_verified),
                      int(user.is_active), json.dumps(user.settings),
                      user.created_at.isoformat(), user.updated_at.isoformat()))
                await db.commit()
        
        logger.info(f"Created user: {user.user_id}")
        return user
    
    async def get_user(self, user_id: str) -> User | None:
        """Get user by ID."""
        if self._use_postgres:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT * FROM users WHERE user_id = $1", user_id
                )
                if row:
                    return self._row_to_user(dict(row))
        else:
            import aiosqlite
            
            async with aiosqlite.connect(self._sqlite_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute(
                    "SELECT * FROM users WHERE user_id = ?", (user_id,)
                ) as cursor:
                    row = await cursor.fetchone()
                    if row:
                        return self._row_to_user(dict(row))
        
        return None
    
    async def get_by_email(self, email: str) -> User | None:
        """Get user by email."""
        email = email.lower().strip()
        
        if self._use_postgres:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT * FROM users WHERE email = $1", email
                )
                if row:
                    return self._row_to_user(dict(row))
        else:
            import aiosqlite
            
            async with aiosqlite.connect(self._sqlite_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute(
                    "SELECT * FROM users WHERE email = ?", (email,)
                ) as cursor:
                    row = await cursor.fetchone()
                    if row:
                        return self._row_to_user(dict(row))
        
        return None
    
    async def authenticate_email(self, email: str, password: str) -> User | None:
        """Authenticate user by email and password."""
        user = await self.get_by_email(email)
        
        if user and user.is_active and user.verify_password(password):
            user.last_login_at = datetime.utcnow()
            await self.update_user(user.user_id, last_login_at=user.last_login_at)
            return user
        
        return None
    
    async def update_user(self, user_id: str, **updates) -> bool:
        """Update user fields."""
        if not updates:
            return False
        
        updates["updated_at"] = datetime.utcnow()
        
        if self._use_postgres:
            set_clause = ", ".join(f"{k} = ${i+2}" for i, k in enumerate(updates.keys()))
            values = [user_id] + [
                v.isoformat() if isinstance(v, datetime) else v
                for v in updates.values()
            ]
            
            async with self._pool.acquire() as conn:
                await conn.execute(
                    f"UPDATE users SET {set_clause} WHERE user_id = $1",
                    *values
                )
        else:
            import aiosqlite
            
            set_clause = ", ".join(f"{k} = ?" for k in updates.keys())
            values = [
                v.isoformat() if isinstance(v, datetime) else v
                for v in updates.values()
            ] + [user_id]
            
            async with aiosqlite.connect(self._sqlite_path) as db:
                await db.execute(
                    f"UPDATE users SET {set_clause} WHERE user_id = ?",
                    values
                )
                await db.commit()
        
        return True
    
    async def delete_user(self, user_id: str) -> bool:
        """Delete user."""
        if self._use_postgres:
            async with self._pool.acquire() as conn:
                await conn.execute("DELETE FROM users WHERE user_id = $1", user_id)
        else:
            import aiosqlite
            
            async with aiosqlite.connect(self._sqlite_path) as db:
                await db.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
                await db.commit()
        
        logger.info(f"Deleted user: {user_id}")
        return True
    
    async def list_users(
        self,
        tenant_id: str = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[User]:
        """List users."""
        users = []
        
        if self._use_postgres:
            async with self._pool.acquire() as conn:
                if tenant_id:
                    rows = await conn.fetch(
                        "SELECT * FROM users WHERE tenant_id = $1 LIMIT $2 OFFSET $3",
                        tenant_id, limit, offset
                    )
                else:
                    rows = await conn.fetch(
                        "SELECT * FROM users LIMIT $1 OFFSET $2",
                        limit, offset
                    )
                users = [self._row_to_user(dict(r)) for r in rows]
        else:
            import aiosqlite
            
            async with aiosqlite.connect(self._sqlite_path) as db:
                db.row_factory = aiosqlite.Row
                if tenant_id:
                    sql = "SELECT * FROM users WHERE tenant_id = ? LIMIT ? OFFSET ?"
                    params = (tenant_id, limit, offset)
                else:
                    sql = "SELECT * FROM users LIMIT ? OFFSET ?"
                    params = (limit, offset)
                
                async with db.execute(sql, params) as cursor:
                    rows = await cursor.fetchall()
                    users = [self._row_to_user(dict(r)) for r in rows]
        
        return users
    
    def _row_to_user(self, row: dict) -> User:
        """Convert database row to User."""
        import json
        
        settings = row.get("settings", "{}")
        if isinstance(settings, str):
            settings = json.loads(settings) if settings else {}
        
        return User(
            user_id=row["user_id"],
            email=row["email"],
            name=row["name"],
            role=UserRole(row.get("role", "user")),
            tenant_id=row.get("tenant_id", "default"),
            password_hash=row.get("password_hash", ""),
            email_verified=bool(row.get("email_verified", False)),
            is_active=bool(row.get("is_active", True)),
            settings=settings,
            created_at=self._parse_datetime(row.get("created_at")),
            updated_at=self._parse_datetime(row.get("updated_at")),
            last_login_at=self._parse_datetime(row.get("last_login_at")),
        )
    
    def _parse_datetime(self, value) -> datetime | None:
        """Parse datetime from various formats."""
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            return datetime.fromisoformat(value)
        return None


class APIKeyManager:
    """Manages API keys."""
    
    def __init__(self, database_url: str = None):
        self.database_url = database_url or os.getenv("DATABASE_URL")
        self._pool = None
        self._sqlite_path = "data/users.db"
        self._use_postgres = bool(self.database_url and "postgres" in self.database_url)
    
    async def initialize(self):
        """Initialize (uses same DB as UserManager)."""
        if self._use_postgres:
            try:
                import asyncpg
                self._pool = await asyncpg.create_pool(self.database_url)
            except Exception as e:
                logger.warning(f"APIKeyManager PostgreSQL failed, using SQLite: {e}")
                self._use_postgres = False
    
    async def create_key(
        self,
        user_id: str,
        name: str,
        scopes: list[str] = None,
        rate_limit: int = 1000,
        expires_at: datetime = None,
    ) -> tuple[APIKey, str]:
        """Create new API key, returns (key, raw_key)."""
        api_key, raw_key = APIKey.create(user_id, name, scopes, rate_limit, expires_at)
        
        if self._use_postgres:
            async with self._pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO api_keys 
                    (key_id, user_id, name, key_hash, key_prefix, scopes, 
                     rate_limit, is_active, created_at, expires_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                """, api_key.key_id, api_key.user_id, api_key.name,
                    api_key.key_hash, api_key.key_prefix, api_key.scopes,
                    api_key.rate_limit, api_key.is_active,
                    api_key.created_at, api_key.expires_at)
        else:
            import aiosqlite
            
            async with aiosqlite.connect(self._sqlite_path) as db:
                await db.execute("""
                    INSERT INTO api_keys 
                    (key_id, user_id, name, key_hash, key_prefix, scopes,
                     rate_limit, is_active, created_at, expires_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (api_key.key_id, api_key.user_id, api_key.name,
                      api_key.key_hash, api_key.key_prefix, ",".join(api_key.scopes),
                      api_key.rate_limit, int(api_key.is_active),
                      api_key.created_at.isoformat(),
                      api_key.expires_at.isoformat() if api_key.expires_at else None))
                await db.commit()
        
        return api_key, raw_key
    
    async def validate_key(self, raw_key: str) -> APIKey | None:
        """Validate API key and return if valid."""
        if not raw_key or not raw_key.startswith("kea_"):
            return None
        
        key_prefix = raw_key[:12]
        
        if self._use_postgres:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT * FROM api_keys WHERE key_prefix = $1 AND is_active = true",
                    key_prefix
                )
                if row and APIKey.verify(raw_key, row["key_hash"]):
                    api_key = self._row_to_key(dict(row))
                    if not api_key.is_expired():
                        # Update last used
                        await conn.execute(
                            "UPDATE api_keys SET last_used_at = $1 WHERE key_id = $2",
                            datetime.utcnow(), api_key.key_id
                        )
                        return api_key
        else:
            import aiosqlite
            
            async with aiosqlite.connect(self._sqlite_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute(
                    "SELECT * FROM api_keys WHERE key_prefix = ? AND is_active = 1",
                    (key_prefix,)
                ) as cursor:
                    row = await cursor.fetchone()
                    if row and APIKey.verify(raw_key, row["key_hash"]):
                        api_key = self._row_to_key(dict(row))
                        if not api_key.is_expired():
                            await db.execute(
                                "UPDATE api_keys SET last_used_at = ? WHERE key_id = ?",
                                (datetime.utcnow().isoformat(), api_key.key_id)
                            )
                            await db.commit()
                            return api_key
        
        return None
    
    async def list_keys(self, user_id: str) -> list[APIKey]:
        """List user's API keys."""
        keys = []
        
        if self._use_postgres:
            async with self._pool.acquire() as conn:
                rows = await conn.fetch(
                    "SELECT * FROM api_keys WHERE user_id = $1 ORDER BY created_at DESC",
                    user_id
                )
                keys = [self._row_to_key(dict(r)) for r in rows]
        else:
            import aiosqlite
            
            async with aiosqlite.connect(self._sqlite_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute(
                    "SELECT * FROM api_keys WHERE user_id = ? ORDER BY created_at DESC",
                    (user_id,)
                ) as cursor:
                    rows = await cursor.fetchall()
                    keys = [self._row_to_key(dict(r)) for r in rows]
        
        return keys
    
    async def revoke_key(self, key_id: str, user_id: str = None) -> bool:
        """Revoke API key."""
        if self._use_postgres:
            async with self._pool.acquire() as conn:
                if user_id:
                    await conn.execute(
                        "UPDATE api_keys SET is_active = false WHERE key_id = $1 AND user_id = $2",
                        key_id, user_id
                    )
                else:
                    await conn.execute(
                        "UPDATE api_keys SET is_active = false WHERE key_id = $1",
                        key_id
                    )
        else:
            import aiosqlite
            
            async with aiosqlite.connect(self._sqlite_path) as db:
                if user_id:
                    await db.execute(
                        "UPDATE api_keys SET is_active = 0 WHERE key_id = ? AND user_id = ?",
                        (key_id, user_id)
                    )
                else:
                    await db.execute(
                        "UPDATE api_keys SET is_active = 0 WHERE key_id = ?",
                        (key_id,)
                    )
                await db.commit()
        
        return True
    
    def _row_to_key(self, row: dict) -> APIKey:
        """Convert row to APIKey."""
        scopes = row.get("scopes", ["read", "write"])
        if isinstance(scopes, str):
            scopes = scopes.split(",") if scopes else ["read", "write"]
        
        return APIKey(
            key_id=row["key_id"],
            user_id=row["user_id"],
            name=row["name"],
            key_hash=row["key_hash"],
            key_prefix=row["key_prefix"],
            scopes=scopes,
            rate_limit=row.get("rate_limit", 1000),
            is_active=bool(row.get("is_active", True)),
            created_at=self._parse_datetime(row.get("created_at")) or datetime.utcnow(),
            expires_at=self._parse_datetime(row.get("expires_at")),
            last_used_at=self._parse_datetime(row.get("last_used_at")),
        )
    
    def _parse_datetime(self, value) -> datetime | None:
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            return datetime.fromisoformat(value)
        return None


# ============================================================================
# Singleton instances
# ============================================================================

_user_manager: UserManager | None = None
_api_key_manager: APIKeyManager | None = None


async def get_user_manager() -> UserManager:
    """Get singleton user manager."""
    global _user_manager
    if _user_manager is None:
        _user_manager = UserManager()
        await _user_manager.initialize()
    return _user_manager


async def get_api_key_manager() -> APIKeyManager:
    """Get singleton API key manager."""
    global _api_key_manager
    if _api_key_manager is None:
        _api_key_manager = APIKeyManager()
        await _api_key_manager.initialize()
    return _api_key_manager
