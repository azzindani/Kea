"""
Unit Tests: Hardware Detector.

Tests for hardware profile detection and resource management.
"""

import pytest
from unittest.mock import patch, MagicMock


class TestHardwareProfile:
    """Test HardwareProfile class."""
    
    def test_import_hardware_profile(self):
        """Test that HardwareProfile can be imported."""
        from shared.hardware.detector import HardwareProfile
        assert HardwareProfile is not None
    
    def test_create_profile(self):
        """Test creating hardware profile."""
        from shared.hardware.detector import HardwareProfile
        
        profile = HardwareProfile(
            total_ram_gb=16.0,
            available_ram_gb=8.0,
            cpu_count=4,
            has_gpu=False,
        )
        
        assert profile.total_ram_gb == 16.0
        assert profile.available_ram_gb == 8.0
        assert profile.cpu_count == 4
        assert profile.has_gpu is False
    
    def test_optimal_workers(self):
        """Test optimal workers calculation."""
        from shared.hardware.detector import HardwareProfile
        
        profile = HardwareProfile(
            total_ram_gb=16.0,
            available_ram_gb=8.0,
            cpu_count=8,
            has_gpu=False,
        )
        
        workers = profile.optimal_workers(min_workers=1, max_workers=4)
        assert 1 <= workers <= 4
    
    def test_optimal_batch_size(self):
        """Test batch size calculation."""
        from shared.hardware.detector import HardwareProfile
        
        profile = HardwareProfile(
            total_ram_gb=32.0,
            available_ram_gb=16.0,
            cpu_count=8,
            has_gpu=True,
        )
        
        batch = profile.optimal_batch_size(min_batch=1, max_batch=64)
        assert 1 <= batch <= 64


class TestHardwareState:
    """Test hardware state detection."""
    
    def test_memory_pressure(self):
        """Test memory pressure detection."""
        from shared.hardware.detector import HardwareProfile
        
        # High memory usage
        profile = HardwareProfile(
            total_ram_gb=16.0,
            available_ram_gb=1.0,  # Low available
            cpu_count=4,
        )
        
        assert profile.is_memory_constrained()
    
    def test_constrained_environment(self):
        """Test constrained environment detection."""
        from shared.hardware.detector import HardwareProfile
        
        # Low resources
        profile = HardwareProfile(
            total_ram_gb=4.0,  # Low RAM
            available_ram_gb=2.0,
            cpu_count=2,  # Few CPUs
        )
        
        assert profile.is_constrained() is True


class TestHardwareDetector:
    """Test HardwareDetector class."""
    
    def test_import_detector(self):
        """Test that detector functions can be imported."""
        from shared.hardware.detector import (
            HardwareDetector,
            detect_hardware,
            get_hardware_profile,
        )
        assert HardwareDetector is not None
        assert detect_hardware is not None
    
    def test_detect_returns_profile(self):
        """Test detect returns HardwareProfile."""
        from shared.hardware.detector import detect_hardware, HardwareProfile
        
        profile = detect_hardware()
        assert isinstance(profile, HardwareProfile)
    
    def test_profile_has_cpu_count(self):
        """Test profile has CPU count."""
        from shared.hardware.detector import detect_hardware
        
        profile = detect_hardware()
        assert profile.cpu_count >= 1


class TestDetectEnvironment:
    """Test environment detection."""
    
    def test_detect_environment_function(self):
        """Test that detect_environment returns a string."""
        from shared.hardware.detector import detect_environment
        
        env = detect_environment()
        # Should return a valid environment string
        assert env in ["kaggle", "colab", "local", "docker", "cloud"]
