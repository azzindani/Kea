"""
Research Metrics Collection.

Tracks resource usage, efficiencies, and performance metrics.
"""

import gc
import json
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

from shared.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ResourceSnapshot:
    """Point-in-time resource snapshot."""
    timestamp: str
    ram_used_mb: float
    ram_percent: float
    cpu_percent: float


@dataclass
class JobMetrics:
    """Metrics for a single research job execution."""
    job_id: str
    query: str
    start_time: str = ""
    end_time: str = ""
    duration_ms: int = 0
    
    # LLM Efficiency
    llm_calls: int = 0
    llm_tokens_input: int = 0
    llm_tokens_output: int = 0
    llm_tokens_total: int = 0
    
    # Tool Usage
    tool_iterations: int = 0
    tool_calls_by_name: Dict[str, int] = field(default_factory=dict)
    tool_durations_by_name: Dict[str, float] = field(default_factory=dict)
    tool_errors: int = 0
    
    # Resource Usage
    peak_memory_mb: float = 0.0
    avg_cpu_percent: float = 0.0
    resource_snapshots: List[ResourceSnapshot] = field(default_factory=list)
    
    # Outcome
    success: bool = False
    error: Optional[str] = None
    report: Optional[str] = None
    confidence: float = 0.0
    facts_count: int = 0
    sources_count: int = 0
    efficiency_ratio: float = 0.0
    
    def calculate_efficiency(self):
        """Update efficiency ratio."""
        if self.llm_calls > 0:
            self.efficiency_ratio = self.tool_iterations / self.llm_calls
        else:
            self.efficiency_ratio = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        self.calculate_efficiency()
        return asdict(self)


class MetricsCollector:
    """
    Collects and tracks metrics for research jobs.
    """
    
    def __init__(self):
        self._current_job: Optional[JobMetrics] = None
        self._all_jobs: List[JobMetrics] = []
        self._snapshot_interval = 0
    
    def start_job(self, job_id: str, query: str):
        """Start tracking a new job."""
        self._current_job = JobMetrics(
            job_id=job_id,
            query=query,
            start_time=datetime.utcnow().isoformat()
        )
        self.record_snapshot()
        logger.debug(f"Started metrics for job {job_id}")
    
    def record_llm_usage(self, prompt_tokens: int, completion_tokens: int):
        """Record LLM token usage."""
        if self._current_job:
            self._current_job.llm_calls += 1
            self._current_job.llm_tokens_input += prompt_tokens
            self._current_job.llm_tokens_output += completion_tokens
            self._current_job.llm_tokens_total += (prompt_tokens + completion_tokens)
            self._current_job.calculate_efficiency()
    
    def record_tool_usage(self, tool_name: str, duration_ms: float, is_error: bool = False):
        """Record tool execution details."""
        if self._current_job:
            self._current_job.tool_iterations += 1
            
            current_count = self._current_job.tool_calls_by_name.get(tool_name, 0)
            self._current_job.tool_calls_by_name[tool_name] = current_count + 1
            
            current_duration = self._current_job.tool_durations_by_name.get(tool_name, 0.0)
            self._current_job.tool_durations_by_name[tool_name] = current_duration + duration_ms
            
            if is_error:
                self._current_job.tool_errors += 1
            
            self._current_job.calculate_efficiency()
            
            # Periodic snapshot (every 50 tool calls)
            self._snapshot_interval += 1
            if self._snapshot_interval >= 50:
                self.record_snapshot()
                self._snapshot_interval = 0

    def record_snapshot(self):
        """Take resource usage snapshot."""
        if not self._current_job:
            return
            
        ram_used = 0.0
        ram_percent = 0.0
        cpu_percent = 0.0
        
        if HAS_PSUTIL:
            try:
                mem = psutil.virtual_memory()
                ram_used = (mem.total - mem.available) / (1024 ** 2)
                ram_percent = mem.percent
                cpu_percent = psutil.cpu_percent(interval=0.1)
            except Exception:
                pass
        
        snapshot = ResourceSnapshot(
            timestamp=datetime.utcnow().isoformat(),
            ram_used_mb=ram_used,
            ram_percent=ram_percent,
            cpu_percent=cpu_percent
        )
        
        self._current_job.resource_snapshots.append(snapshot)
        if ram_used > self._current_job.peak_memory_mb:
            self._current_job.peak_memory_mb = ram_used

    def end_job(self, success: bool, error: Optional[str] = None) -> Optional[JobMetrics]:
        """Complete the job tracking."""
        if not self._current_job:
            return None
            
        self._current_job.end_time = datetime.utcnow().isoformat()
        self._current_job.success = success
        self._current_job.error = error
        
        # Calculate duration
        start = datetime.fromisoformat(self._current_job.start_time)
        end = datetime.fromisoformat(self._current_job.end_time)
        self._current_job.duration_ms = int((end - start).total_seconds() * 1000)
        
        # Final calculations
        self.record_snapshot()
        self._current_job.calculate_efficiency()
        
        if self._current_job.resource_snapshots:
            avg_cpu = sum(s.cpu_percent for s in self._current_job.resource_snapshots) / len(self._current_job.resource_snapshots)
            self._current_job.avg_cpu_percent = avg_cpu
            
        completed = self._current_job
        self._all_jobs.append(completed)
        self._current_job = None
        
        gc.collect()
        return completed
    
    def export(self, path: str):
        """Export metrics to JSON."""
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            "exported_at": datetime.utcnow().isoformat(),
            "jobs": [j.to_dict() for j in self._all_jobs]
        }
        
        with open(output_path, "w") as f:
            json.dump(data, f, indent=2, default=str)
        logger.info(f"Metrics exported to {path}")
