"""
Unit Tests: Hardware Detector.

Tests for hardware profile detection and resource management.
"""



class TestHardwareProfile:
    """Test HardwareProfile class."""

    def test_import_hardware_profile(self):
        """Test that HardwareProfile can be imported."""
        from shared.hardware.detector import HardwareProfile
        assert HardwareProfile is not None

    def test_create_profile(self):
        """Test creating hardware profile with correct attributes."""
        from shared.hardware.detector import HardwareProfile

        profile = HardwareProfile(
            cpu_cores=4,
            cpu_threads=8,
            ram_total_gb=16.0,
            ram_available_gb=8.0,
            gpu_count=0,
        )

        assert profile.ram_total_gb == 16.0
        assert profile.ram_available_gb == 8.0
        assert profile.cpu_threads == 8
        assert profile.gpu_count == 0

    def test_optimal_workers(self):
        """Test optimal workers calculation."""
        from shared.hardware.detector import HardwareProfile

        profile = HardwareProfile(
            cpu_cores=4,
            cpu_threads=8,
            ram_total_gb=16.0,
            ram_available_gb=8.0,
        )

        workers = profile.optimal_workers()
        assert 1 <= workers <= 8

    def test_optimal_batch_size(self):
        """Test batch size calculation."""
        from shared.hardware.detector import HardwareProfile

        profile = HardwareProfile(
            ram_total_gb=32.0,
            ram_available_gb=16.0,
        )

        batch = profile.optimal_batch_size()
        assert batch > 0


class TestHardwareState:
    """Test hardware state detection."""

    def test_memory_pressure(self):
        """Test memory pressure detection."""
        from shared.hardware.detector import HardwareProfile

        # High memory usage (low available)
        profile = HardwareProfile(
            ram_total_gb=16.0,
            ram_available_gb=1.0,
        )

        pressure = profile.memory_pressure()
        assert pressure > 0.9  # High pressure

    def test_constrained_environment(self):
        """Test constrained environment detection."""
        from shared.hardware.detector import HardwareProfile

        # Low resources -> constrained
        profile = HardwareProfile(
            ram_total_gb=4.0,
            ram_available_gb=2.0,
            cpu_cores=2,
        )

        # Low RAM (<8GB) = constrained
        assert profile.is_constrained() is True

    def test_not_constrained_high_ram(self):
        """Test not constrained with high RAM."""
        from shared.hardware.detector import HardwareProfile

        profile = HardwareProfile(
            ram_total_gb=32.0,
            ram_available_gb=16.0,
            cpu_cores=8,
            environment="local",
        )

        assert profile.is_constrained() is False


class TestDetectHardware:
    """Test detect_hardware function."""

    def test_import_detect_hardware(self):
        """Test that detect_hardware can be imported."""
        from shared.hardware.detector import detect_hardware
        assert detect_hardware is not None

    def test_detect_returns_profile(self):
        """Test detect returns HardwareProfile."""
        from shared.hardware.detector import HardwareProfile, detect_hardware

        profile = detect_hardware()
        assert isinstance(profile, HardwareProfile)

    def test_profile_has_cpu_threads(self):
        """Test profile has cpu_threads attribute."""
        from shared.hardware.detector import detect_hardware

        profile = detect_hardware()
        assert profile.cpu_threads >= 1

    def test_profile_has_environment(self):
        """Test profile has environment attribute."""
        from shared.hardware.detector import detect_hardware

        profile = detect_hardware()
        assert profile.environment in ["kaggle", "colab", "local", "vps"]


class TestGPUDetection:
    """Test GPU detection."""

    def test_can_use_gpu_embedding(self):
        """Test GPU embedding check."""
        from shared.hardware.detector import HardwareProfile

        # No CUDA
        profile = HardwareProfile(cuda_available=False)
        assert profile.can_use_gpu_embedding() is False

        # Has CUDA + enough VRAM
        profile_gpu = HardwareProfile(
            cuda_available=True,
            vram_available_gb=4.0,
        )
        assert profile_gpu.can_use_gpu_embedding() is True
