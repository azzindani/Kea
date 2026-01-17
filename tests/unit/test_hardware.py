"""
Tests for Hardware Detection and Resource Monitoring.
"""

import pytest
import asyncio


class TestHardwareDetection:
    """Tests for hardware detection."""
    
    def test_detect_hardware(self):
        """Test hardware detection returns valid profile."""
        from shared.hardware import detect_hardware, HardwareProfile
        
        profile = detect_hardware()
        
        assert isinstance(profile, HardwareProfile)
        assert profile.cpu_cores >= 1
        assert profile.cpu_threads >= 1
        assert profile.ram_total_gb > 0
        assert profile.environment in ("colab", "kaggle", "vps", "local")
        
        print(f"\n✅ Hardware Profile:")
        print(f"   CPU: {profile.cpu_cores} cores, {profile.cpu_threads} threads")
        print(f"   RAM: {profile.ram_total_gb:.1f}GB total, {profile.ram_available_gb:.1f}GB free")
        print(f"   GPU: {profile.gpu_count} ({', '.join(profile.gpu_names) or 'None'})")
        print(f"   Environment: {profile.environment}")
    
    def test_optimal_workers(self):
        """Test optimal worker calculation."""
        from shared.hardware import detect_hardware
        
        profile = detect_hardware()
        workers = profile.optimal_workers()
        
        assert workers >= 1
        assert workers <= 8  # Capped at 8
        print(f"\n✅ Optimal workers: {workers}")
    
    def test_optimal_batch_size(self):
        """Test batch size calculation."""
        from shared.hardware import detect_hardware
        
        profile = detect_hardware()
        batch = profile.optimal_batch_size()
        
        assert batch >= 500
        assert batch <= 10000
        print(f"\n✅ Optimal batch size: {batch}")
    
    def test_memory_pressure(self):
        """Test memory pressure calculation."""
        from shared.hardware import detect_hardware
        
        profile = detect_hardware()
        pressure = profile.memory_pressure()
        
        assert 0.0 <= pressure <= 1.0
        print(f"\n✅ Memory pressure: {pressure:.1%}")


class TestExecutorConfig:
    """Tests for executor configuration."""
    
    def test_get_optimal_config(self):
        """Test optimal config generation."""
        from shared.hardware import get_optimal_config, ExecutorConfig
        
        config = get_optimal_config()
        
        assert isinstance(config, ExecutorConfig)
        assert config.max_parallel_scrapers >= 1
        assert config.max_parallel_llm_calls >= 1
        assert config.batch_size >= 500
        
        print(f"\n✅ Executor Config:")
        print(f"   Scrapers: {config.max_parallel_scrapers}")
        print(f"   LLM calls: {config.max_parallel_llm_calls}")
        print(f"   Embedders: {config.max_parallel_embedders}")
        print(f"   Batch size: {config.batch_size}")
        print(f"   GPU embedding: {config.use_gpu_embedding}")


class TestResourceMonitor:
    """Tests for resource monitoring."""
    
    @pytest.mark.asyncio
    async def test_monitor_start_stop(self):
        """Test monitor lifecycle."""
        from shared.hardware import ResourceMonitor
        
        monitor = ResourceMonitor(check_interval_seconds=0.5)
        
        await monitor.start()
        await asyncio.sleep(0.6)  # Let it take one snapshot
        
        snapshot = monitor.get_current_snapshot()
        assert snapshot is not None
        assert snapshot.ram_percent >= 0
        
        await monitor.stop()
        
        print(f"\n✅ Monitor snapshot:")
        print(f"   RAM: {snapshot.ram_percent:.1f}%")
        print(f"   CPU: {snapshot.cpu_percent:.1f}%")
    
    @pytest.mark.asyncio
    async def test_monitor_alerts(self):
        """Test alert emission."""
        from shared.hardware import ResourceMonitor, ResourceAlert
        
        alerts_received: list[ResourceAlert] = []
        
        def on_alert(alert: ResourceAlert):
            alerts_received.append(alert)
            print(f"\n⚠️ Alert: {alert.level.value} - {alert.message}")
        
        # Use very low threshold to trigger alert
        monitor = ResourceMonitor(
            ram_warning_percent=1.0,  # Will definitely trigger
            check_interval_seconds=0.5,
        )
        monitor.on_alert(on_alert)
        
        await monitor.start()
        await asyncio.sleep(0.6)
        await monitor.stop()
        
        # Should have received at least one warning (RAM > 1%)
        assert len(alerts_received) > 0
        print(f"\n✅ Received {len(alerts_received)} alert(s)")
    
    def test_recommended_parallelism(self):
        """Test parallelism recommendation."""
        from shared.hardware import ResourceMonitor
        
        monitor = ResourceMonitor()
        
        # Without snapshot, should return base
        recommended = monitor.get_recommended_parallelism(base_parallelism=4)
        assert recommended == 4
        
        print(f"\n✅ Recommended parallelism: {recommended}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
