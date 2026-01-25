"""
Hardware Detection.

Auto-detect system capabilities for adaptive execution.
"""

from __future__ import annotations

import os
import platform
from dataclasses import dataclass, field
from typing import Literal

from shared.logging import get_logger


logger = get_logger(__name__)


@dataclass
class HardwareProfile:
    """System hardware profile."""
    
    # CPU
    cpu_cores: int = 1
    cpu_threads: int = 1
    cpu_model: str = "Unknown"
    
    # Memory
    ram_total_gb: float = 4.0
    ram_available_gb: float = 2.0
    
    # GPU
    gpu_count: int = 0
    gpu_names: list[str] = field(default_factory=list)
    vram_total_gb: float = 0.0
    vram_available_gb: float = 0.0
    cuda_available: bool = False
    
    # Storage
    disk_total_gb: float = 50.0
    disk_free_gb: float = 10.0
    
    # Environment
    environment: Literal["colab", "kaggle", "vps", "local"] = "local"
    python_version: str = ""
    os_name: str = ""
    
    def optimal_workers(self) -> int:
        """Calculate optimal number of worker threads."""
        # Base on CPU threads, but limit by RAM
        cpu_based = max(1, self.cpu_threads - 1)  # Leave 1 for main
        ram_based = max(1, int(self.ram_available_gb / 2))  # 2GB per worker
        return min(cpu_based, ram_based, 8)  # Cap at 8
    
    def optimal_batch_size(self) -> int:
        """Calculate optimal batch size for data processing."""
        if self.ram_available_gb >= 16:
            return 10000
        elif self.ram_available_gb >= 8:
            return 5000
        elif self.ram_available_gb >= 4:
            return 1000
        else:
            return 500
    
    def can_use_gpu_embedding(self) -> bool:
        """Check if GPU can be used for embeddings."""
        return self.cuda_available and self.vram_available_gb >= 2.0
    
    def memory_pressure(self) -> float:
        """Calculate memory pressure (0.0 = free, 1.0 = full)."""
        if self.ram_total_gb == 0:
            return 1.0
        return 1.0 - (self.ram_available_gb / self.ram_total_gb)
    
    def is_constrained(self) -> bool:
        """Check if running in constrained environment."""
        return self.environment in ("colab", "kaggle") or self.ram_total_gb < 8
    
    def optimal_max_results(self) -> int:
        """Calculate optimal max_results based on RAM.
        
        Returns hardware-aware limit for search/discovery operations.
        10K results per GB of RAM, capped at 100K.
        """
        return min(int(self.ram_available_gb * 10000), 100000)
    
    def optimal_top_k(self) -> int:
        """Calculate optimal top_k for tool routing.
        
        Returns hardware-aware limit for tool discovery.
        Based on workers * 10, minimum 20.
        """
        return max(20, self.optimal_workers() * 10)
    
    def optimal_search_limit(self) -> int:
        """Calculate optimal limit for web/API searches.
        
        Uses logarithmic scaling: 10 * log2(RAM + 1)
        Range: ~10 (1GB) to ~100 (128GB)
        """
        import math
        base = 10 * math.log2(max(1, self.ram_available_gb) + 1)
        return max(10, min(100, int(base)))
    
    def optimal_tool_registry_limit(self) -> int:
        """Calculate optimal limit for tool registry searches.
        
        Uses linear scaling: 300 * RAM (capped)
        Range: 100 (minimal) to 10000 (32GB+)
        """
        limit = int(300 * self.ram_available_gb)
        return max(100, min(10000, limit))
    
    def optimal_fact_limit(self) -> int:
        """Calculate optimal limit for semantic fact search.
        
        Uses square root scaling: 40 * sqrt(RAM)
        Range: ~20 (1GB) to ~500 (150GB)
        """
        import math
        limit = int(40 * math.sqrt(max(1, self.ram_available_gb)))
        return max(20, min(500, limit))

    
    def vram_pressure(self) -> float:
        """Calculate VRAM pressure (0.0 = free, 1.0 = full).
        
        Returns 0.0 if no GPU available.
        """
        if not self.cuda_available or self.vram_total_gb == 0:
            return 0.0
        return 1.0 - (self.vram_available_gb / self.vram_total_gb)
    
    def is_gpu_oom_risk(self, required_gb: float = 1.0) -> bool:
        """Check if GPU is at risk of OOM.
        
        Args:
            required_gb: Estimated VRAM needed for upcoming operation
            
        Returns:
            True if available VRAM < required_gb or VRAM pressure > 90%
        """
        if not self.cuda_available:
            return True  # No GPU = always risky
        return self.vram_available_gb < required_gb or self.vram_pressure() > 0.9
    
    def refresh_vram(self) -> None:
        """Refresh VRAM stats (call before GPU operations)."""
        if not self.cuda_available:
            return
        try:
            import torch
            torch.cuda.synchronize()
            self.vram_available_gb = 0.0
            for i in range(self.gpu_count):
                free, total = torch.cuda.mem_get_info(i)
                self.vram_available_gb += free / (1024**3)
        except Exception:
            pass
    
    def refresh_ram(self) -> None:
        """Refresh RAM stats (call before memory-intensive operations)."""
        try:
            import psutil
            mem = psutil.virtual_memory()
            self.ram_available_gb = mem.available / (1024**3)
        except Exception:
            pass
    
    def is_ram_oom_risk(self, required_gb: float = 2.0) -> bool:
        """Check if RAM is at risk of OOM.
        
        Args:
            required_gb: Estimated RAM needed for upcoming operation
            
        Returns:
            True if available RAM < required_gb or RAM pressure > 90%
        """
        return self.ram_available_gb < required_gb or self.memory_pressure() > 0.9


def detect_hardware() -> HardwareProfile:
    """Detect system hardware capabilities."""
    profile = HardwareProfile()
    
    # Python and OS
    profile.python_version = platform.python_version()
    profile.os_name = platform.system()
    
    # Detect environment
    profile.environment = _detect_environment()
    
    # CPU detection
    try:
        import psutil
        profile.cpu_cores = psutil.cpu_count(logical=False) or 1
        profile.cpu_threads = psutil.cpu_count(logical=True) or 1
    except ImportError:
        profile.cpu_cores = os.cpu_count() or 1
        profile.cpu_threads = os.cpu_count() or 1
    
    # RAM detection
    try:
        import psutil
        mem = psutil.virtual_memory()
        profile.ram_total_gb = mem.total / (1024**3)
        profile.ram_available_gb = mem.available / (1024**3)
    except ImportError:
        logger.warning("psutil not available, using defaults for RAM")
    
    # GPU detection
    try:
        import torch
        if torch.cuda.is_available():
            profile.cuda_available = True
            profile.gpu_count = torch.cuda.device_count()
            for i in range(profile.gpu_count):
                profile.gpu_names.append(torch.cuda.get_device_name(i))
            # VRAM
            total_vram = 0
            free_vram = 0
            for i in range(profile.gpu_count):
                props = torch.cuda.get_device_properties(i)
                total_vram += props.total_memory
                free_vram += torch.cuda.memory_reserved(i) - torch.cuda.memory_allocated(i)
            profile.vram_total_gb = total_vram / (1024**3)
            profile.vram_available_gb = free_vram / (1024**3)
    except ImportError:
        logger.debug("torch not available, GPU detection skipped")
    except Exception as e:
        logger.debug(f"GPU detection failed: {e}")
    
    # Disk detection
    try:
        import shutil
        disk = shutil.disk_usage("/")
        profile.disk_total_gb = disk.total / (1024**3)
        profile.disk_free_gb = disk.free / (1024**3)
    except Exception:
        pass
    
    logger.info(
        f"Hardware detected: {profile.cpu_threads} threads, "
        f"{profile.ram_total_gb:.1f}GB RAM, "
        f"{profile.gpu_count} GPU(s), "
        f"env={profile.environment}"
    )
    
    return profile


def _detect_environment() -> Literal["colab", "kaggle", "vps", "local"]:
    """Detect runtime environment."""
    # Colab detection
    if "COLAB_GPU" in os.environ or "COLAB_RELEASE_TAG" in os.environ:
        return "colab"
    
    # Kaggle detection
    if "KAGGLE_KERNEL_RUN_TYPE" in os.environ or os.path.exists("/kaggle"):
        return "kaggle"
    
    # VPS detection (common cloud indicators)
    if any(k in os.environ for k in ["KUBERNETES_SERVICE_HOST", "AWS_REGION", "GCP_PROJECT"]):
        return "vps"
    
    # Check for containerized environment
    if os.path.exists("/.dockerenv") or os.path.exists("/run/.containerenv"):
        return "vps"
    
    return "local"
