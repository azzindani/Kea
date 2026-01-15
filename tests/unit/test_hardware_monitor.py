"""
Unit Tests: Hardware Monitor and Executor Config.

Tests for hardware monitoring and executor configuration.
"""

import pytest
from unittest.mock import patch, MagicMock

from shared.hardware.monitor import (
    HardwareMonitor,
    ResourceUsage,
    get_monitor,
)
from shared.hardware.executor_config import (
    ExecutorConfig,
    get_executor_config,
)


class TestResourceUsage:
    """Test ResourceUsage dataclass."""
    
    def test_default_values(self):
        """Test default resource values."""
        usage = ResourceUsage()
        
        assert usage.cpu_percent == 0.0
        assert usage.memory_percent == 0.0
        assert usage.memory_used_gb == 0.0
    
    def test_custom_values(self):
        """Test custom resource values."""
        usage = ResourceUsage(
            cpu_percent=75.0,
            memory_percent=60.0,
            memory_used_gb=12.0,
        )
        
        assert usage.cpu_percent == 75.0
        assert usage.memory_percent == 60.0


class TestHardwareMonitor:
    """Test HardwareMonitor class."""
    
    @pytest.fixture
    def monitor(self):
        """Create monitor for testing."""
        return HardwareMonitor()
    
    def test_monitor_init(self, monitor):
        """Test monitor initialization."""
        assert monitor is not None
    
    def test_get_usage(self, monitor):
        """Test getting resource usage."""
        with patch("shared.hardware.monitor.psutil") as mock:
            mock.cpu_percent.return_value = 50.0
            mock.virtual_memory.return_value = MagicMock(
                percent=60.0,
                used=8 * 1024**3,
            )
            
            usage = monitor.get_usage()
            
            assert isinstance(usage, ResourceUsage)
    
    def test_is_overloaded_false(self, monitor):
        """Test not overloaded with low usage."""
        with patch.object(monitor, "get_usage") as mock:
            mock.return_value = ResourceUsage(
                cpu_percent=30.0,
                memory_percent=40.0,
            )
            
            assert monitor.is_overloaded() is False
    
    def test_is_overloaded_high_cpu(self, monitor):
        """Test overloaded with high CPU."""
        with patch.object(monitor, "get_usage") as mock:
            mock.return_value = ResourceUsage(
                cpu_percent=95.0,
                memory_percent=40.0,
            )
            
            assert monitor.is_overloaded() is True
    
    def test_is_overloaded_high_memory(self, monitor):
        """Test overloaded with high memory."""
        with patch.object(monitor, "get_usage") as mock:
            mock.return_value = ResourceUsage(
                cpu_percent=30.0,
                memory_percent=95.0,
            )
            
            assert monitor.is_overloaded() is True


class TestExecutorConfig:
    """Test ExecutorConfig class."""
    
    def test_default_config(self):
        """Test default executor config."""
        config = ExecutorConfig()
        
        assert config.max_workers >= 1
        assert config.batch_size >= 1
    
    def test_from_hardware_profile(self):
        """Test creating config from hardware profile."""
        from shared.hardware.detector import HardwareProfile
        
        profile = HardwareProfile(
            cpu_threads=8,
            ram_available_gb=16.0,
        )
        
        config = ExecutorConfig.from_profile(profile)
        
        assert config.max_workers >= 1
    
    def test_constrained_mode(self):
        """Test constrained mode config."""
        config = ExecutorConfig.constrained()
        
        assert config.max_workers <= 2
        assert config.batch_size <= 100


class TestGlobalMonitor:
    """Test global monitor singleton."""
    
    def test_get_monitor_singleton(self):
        """Test get_monitor returns singleton."""
        import shared.hardware.monitor as module
        module._monitor = None
        
        m1 = get_monitor()
        m2 = get_monitor()
        
        assert m1 is m2


class TestGetExecutorConfig:
    """Test global executor config."""
    
    def test_get_executor_config_singleton(self):
        """Test get_executor_config returns config."""
        import shared.hardware.executor_config as module
        module._config = None
        
        c1 = get_executor_config()
        c2 = get_executor_config()
        
        assert c1 is c2
