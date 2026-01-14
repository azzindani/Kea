"""
Hardware Detection and Resource Monitoring.

Provides:
- HardwareProfile: Auto-detect CPU, RAM, GPU, storage
- ResourceMonitor: Real-time monitoring with alerts
- ExecutorConfig: Adaptive parallelism based on hardware
"""

from .detector import HardwareProfile, detect_hardware
from .monitor import ResourceMonitor, ResourceAlert
from .executor_config import ExecutorConfig, get_optimal_config

__all__ = [
    "HardwareProfile",
    "detect_hardware",
    "ResourceMonitor",
    "ResourceAlert",
    "ExecutorConfig",
    "get_optimal_config",
]
