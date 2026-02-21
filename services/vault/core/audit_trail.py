"""
Audit Trail System.

Provides immutable audit logging for compliance requirements.
Supports PostgreSQL (production) and In-Memory (testing).
"""

from __future__ import annotations

import hashlib
import json
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from functools import wraps
from typing import Any, Callable
from uuid import uuid4

from shared.logging.main import get_logger


logger = get_logger(__name__)


# ============================================================================
# Audit Event Types
# ============================================================================

from shared.schemas import AuditEventType


@dataclass
class AuditEntry:
    """
    Immutable audit log entry.
    
    Each entry includes a checksum for integrity verification.
    """
    entry_id: str
    timestamp: datetime
    event_type: AuditEventType
    actor: str                  # User, agent, or "system"
    action: str                 # Human-readable action description
    resource: str = ""          # Resource affected (e.g., file, URL, tool)
    details: dict = field(default_factory=dict)
    parent_id: str = ""         # For tracing chains
    session_id: str = ""        # Session identifier
    checksum: str = ""          # SHA-256 for integrity
    
    def __post_init__(self):
        """Generate checksum if not provided."""
        if not self.checksum:
            self.checksum = self._compute_checksum()
    
    def _compute_checksum(self) -> str:
        """Compute SHA-256 checksum of entry."""
        data = {
            "entry_id": self.entry_id,
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type.value if hasattr(self.event_type, 'value') else str(self.event_type),
            "actor": self.actor,
            "action": self.action,
            "resource": self.resource,
            "details": self.details,
            "parent_id": self.parent_id,
            "session_id": self.session_id,
        }
        content = json.dumps(data, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()
    
    def verify(self) -> bool:
        """Verify entry integrity."""
        return self.checksum == self._compute_checksum()
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "entry_id": self.entry_id,
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type.value if hasattr(self.event_type, 'value') else str(self.event_type),
            "actor": self.actor,
            "action": self.action,
            "resource": self.resource,
            "details": self.details,
            "parent_id": self.parent_id,
            "session_id": self.session_id,
            "checksum": self.checksum,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> AuditEntry:
        """Create from dictionary."""
        return cls(
            entry_id=data["entry_id"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            event_type=AuditEventType(data["event_type"]),
            actor=data["actor"],
            action=data["action"],
            resource=data.get("resource", ""),
            details=data.get("details", {}),
            parent_id=data.get("parent_id", ""),
            session_id=data.get("session_id", ""),
            checksum=data.get("checksum", ""),
        )


# ============================================================================
# Audit Backend Interface
# ============================================================================

class AuditBackend(ABC):
    """Abstract backend for audit storage."""
    
    @abstractmethod
    async def write(self, entry: AuditEntry) -> bool:
        """Write entry to storage."""
        pass
    
    @abstractmethod
    async def query(
        self,
        start_time: datetime = None,
        end_time: datetime = None,
        event_types: list[AuditEventType] = None,
        actor: str = None,
        session_id: str = None,
        limit: int = 1000,
    ) -> list[AuditEntry]:
        """Query entries from storage."""
        pass
    
    @abstractmethod
    async def get_by_id(self, entry_id: str) -> AuditEntry | None:
        """Get single entry by ID."""
        pass
    
    @abstractmethod
    async def count(self) -> int:
        """Get total entry count."""
        pass


class MemoryBackend(AuditBackend):
    """In-memory backend for testing and lightweight use."""
    
    def __init__(self, max_entries: int = 10000):
        self._entries: list[AuditEntry] = []
        self._max_entries = max_entries
    
    async def write(self, entry: AuditEntry) -> bool:
        """Write entry to memory."""
        self._entries.append(entry)
        
        # Trim if too many entries
        if len(self._entries) > self._max_entries:
            self._entries = self._entries[-self._max_entries:]
        
        return True
    
    async def query(
        self,
        start_time: datetime = None,
        end_time: datetime = None,
        event_types: list[AuditEventType] = None,
        actor: str = None,
        session_id: str = None,
        limit: int = 1000,
    ) -> list[AuditEntry]:
        """Query entries from memory."""
        results = self._entries.copy()
        
        if start_time:
            results = [e for e in results if e.timestamp >= start_time]
        
        if end_time:
            results = [e for e in results if e.timestamp <= end_time]
        
        if event_types:
            results = [e for e in results if e.event_type in event_types]
        
        if actor:
            results = [e for e in results if e.actor == actor]
        
        if session_id:
            results = [e for e in results if e.session_id == session_id]
        
        return list(reversed(results))[:limit]
    
    async def get_by_id(self, entry_id: str) -> AuditEntry | None:
        """Get single entry by ID."""
        for entry in self._entries:
            if entry.entry_id == entry_id:
                return entry
        return None
    
    async def count(self) -> int:
        """Get total entry count."""
        return len(self._entries)


# ============================================================================
# Main Audit Trail
# ============================================================================

class AuditTrail:
    """
    Main audit trail interface.
    
    Example:
        audit = AuditTrail()
        
        # Log an event
        await audit.log(
            AuditEventType.QUERY_RECEIVED,
            action="User submitted autonomous query",
            actor="user_123",
            details={"query": "Tesla financials"},
            session_id="session_456",
        )
        
        # Query audit history
        entries = await audit.query(
            start_time=datetime.now() - timedelta(hours=1),
            event_types=[AuditEventType.QUERY_RECEIVED],
        )
    """
    
    def __init__(self, backend: AuditBackend = None):
        """
        Initialize audit trail.
        
        Args:
            backend: Storage backend (defaults to Postgres -> Memory)
        """
        if backend is None:
            from shared.config import get_settings
            settings = get_settings()
            
            # 1. Try Postgres (Primary)
            if settings.database.url:
                try:
                    from services.vault.core.postgres_audit import PostgresBackend
                    backend = PostgresBackend()
                    logger.debug("AuditTrail using PostgresBackend")
                except Exception as e:
                    logger.warning(f"Failed to init PostgresBackend: {e}, falling back to Memory")
            
            # 2. Fallback to Memory
            if backend is None:
                backend = MemoryBackend()
                logger.info("AuditTrail using MemoryBackend (No Database Configured)")
        
        self.backend = backend
        self._session_id = str(uuid4())[:8]
        logger.debug(f"AuditTrail initialized with session {self._session_id}")
    
    async def log(
        self,
        event_type: AuditEventType,
        action: str,
        actor: str = "system",
        resource: str = "",
        details: dict = None,
        parent_id: str = "",
        session_id: str = "",
    ) -> str:
        """
        Log an audit event.
        
        Args:
            event_type: Type of event
            action: Human-readable action description
            actor: Who performed the action
            resource: Resource affected
            details: Additional details
            parent_id: Parent entry ID for tracing
            session_id: Session identifier
            
        Returns:
            Entry ID
        """
        entry = AuditEntry(
            entry_id=str(uuid4()),
            timestamp=datetime.utcnow(),
            event_type=event_type,
            actor=actor,
            action=action,
            resource=resource,
            details=details or {},
            parent_id=parent_id,
            session_id=session_id or self._session_id,
        )
        
        await self.backend.write(entry)
        
        logger.debug(f"Audit: {event_type.value if hasattr(event_type, 'value') else str(event_type)} - {action[:50]}")
        
        return entry.entry_id
    
    async def query(
        self,
        start_time: datetime = None,
        end_time: datetime = None,
        event_types: list[AuditEventType] = None,
        actor: str = None,
        session_id: str = None,
        limit: int = 1000,
    ) -> list[AuditEntry]:
        """Query audit entries."""
        return await self.backend.query(
            start_time=start_time,
            end_time=end_time,
            event_types=event_types,
            actor=actor,
            session_id=session_id,
            limit=limit,
        )
    
    async def get(self, entry_id: str) -> AuditEntry | None:
        """Get single entry by ID."""
        return await self.backend.get_by_id(entry_id)
    
    async def verify_integrity(self, entries: list[AuditEntry] = None) -> tuple[int, int]:
        """
        Verify integrity of audit entries.
        
        Returns:
            (valid_count, invalid_count)
        """
        if entries is None:
            entries = await self.query(limit=10000)
        
        valid = 0
        invalid = 0
        
        for entry in entries:
            if entry.verify():
                valid += 1
            else:
                invalid += 1
                logger.warning(f"Integrity check failed for entry {entry.entry_id}")
        
        return valid, invalid
    
    async def export(self, format: str = "json") -> bytes:
        """Export audit trail."""
        entries = await self.query(limit=100000)
        
        if format == "json":
            data = [e.to_dict() for e in entries]
            return json.dumps(data, indent=2).encode()
        
        elif format == "csv":
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.DictWriter(
                output,
                fieldnames=["entry_id", "timestamp", "event_type", "actor", "action", "resource", "session_id"],
            )
            writer.writeheader()
            for entry in entries:
                writer.writerow({
                    "entry_id": entry.entry_id,
                    "timestamp": entry.timestamp.isoformat(),
                    "event_type": entry.event_type.value if hasattr(entry.event_type, 'value') else str(entry.event_type),
                    "actor": entry.actor,
                    "action": entry.action,
                    "resource": entry.resource,
                    "session_id": entry.session_id,
                })
            return output.getvalue().encode()
        
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    @property
    async def stats(self) -> dict:
        """Get audit trail statistics."""
        count = await self.backend.count()
        return {
            "total_entries": count,
            "session_id": self._session_id,
        }


# ============================================================================
# Decorator for automatic auditing
# ============================================================================

def audited(
    event_type: AuditEventType,
    action_template: str = "{func_name} called",
    include_args: bool = False,
    include_result: bool = False,
):
    """
    Decorator to automatically audit function calls.
    
    Example:
        @audited(AuditEventType.TOOL_CALLED, "Called {func_name}")
        async def my_tool(query: str):
            return result
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            audit = get_audit_trail()
            
            # Build details
            details = {}
            if include_args:
                details["args"] = str(args)[:200]
                details["kwargs"] = {k: str(v)[:100] for k, v in kwargs.items()}
            
            action = action_template.format(func_name=func.__name__)
            
            parent_id = await audit.log(
                event_type=event_type,
                action=f"Starting: {action}",
                actor="system",
                details=details,
            )
            
            try:
                result = await func(*args, **kwargs)
                
                # Log success
                result_details = {"status": "success"}
                if include_result:
                    result_details["result"] = str(result)[:500]
                
                await audit.log(
                    event_type=event_type,
                    action=f"Completed: {action}",
                    actor="system",
                    details=result_details,
                    parent_id=parent_id,
                )
                
                return result
                
            except Exception as e:
                # Log failure
                await audit.log(
                    event_type=AuditEventType.ERROR,
                    action=f"Failed: {action}",
                    actor="system",
                    details={"error": str(e)[:500]},
                    parent_id=parent_id,
                )
                raise
        
        return wrapper
    return decorator


# ============================================================================
# Singleton
# ============================================================================

_audit_trail: AuditTrail | None = None


def get_audit_trail() -> AuditTrail:
    """Get singleton audit trail."""
    global _audit_trail
    if _audit_trail is None:
        _audit_trail = AuditTrail()
    return _audit_trail


def configure_audit_trail(backend: AuditBackend):
    """Configure audit trail with custom backend."""
    global _audit_trail
    _audit_trail = AuditTrail(backend=backend)

