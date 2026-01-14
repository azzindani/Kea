"""
Tests for Graceful Degradation System.
"""

import pytest


class TestDegradationLevel:
    """Tests for degradation levels."""
    
    def test_degradation_levels(self):
        """Test degradation level enum."""
        from services.orchestrator.core.degradation import DegradationLevel
        
        assert DegradationLevel.NORMAL.value == 0
        assert DegradationLevel.WARNING.value == 1
        assert DegradationLevel.CRITICAL.value == 2
        assert DegradationLevel.EMERGENCY.value == 3
        
        print("\n✅ DegradationLevel values correct")


class TestGracefulDegrader:
    """Tests for GracefulDegrader."""
    
    def test_create_degrader(self):
        """Test degrader creation."""
        from services.orchestrator.core.degradation import GracefulDegrader
        
        degrader = GracefulDegrader(
            base_parallel=4,
            base_batch_size=1000,
        )
        
        assert degrader is not None
        print("\n✅ GracefulDegrader created")
    
    def test_get_current_level(self):
        """Test getting current level."""
        from services.orchestrator.core.degradation import GracefulDegrader, DegradationLevel
        
        degrader = GracefulDegrader()
        level = degrader.get_current_level()
        
        assert isinstance(level, DegradationLevel)
        print(f"\n✅ Current level: {level.name}")
    
    def test_set_level(self):
        """Test setting degradation level."""
        from services.orchestrator.core.degradation import GracefulDegrader, DegradationLevel
        
        degrader = GracefulDegrader()
        
        # Set to warning
        degrader.set_level(1)
        assert degrader.get_current_level() == DegradationLevel.WARNING
        
        # Set to critical
        degrader.set_level(2)
        assert degrader.get_current_level() == DegradationLevel.CRITICAL
        
        # Reset to normal
        degrader.set_level(0)
        assert degrader.get_current_level() == DegradationLevel.NORMAL
        
        print("\n✅ Level setting works")
    
    def test_get_adjusted_config_normal(self):
        """Test config at normal level."""
        from services.orchestrator.core.degradation import GracefulDegrader
        
        degrader = GracefulDegrader(base_parallel=4, base_batch_size=1000)
        degrader.set_level(0)
        
        config = degrader.get_adjusted_config()
        
        assert config["parallel"] == 4
        assert config["batch_size"] == 1000
        
        print(f"\n✅ Normal config: {config}")
    
    def test_get_adjusted_config_warning(self):
        """Test reduced config at warning level."""
        from services.orchestrator.core.degradation import GracefulDegrader
        
        degrader = GracefulDegrader(base_parallel=4, base_batch_size=1000)
        degrader.set_level(1)  # Warning
        
        config = degrader.get_adjusted_config()
        
        # Should reduce parallel workers
        assert config["parallel"] < 4
        
        print(f"\n✅ Warning config: {config}")
    
    def test_get_adjusted_config_critical(self):
        """Test minimal config at critical level."""
        from services.orchestrator.core.degradation import GracefulDegrader
        
        degrader = GracefulDegrader(base_parallel=4, base_batch_size=1000)
        degrader.set_level(2)  # Critical
        
        config = degrader.get_adjusted_config()
        
        # Should significantly reduce
        assert config["parallel"] <= 2
        
        print(f"\n✅ Critical config: {config}")
    
    def test_auto_detect_level(self):
        """Test auto-detection based on hardware."""
        from services.orchestrator.core.degradation import GracefulDegrader
        
        degrader = GracefulDegrader()
        
        # This should check hardware and set appropriate level
        degrader.auto_detect()
        level = degrader.get_current_level()
        
        assert level is not None
        print(f"\n✅ Auto-detected level: {level.name}")
    
    def test_singleton(self):
        """Test degrader singleton."""
        from services.orchestrator.core.degradation import get_degrader
        
        d1 = get_degrader()
        d2 = get_degrader()
        
        assert d1 is d2
        print("\n✅ Singleton works")


class TestThrottled:
    """Tests for throttled decorator."""
    
    def test_throttled_at_normal(self):
        """Test throttled doesn't affect normal operations."""
        from services.orchestrator.core.degradation import throttled, get_degrader
        import asyncio
        
        get_degrader().set_level(0)  # Normal
        
        call_count = 0
        
        @throttled(1)  # Only throttle at level 1+
        async def test_func():
            nonlocal call_count
            call_count += 1
            return "done"
        
        asyncio.run(test_func())
        assert call_count == 1
        
        print("\n✅ Throttled at normal level works")
    
    def test_throttled_at_warning(self):
        """Test throttled adds delay at warning level."""
        from services.orchestrator.core.degradation import throttled, get_degrader
        import asyncio
        import time
        
        get_degrader().set_level(1)  # Warning
        
        @throttled(1, delay=0.1)
        async def slow_func():
            return "done"
        
        start = time.time()
        asyncio.run(slow_func())
        duration = time.time() - start
        
        # Should have some delay
        assert duration >= 0.05  # At least some delay
        
        print(f"\n✅ Throttled added delay: {duration:.2f}s")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
