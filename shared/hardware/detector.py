"""
Hardware Detection.

Auto-detect system capabilities for adaptive execution.
"""

from __future__ import annotations

import os
import platform
from dataclasses import dataclass, field
from typing import Literal

from shared.logging.main import get_logger


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
        from shared.config import get_settings
        settings = get_settings().hardware
        # Base on CPU threads, but limit by RAM
        cpu_based = max(1, self.cpu_threads - 1)  # Leave 1 for main
        ram_based = max(1, int(self.ram_available_gb / settings.ram_per_worker_gb))
        return min(cpu_based, ram_based, settings.worker_cap)
    
    def optimal_batch_size(self) -> int:
        """Calculate optimal batch size for data processing."""
        from shared.config import get_settings
        settings = get_settings().hardware
        if self.ram_available_gb >= settings.batch_size_high_threshold:
            return settings.batch_size_high_val
        elif self.ram_available_gb >= settings.batch_size_med_threshold:
            return settings.batch_size_med_val
        elif self.ram_available_gb >= settings.batch_size_low_threshold:
            return settings.batch_size_low_val
        else:
            return settings.batch_size_min_val
    
    def can_use_gpu_embedding(self) -> bool:
        """Check if GPU can be used for embeddings."""
        from shared.config import get_settings
        return self.cuda_available and self.vram_available_gb >= get_settings().hardware.vram_min_embedding_gb
    
    def memory_pressure(self) -> float:
        """Calculate memory pressure (0.0 = free, 1.0 = full)."""
        if self.ram_total_gb == 0:
            return 1.0
        return 1.0 - (self.ram_available_gb / self.ram_total_gb)

    def should_queue_tasks(self) -> bool:
        """Check if tasks should be queued due to high memory pressure.

        Returns True if RAM usage > High Pressure Threshold, preventing OOM crashes.
        """
        from shared.config import get_settings
        threshold = get_settings().hardware.high_pressure_threshold
        pressure = self.memory_pressure()
        return pressure > threshold

    def safe_parallel_limit(self) -> int:
        """Calculate safe parallel task limit based on current RAM pressure."""
        from shared.config import get_settings
        settings = get_settings().hardware
        
        pressure = self.memory_pressure()
        base_limit = self.optimal_workers()

        if pressure > settings.critical_pressure_threshold:
            return max(1, base_limit // settings.critical_pressure_divisor)
        elif pressure > settings.high_pressure_threshold:
            return max(1, base_limit // settings.high_pressure_divisor)
        elif pressure > settings.moderate_pressure_threshold:
            return max(2, int(base_limit * settings.moderate_pressure_multiplier))
        else:
            return base_limit

    def is_constrained(self) -> bool:
        """Check if running in constrained environment."""
        from shared.config import get_settings
        threshold = get_settings().hardware.constrained_ram_threshold
        return self.environment in ("colab", "kaggle") or self.ram_total_gb < threshold
    
    def optimal_max_results(self) -> int:
        """Calculate optimal max_results based on RAM."""
        from shared.config import get_settings
        settings = get_settings().knowledge
        return min(
            int(self.ram_available_gb * settings.results_per_gb_ram),
            settings.max_results_cap
        )
    
    def optimal_top_k(self) -> int:
        """Calculate optimal top_k for tool routing."""
        from shared.config import get_settings
        settings = get_settings().hardware
        return max(settings.top_k_min, self.optimal_workers() * settings.top_k_multiplier)
    
    def optimal_search_limit(self) -> int:
        """Calculate optimal limit for web/API searches."""
        import math
        from shared.config import get_settings
        settings = get_settings().hardware
        base = settings.search_limit_multiplier * math.log2(max(1, self.ram_available_gb) + 1)
        return max(settings.search_limit_min, min(settings.search_limit_max, int(base)))
    
    def optimal_tool_registry_limit(self) -> int:
        """Calculate optimal limit for tool registry searches."""
        from shared.config import get_settings
        settings = get_settings().knowledge
        limit = int(settings.tool_registry_multiplier * self.ram_available_gb)
        return max(settings.tool_registry_min, min(settings.tool_registry_max, limit))
    
    def optimal_fact_limit(self) -> int:
        """Calculate optimal limit for semantic fact search."""
        import math
        from shared.config import get_settings
        settings = get_settings().knowledge
        limit = int(settings.fact_limit_sqrt_multiplier * math.sqrt(max(1, self.ram_available_gb)))
        return max(settings.fact_limit_min, min(settings.fact_limit_max, limit))

    
    def vram_pressure(self) -> float:
        """Calculate VRAM pressure (0.0 = free, 1.0 = full).
        
        Returns 0.0 if no GPU available.
        """
        if not self.cuda_available or self.vram_total_gb == 0:
            return 0.0
        return 1.0 - (self.vram_available_gb / self.vram_total_gb)
    
    def is_gpu_oom_risk(self, required_gb: float | None = None) -> bool:
        """Check if GPU is at risk of OOM.
        
        Args:
            required_gb: Estimated VRAM needed for upcoming operation (defaults to config)
            
        Returns:
            True if available VRAM < required_gb or VRAM pressure > critical threshold
        """
        from shared.config import get_settings
        settings = get_settings().hardware
        req = required_gb if required_gb is not None else settings.vram_oom_limit_gb
        
        if not self.cuda_available:
            return True  # No GPU = always risky
        return self.vram_available_gb < req or self.vram_pressure() > settings.critical_pressure_threshold
    
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
    
    def is_ram_oom_risk(self, required_gb: float | None = None) -> bool:
        """Check if RAM is at risk of OOM.
        
        Args:
            required_gb: Estimated RAM needed for upcoming operation (defaults to config)
            
        Returns:
            True if available RAM < required_gb or RAM pressure > critical threshold
        """
        from shared.config import get_settings
        settings = get_settings().hardware
        req = required_gb if required_gb is not None else settings.ram_oom_limit_gb

        return self.ram_available_gb < req or self.memory_pressure() > settings.critical_pressure_threshold


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
    
    if not os.path.exists(".quiet_logs"):
        logger.debug(
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
