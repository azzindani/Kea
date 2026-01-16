"""
Tests for hardware resource monitoring.
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

from shared.hardware.monitor import (
    AlertLevel,
    ResourceAlert,
    ResourceSnapshot,
    ResourceMonitor,
)


class TestAlertLevel:
    """Tests for AlertLevel enum."""
    
    def test_alert_levels(self):
        """Test alert level values."""
        assert AlertLevel.INFO.value == "info"
        assert AlertLevel.WARNING.value == "warning"
        assert AlertLevel.CRITICAL.value == "critical"


class TestResourceAlert:
    """Tests for ResourceAlert dataclass."""
    
    def test_alert_creation(self):
        """Test creating resource alert."""
        alert = ResourceAlert(
            level=AlertLevel.WARNING,
            resource="ram",
            message="Memory usage high",
            value=85.0,
            threshold=75.0,
        )
        assert alert.level == AlertLevel.WARNING
        assert alert.resource == "ram"
        assert alert.value > alert.threshold
        assert alert.timestamp is not None


class TestResourceSnapshot:
    """Tests for ResourceSnapshot dataclass."""
    
    def test_snapshot_creation(self):
        """Test creating resource snapshot."""
        snapshot = ResourceSnapshot(
            timestamp=datetime.utcnow(),
            ram_percent=50.0,
            ram_available_gb=8.0,
            cpu_percent=25.0,
            gpu_memory_percent=0.0,
            disk_free_gb=100.0,
        )
        assert snapshot.ram_percent == 50.0
        assert snapshot.cpu_percent == 25.0


class TestResourceMonitor:
    """Tests for ResourceMonitor."""
    
    @pytest.fixture
    def monitor(self):
        return ResourceMonitor(
            ram_warning_percent=75.0,
            ram_critical_percent=90.0,
            cpu_warning_percent=80.0,
            check_interval_seconds=1.0,
        )
    
    def test_monitor_init(self, monitor):
        """Test monitor initialization."""
        assert monitor.ram_warning == 75.0
        assert monitor.ram_critical == 90.0
        assert monitor.cpu_warning == 80.0
        assert monitor.check_interval == 1.0
    
    def test_on_alert_callback(self, monitor):
        """Test registering alert callback."""
        callback = MagicMock()
        monitor.on_alert(callback)
        assert callback in monitor._callbacks
    
    def test_is_memory_critical_false(self, monitor):
        """Test memory critical when no snapshot."""
        assert monitor.is_memory_critical() is False
    
    def test_is_memory_warning_false(self, monitor):
        """Test memory warning when no snapshot."""
        assert monitor.is_memory_warning() is False
    
    def test_is_memory_critical_true(self, monitor):
        """Test memory critical detection."""
        monitor._last_snapshot = ResourceSnapshot(
            timestamp=datetime.utcnow(),
            ram_percent=95.0,
            ram_available_gb=0.5,
            cpu_percent=50.0,
        )
        assert monitor.is_memory_critical() is True
    
    def test_is_memory_warning_true(self, monitor):
        """Test memory warning detection."""
        monitor._last_snapshot = ResourceSnapshot(
            timestamp=datetime.utcnow(),
            ram_percent=80.0,
            ram_available_gb=2.0,
            cpu_percent=50.0,
        )
        assert monitor.is_memory_warning() is True
    
    def test_get_current_snapshot(self, monitor):
        """Test getting current snapshot."""
        assert monitor.get_current_snapshot() is None
        
        snapshot = ResourceSnapshot(
            timestamp=datetime.utcnow(),
            ram_percent=50.0,
            ram_available_gb=8.0,
            cpu_percent=25.0,
        )
        monitor._last_snapshot = snapshot
        assert monitor.get_current_snapshot() == snapshot
    
    def test_get_recommended_parallelism_normal(self, monitor):
        """Test parallelism recommendation under normal load."""
        monitor._last_snapshot = ResourceSnapshot(
            timestamp=datetime.utcnow(),
            ram_percent=50.0,
            ram_available_gb=8.0,
            cpu_percent=25.0,
        )
        result = monitor.get_recommended_parallelism(8)
        assert result == 8
    
    def test_get_recommended_parallelism_warning(self, monitor):
        """Test parallelism recommendation under warning."""
        monitor._last_snapshot = ResourceSnapshot(
            timestamp=datetime.utcnow(),
            ram_percent=80.0,
            ram_available_gb=2.0,
            cpu_percent=50.0,
        )
        result = monitor.get_recommended_parallelism(8)
        assert result == 4
    
    def test_get_recommended_parallelism_critical(self, monitor):
        """Test parallelism recommendation under critical."""
        monitor._last_snapshot = ResourceSnapshot(
            timestamp=datetime.utcnow(),
            ram_percent=95.0,
            ram_available_gb=0.5,
            cpu_percent=50.0,
        )
        result = monitor.get_recommended_parallelism(8)
        assert result == 2
    
    @pytest.mark.asyncio
    async def test_start_stop(self, monitor):
        """Test starting and stopping monitor."""
        await monitor.start()
        assert monitor._running is True
        
        await monitor.stop()
        assert monitor._running is False
    
    def test_emit_alert(self, monitor):
        """Test emitting alerts to callbacks."""
        callback = MagicMock()
        monitor.on_alert(callback)
        
        alert = ResourceAlert(
            level=AlertLevel.WARNING,
            resource="ram",
            message="Test alert",
            value=80.0,
            threshold=75.0,
        )
        monitor._emit_alert(alert)
        
        callback.assert_called_once_with(alert)
