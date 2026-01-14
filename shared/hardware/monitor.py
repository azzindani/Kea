"""
Real-time Resource Monitoring.

Provides continuous monitoring with alerts for memory pressure.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Callable

from shared.logging import get_logger


logger = get_logger(__name__)


class AlertLevel(str, Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class ResourceAlert:
    """Resource usage alert."""
    level: AlertLevel
    resource: str  # "ram", "cpu", "gpu", "disk"
    message: str
    value: float
    threshold: float
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ResourceSnapshot:
    """Point-in-time resource snapshot."""
    timestamp: datetime
    ram_percent: float
    ram_available_gb: float
    cpu_percent: float
    gpu_memory_percent: float = 0.0
    disk_free_gb: float = 0.0


class ResourceMonitor:
    """
    Real-time resource monitoring with alerts.
    
    Usage:
        monitor = ResourceMonitor()
        monitor.on_alert(my_callback)
        await monitor.start()
        
        # Check current state
        if monitor.is_memory_critical():
            # Reduce parallelism
            pass
    """
    
    def __init__(
        self,
        ram_warning_percent: float = 75.0,
        ram_critical_percent: float = 90.0,
        cpu_warning_percent: float = 80.0,
        check_interval_seconds: float = 5.0,
    ):
        self.ram_warning = ram_warning_percent
        self.ram_critical = ram_critical_percent
        self.cpu_warning = cpu_warning_percent
        self.check_interval = check_interval_seconds
        
        self._running = False
        self._task: asyncio.Task | None = None
        self._callbacks: list[Callable[[ResourceAlert], None]] = []
        self._history: list[ResourceSnapshot] = []
        self._max_history = 100
        
        # Current state
        self._last_snapshot: ResourceSnapshot | None = None
        self._in_critical = False
    
    def on_alert(self, callback: Callable[[ResourceAlert], None]) -> None:
        """Register alert callback."""
        self._callbacks.append(callback)
    
    async def start(self) -> None:
        """Start monitoring loop."""
        if self._running:
            return
        
        self._running = True
        self._task = asyncio.create_task(self._monitor_loop())
        logger.info("Resource monitor started")
    
    async def stop(self) -> None:
        """Stop monitoring loop."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Resource monitor stopped")
    
    def is_memory_critical(self) -> bool:
        """Check if memory is critically low."""
        if not self._last_snapshot:
            return False
        return self._last_snapshot.ram_percent >= self.ram_critical
    
    def is_memory_warning(self) -> bool:
        """Check if memory is at warning level."""
        if not self._last_snapshot:
            return False
        return self._last_snapshot.ram_percent >= self.ram_warning
    
    def get_current_snapshot(self) -> ResourceSnapshot | None:
        """Get most recent resource snapshot."""
        return self._last_snapshot
    
    def get_recommended_parallelism(self, base_parallelism: int) -> int:
        """Get recommended parallelism based on current resources."""
        if not self._last_snapshot:
            return base_parallelism
        
        if self.is_memory_critical():
            return max(1, base_parallelism // 4)
        elif self.is_memory_warning():
            return max(1, base_parallelism // 2)
        else:
            return base_parallelism
    
    async def _monitor_loop(self) -> None:
        """Main monitoring loop."""
        while self._running:
            try:
                snapshot = self._take_snapshot()
                self._last_snapshot = snapshot
                
                # Keep history
                self._history.append(snapshot)
                if len(self._history) > self._max_history:
                    self._history = self._history[-self._max_history:]
                
                # Check for alerts
                self._check_alerts(snapshot)
                
            except Exception as e:
                logger.error(f"Monitor error: {e}")
            
            await asyncio.sleep(self.check_interval)
    
    def _take_snapshot(self) -> ResourceSnapshot:
        """Take current resource snapshot."""
        ram_percent = 0.0
        ram_available = 0.0
        cpu_percent = 0.0
        disk_free = 0.0
        
        try:
            import psutil
            mem = psutil.virtual_memory()
            ram_percent = mem.percent
            ram_available = mem.available / (1024**3)
            cpu_percent = psutil.cpu_percent(interval=0.1)
            
            disk = psutil.disk_usage("/")
            disk_free = disk.free / (1024**3)
        except ImportError:
            pass
        except Exception as e:
            logger.debug(f"Snapshot error: {e}")
        
        return ResourceSnapshot(
            timestamp=datetime.utcnow(),
            ram_percent=ram_percent,
            ram_available_gb=ram_available,
            cpu_percent=cpu_percent,
            disk_free_gb=disk_free,
        )
    
    def _check_alerts(self, snapshot: ResourceSnapshot) -> None:
        """Check snapshot against thresholds and emit alerts."""
        # RAM critical
        if snapshot.ram_percent >= self.ram_critical:
            if not self._in_critical:
                self._emit_alert(ResourceAlert(
                    level=AlertLevel.CRITICAL,
                    resource="ram",
                    message=f"Memory critically low: {snapshot.ram_percent:.1f}%",
                    value=snapshot.ram_percent,
                    threshold=self.ram_critical,
                ))
                self._in_critical = True
        
        # RAM warning
        elif snapshot.ram_percent >= self.ram_warning:
            self._in_critical = False
            self._emit_alert(ResourceAlert(
                level=AlertLevel.WARNING,
                resource="ram",
                message=f"Memory usage high: {snapshot.ram_percent:.1f}%",
                value=snapshot.ram_percent,
                threshold=self.ram_warning,
            ))
        
        else:
            self._in_critical = False
        
        # CPU warning
        if snapshot.cpu_percent >= self.cpu_warning:
            self._emit_alert(ResourceAlert(
                level=AlertLevel.WARNING,
                resource="cpu",
                message=f"CPU usage high: {snapshot.cpu_percent:.1f}%",
                value=snapshot.cpu_percent,
                threshold=self.cpu_warning,
            ))
    
    def _emit_alert(self, alert: ResourceAlert) -> None:
        """Emit alert to all callbacks."""
        for callback in self._callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"Alert callback error: {e}")
