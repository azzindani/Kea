"""
Emergency Kill Switch for System Protection.

Provides emergency controls to prevent cascading failures.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Callable

from shared.logging.main import get_logger


logger = get_logger(__name__)


@dataclass
class BlacklistEntry:
    """Blacklisted tool or server."""
    name: str
    reason: str
    until: datetime
    created_at: datetime = field(default_factory=datetime.utcnow)


class KillSwitch:
    """
    Emergency controls for system protection.
    
    Provides:
    - Emergency stop all agents
    - Tool blacklisting
    - Department pause
    - Global pause
    
    Example:
        switch = KillSwitch()
        
        # Emergency stop
        await switch.emergency_stop("Memory critical")
        
        # Blacklist failing tool
        switch.blacklist_tool("failing_tool", duration_minutes=30)
    """
    
    def __init__(self):
        self._emergency_stopped = False
        self._stop_reason: str = ""
        self._paused_departments: set[str] = set()
        self._blacklisted_tools: dict[str, BlacklistEntry] = {}
        self._on_emergency_callbacks: list[Callable] = []
    
    @property
    def is_emergency_stopped(self) -> bool:
        """Check if system is in emergency stop."""
        return self._emergency_stopped
    
    def on_emergency(self, callback: Callable) -> None:
        """Register callback for emergency events."""
        self._on_emergency_callbacks.append(callback)
    
    async def emergency_stop(self, reason: str) -> None:
        """
        Emergency stop all agents.
        
        Args:
            reason: Why emergency stop was triggered
        """
        logger.critical(f"🚨 EMERGENCY STOP: {reason}")
        self._emergency_stopped = True
        self._stop_reason = reason
        
        # Notify all callbacks
        for callback in self._on_emergency_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(reason)
                else:
                    callback(reason)
            except Exception as e:
                logger.error(f"Emergency callback failed: {e}")
    
    async def resume(self) -> None:
        """Resume from emergency stop."""
        logger.info("Resuming from emergency stop")
        self._emergency_stopped = False
        self._stop_reason = ""
    
    def blacklist_tool(
        self,
        tool_name: str,
        reason: str = "Repeated failures",
        duration_minutes: int | None = None,
    ) -> None:
        """Temporarily blacklist a tool."""
        from shared.config import get_settings
        duration_minutes = duration_minutes or get_settings().swarm.default_blacklist_duration_minutes
        
        until = datetime.utcnow() + timedelta(minutes=duration_minutes)
        self._blacklisted_tools[tool_name] = BlacklistEntry(
            name=tool_name,
            reason=reason,
            until=until,
        )
        logger.warning(f"Tool blacklisted: {tool_name} until {until} ({reason})")
    
    def unblacklist_tool(self, tool_name: str) -> None:
        """Remove tool from blacklist."""
        if tool_name in self._blacklisted_tools:
            del self._blacklisted_tools[tool_name]
            logger.info(f"Tool unblacklisted: {tool_name}")
    
    def is_tool_blacklisted(self, tool_name: str) -> bool:
        """Check if tool is currently blacklisted."""
        if tool_name not in self._blacklisted_tools:
            return False
        
        entry = self._blacklisted_tools[tool_name]
        if datetime.utcnow() > entry.until:
            # Expired, remove
            del self._blacklisted_tools[tool_name]
            return False
        
        return True
    
    def pause_department(self, dept_id: str) -> None:
        """Pause all agents in a department."""
        self._paused_departments.add(dept_id)
        logger.warning(f"Department paused: {dept_id}")
    
    def resume_department(self, dept_id: str) -> None:
        """Resume a paused department."""
        self._paused_departments.discard(dept_id)
        logger.info(f"Department resumed: {dept_id}")
    
    def is_department_paused(self, dept_id: str) -> bool:
        """Check if department is paused."""
        return dept_id in self._paused_departments
    
    def can_proceed(self, tool_name: str | None = None, dept_id: str | None = None) -> bool:
        """
        Check if operation can proceed.
        
        Returns False if:
        - Emergency stopped
        - Tool is blacklisted
        - Department is paused
        """
        if self._emergency_stopped:
            return False
        
        if tool_name and self.is_tool_blacklisted(tool_name):
            return False
        
        if dept_id and self.is_department_paused(dept_id):
            return False
        
        return True


# Global instance
_switch: KillSwitch | None = None


def get_kill_switch() -> KillSwitch:
    """Get or create global kill switch."""
    global _switch
    if _switch is None:
        _switch = KillSwitch()
    return _switch
