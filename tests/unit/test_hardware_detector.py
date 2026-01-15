"""
Unit Tests: Hardware Detection.

Tests for hardware profile and detection.
"""

import pytest
from unittest.mock import patch, MagicMock
import os

from shared.hardware.detector import (
    HardwareProfile,
    detect_hardware,
    _detect_environment,
)


class TestHardwareProfile:
    """Test HardwareProfile dataclass."""
    
    def test_default_profile(self):
        """Test default profile values."""
        profile = HardwareProfile()
        
        assert profile.cpu_cores == 1
        assert profile.cpu_threads == 1
        assert profile.ram_total_gb == 4.0
        assert profile.gpu_count == 0
        assert profile.cuda_available is False
        assert profile.environment == "local"
    
    def test_custom_profile(self):
        """Test custom profile values."""
        profile = HardwareProfile(
            cpu_cores=8,
            cpu_threads=16,
            ram_total_gb=32.0,
            ram_available_gb=24.0,
            gpu_count=2,
            cuda_available=True,
        )
        
        assert profile.cpu_cores == 8
        assert profile.cpu_threads == 16
        assert profile.ram_total_gb == 32.0


class TestOptimalWorkers:
    """Test optimal workers calculation."""
    
    def test_low_ram_limits_workers(self):
        """Test low RAM limits worker count."""
        profile = HardwareProfile(
            cpu_threads=16,
            ram_available_gb=4.0,  # Only 4GB available
        )
        
        workers = profile.optimal_workers()
        
        assert workers <= 2  # Limited by RAM (4GB / 2GB per worker)
    
    def test_high_threads_capped(self):
        """Test high thread count is capped."""
        profile = HardwareProfile(
            cpu_threads=32,
            ram_available_gb=64.0,
        )
        
        workers = profile.optimal_workers()
        
        assert workers <= 8  # Capped at 8
    
    def test_minimum_one_worker(self):
        """Test minimum of 1 worker."""
        profile = HardwareProfile(
            cpu_threads=1,
            ram_available_gb=0.5,
        )
        
        workers = profile.optimal_workers()
        
        assert workers >= 1


class TestOptimalBatchSize:
    """Test optimal batch size calculation."""
    
    def test_high_ram_large_batch(self):
        """Test high RAM gives large batch size."""
        profile = HardwareProfile(ram_available_gb=32.0)
        
        batch = profile.optimal_batch_size()
        
        assert batch == 10000
    
    def test_medium_ram_medium_batch(self):
        """Test medium RAM gives medium batch size."""
        profile = HardwareProfile(ram_available_gb=8.0)
        
        batch = profile.optimal_batch_size()
        
        assert batch == 5000
    
    def test_low_ram_small_batch(self):
        """Test low RAM gives small batch size."""
        profile = HardwareProfile(ram_available_gb=2.0)
        
        batch = profile.optimal_batch_size()
        
        assert batch == 500


class TestGPUCheck:
    """Test GPU capability checks."""
    
    def test_can_use_gpu_with_cuda_and_vram(self):
        """Test GPU usable with CUDA and sufficient VRAM."""
        profile = HardwareProfile(
            cuda_available=True,
            vram_available_gb=4.0,
        )
        
        assert profile.can_use_gpu_embedding() is True
    
    def test_cannot_use_gpu_without_cuda(self):
        """Test GPU not usable without CUDA."""
        profile = HardwareProfile(
            cuda_available=False,
            vram_available_gb=4.0,
        )
        
        assert profile.can_use_gpu_embedding() is False
    
    def test_cannot_use_gpu_low_vram(self):
        """Test GPU not usable with low VRAM."""
        profile = HardwareProfile(
            cuda_available=True,
            vram_available_gb=1.0,  # Less than 2GB minimum
        )
        
        assert profile.can_use_gpu_embedding() is False


class TestMemoryPressure:
    """Test memory pressure calculation."""
    
    def test_zero_pressure(self):
        """Test zero pressure when full RAM available."""
        profile = HardwareProfile(
            ram_total_gb=16.0,
            ram_available_gb=16.0,
        )
        
        pressure = profile.memory_pressure()
        
        assert pressure == 0.0
    
    def test_full_pressure(self):
        """Test full pressure when no RAM available."""
        profile = HardwareProfile(
            ram_total_gb=16.0,
            ram_available_gb=0.0,
        )
        
        pressure = profile.memory_pressure()
        
        assert pressure == 1.0
    
    def test_half_pressure(self):
        """Test half pressure."""
        profile = HardwareProfile(
            ram_total_gb=16.0,
            ram_available_gb=8.0,
        )
        
        pressure = profile.memory_pressure()
        
        assert pressure == 0.5


class TestIsConstrained:
    """Test constrained environment detection."""
    
    def test_colab_is_constrained(self):
        """Test Colab is constrained."""
        profile = HardwareProfile(
            environment="colab",
            ram_total_gb=12.0,
        )
        
        assert profile.is_constrained() is True
    
    def test_kaggle_is_constrained(self):
        """Test Kaggle is constrained."""
        profile = HardwareProfile(
            environment="kaggle",
            ram_total_gb=16.0,
        )
        
        assert profile.is_constrained() is True
    
    def test_low_ram_is_constrained(self):
        """Test low RAM local is constrained."""
        profile = HardwareProfile(
            environment="local",
            ram_total_gb=4.0,
        )
        
        assert profile.is_constrained() is True
    
    def test_high_ram_local_not_constrained(self):
        """Test high RAM local is not constrained."""
        profile = HardwareProfile(
            environment="local",
            ram_total_gb=32.0,
        )
        
        assert profile.is_constrained() is False


class TestDetectEnvironment:
    """Test environment detection."""
    
    def test_detect_colab(self):
        """Test Colab detection."""
        with patch.dict(os.environ, {"COLAB_GPU": "1"}):
            env = _detect_environment()
            assert env == "colab"
    
    def test_detect_kaggle(self):
        """Test Kaggle detection."""
        with patch.dict(os.environ, {"KAGGLE_KERNEL_RUN_TYPE": "Interactive"}):
            env = _detect_environment()
            assert env == "kaggle"
    
    def test_detect_local(self):
        """Test local detection (default)."""
        # Clear any cloud indicators
        env_vars = {k: "" for k in [
            "COLAB_GPU", "COLAB_RELEASE_TAG",
            "KAGGLE_KERNEL_RUN_TYPE",
            "KUBERNETES_SERVICE_HOST", "AWS_REGION", "GCP_PROJECT"
        ]}
        with patch.dict(os.environ, env_vars, clear=False):
            with patch("os.path.exists", return_value=False):
                env = _detect_environment()
                assert env == "local"


class TestDetectHardware:
    """Test hardware detection function."""
    
    def test_detect_returns_profile(self):
        """Test detect returns HardwareProfile."""
        with patch("shared.hardware.detector.psutil") as mock_psutil:
            mock_psutil.cpu_count.return_value = 4
            mock_psutil.virtual_memory.return_value = MagicMock(
                total=16 * 1024**3,
                available=8 * 1024**3,
            )
            
            profile = detect_hardware()
            
            assert isinstance(profile, HardwareProfile)
            assert profile.python_version != ""
