"""
Stress Test Metrics Collection.

Tracks resource usage, LLM efficiency, and performance metrics.
"""

from __future__ import annotations

import gc
import json
import os
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

from shared.logging.main import get_logger


logger = get_logger(__name__)


@dataclass
class ResourceSnapshot:
    """Point-in-time resource snapshot."""
    timestamp: str
    ram_used_mb: float
    ram_percent: float
    cpu_percent: float


@dataclass
class QueryMetrics:
    """Metrics for a single query execution."""
    query_id: int
    query_name: str
    start_time: str = ""
    end_time: str = ""
    duration_ms: int = 0
    
    # LLM Efficiency (KEY METRIC)
    llm_calls: int = 0
    llm_tokens_input: int = 0
    llm_tokens_output: int = 0
    llm_tokens_total: int = 0
    
    # Tool Iterations (should be >> llm_calls)
    tool_iterations: int = 0
    tool_calls_by_name: dict[str, int] = field(default_factory=dict)
    tool_durations_by_name: dict[str, float] = field(default_factory=dict)
    tool_errors: int = 0
    
    # Efficiency Ratio (target: >> 100)
    @property
    def efficiency_ratio(self) -> float:
        if self.llm_calls == 0:
            return 0.0
        return self.tool_iterations / self.llm_calls
    
    # Resource Usage
    peak_memory_mb: float = 0.0
    avg_cpu_percent: float = 0.0
    resource_snapshots: list[ResourceSnapshot] = field(default_factory=list)
    
    # Cache
    cache_hits: int = 0
    cache_misses: int = 0
    
    @property
    def cache_hit_rate(self) -> float:
        total = self.cache_hits + self.cache_misses
        if total == 0:
            return 0.0
        return self.cache_hits / total
    
    @property
    def total_tool_duration_ms(self) -> float:
        """Total CPU time spent in tools (can exceed wall clock if parallel)."""
        return sum(self.tool_durations_by_name.values())
        
    @property
    def concurrency_factor(self) -> float:
        """Measure of parallelism: Total Tool Time / Wall Clock Time."""
        if self.duration_ms == 0:
            return 0.0
        return self.total_tool_duration_ms / self.duration_ms
    
    # Output
    artifacts_produced: list[str] = field(default_factory=list)
    database_built: bool = False
    agents_spawned: int = 0
    
    # Status
    success: bool = False
    error_type: str = ""
    error_message: str = ""
    
    def to_dict(self) -> dict:
        """Convert to dictionary with computed properties."""
        d = asdict(self)
        d["efficiency_ratio"] = self.efficiency_ratio
        d["cache_hit_rate"] = self.cache_hit_rate
        return d


class MetricsCollector:
    """
    Collects and tracks metrics during stress test execution.
    
    Usage:
        metrics = MetricsCollector()
        metrics.start_query(1, "Indonesian Alpha Hunt")
        
        # During execution
        metrics.record_llm_call(tokens_in=100, tokens_out=500)
        metrics.record_tool_call("fetch_url", duration_ms=150)
        metrics.record_resource_snapshot()
        
        # On completion
        metrics.end_query(success=True)
        
        # Export
        metrics.export("results/query_1.json")
    """
    
    def __init__(self) -> None:
        self._current_query: QueryMetrics | None = None
        self._all_queries: list[QueryMetrics] = []
        self._snapshot_interval_calls: int = 0
    
    def start_query(self, query_id: int, query_name: str) -> None:
        """Start tracking a new query."""
        self._current_query = QueryMetrics(
            query_id=query_id,
            query_name=query_name,
            start_time=datetime.utcnow().isoformat(),
        )
        self._snapshot_interval_calls = 0
        
        # Initial snapshot
        self.record_resource_snapshot()
        
        logger.info(f"Started metrics for query {query_id}: {query_name}")
    
    def record_llm_call(
        self,
        tokens_in: int = 0,
        tokens_out: int = 0,
    ) -> None:
        """Record an LLM inference call."""
        if not self._current_query:
            return
        
        self._current_query.llm_calls += 1
        self._current_query.llm_tokens_input += tokens_in
        self._current_query.llm_tokens_output += tokens_out
        self._current_query.llm_tokens_total += tokens_in + tokens_out
    
    def record_tool_call(
        self,
        tool_name: str,
        duration_ms: float = 0.0,
        is_error: bool = False,
    ) -> None:
        """Record a tool iteration."""
        if not self._current_query:
            return
        
        self._current_query.tool_iterations += 1
        
        # Track by name
        if tool_name not in self._current_query.tool_calls_by_name:
            self._current_query.tool_calls_by_name[tool_name] = 0
            self._current_query.tool_durations_by_name[tool_name] = 0.0
        
        self._current_query.tool_calls_by_name[tool_name] += 1
        self._current_query.tool_durations_by_name[tool_name] += duration_ms
        
        if is_error:
            self._current_query.tool_errors += 1
        
        # Periodic resource snapshot (every 100 tool calls)
        self._snapshot_interval_calls += 1
        if self._snapshot_interval_calls >= 100:
            self.record_resource_snapshot()
            self._snapshot_interval_calls = 0
    
    def record_cache_event(self, hit: bool) -> None:
        """Record cache hit or miss."""
        if not self._current_query:
            return
        
        if hit:
            self._current_query.cache_hits += 1
        else:
            self._current_query.cache_misses += 1
    
    def record_resource_snapshot(self) -> None:
        """Take a resource usage snapshot."""
        if not self._current_query:
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
            except Exception as e:
                logger.debug(f"Failed to get resource snapshot: {e}")
        
        snapshot = ResourceSnapshot(
            timestamp=datetime.utcnow().isoformat(),
            ram_used_mb=ram_used,
            ram_percent=ram_percent,
            cpu_percent=cpu_percent,
        )
        
        self._current_query.resource_snapshots.append(snapshot)
        
        # Update peak
        if ram_used > self._current_query.peak_memory_mb:
            self._current_query.peak_memory_mb = ram_used
    
    def record_artifact(self, path: str) -> None:
        """Record an artifact produced."""
        if not self._current_query:
            return
        self._current_query.artifacts_produced.append(path)
    
    def record_database_built(self) -> None:
        """Record that a database was built."""
        if not self._current_query:
            return
        self._current_query.database_built = True
    
    def record_agent_spawn(self) -> None:
        """Record an agent spawn."""
        if not self._current_query:
            return
        self._current_query.agents_spawned += 1
    
    def end_query(
        self,
        success: bool,
        error: Exception | None = None,
    ) -> QueryMetrics | None:
        """End tracking for current query."""
        if not self._current_query:
            return None
        
        self._current_query.end_time = datetime.utcnow().isoformat()
        self._current_query.success = success
        
        # Calculate duration
        start = datetime.fromisoformat(self._current_query.start_time)
        end = datetime.fromisoformat(self._current_query.end_time)
        self._current_query.duration_ms = int((end - start).total_seconds() * 1000)
        
        # Calculate average CPU
        if self._current_query.resource_snapshots:
            total_cpu = sum(s.cpu_percent for s in self._current_query.resource_snapshots)
            self._current_query.avg_cpu_percent = total_cpu / len(self._current_query.resource_snapshots)
        
        if error:
            self._current_query.error_type = type(error).__name__
            self._current_query.error_message = str(error)
        
        # Final snapshot
        self.record_resource_snapshot()
        
        # Store
        completed = self._current_query
        self._all_queries.append(completed)
        self._current_query = None
        
        # Force GC
        gc.collect()
        
        logger.info(
            f"Query {completed.query_id} completed: "
            f"success={success}, "
            f"duration={completed.duration_ms}ms, "
            f"efficiency_ratio={completed.efficiency_ratio:.1f}"
        )
        
        return completed
    
    def get_current_metrics(self) -> QueryMetrics | None:
        """Get metrics for currently running query."""
        return self._current_query
    
    def get_all_metrics(self) -> list[QueryMetrics]:
        """Get metrics for all completed queries."""
        return self._all_queries
    
    def get_summary(self) -> dict[str, Any]:
        """Get aggregated summary of all queries."""
        if not self._all_queries:
            return {}
        
        total_llm_calls = sum(q.llm_calls for q in self._all_queries)
        total_tool_iterations = sum(q.tool_iterations for q in self._all_queries)
        total_tokens = sum(q.llm_tokens_total for q in self._all_queries)
        total_duration = sum(q.duration_ms for q in self._all_queries)
        successful = sum(1 for q in self._all_queries if q.success)
        
        return {
            "total_queries": len(self._all_queries),
            "successful": successful,
            "failed": len(self._all_queries) - successful,
            "success_rate": successful / len(self._all_queries),
            "total_duration_ms": total_duration,
            "total_llm_calls": total_llm_calls,
            "total_tool_iterations": total_tool_iterations,
            "total_tokens": total_tokens,
            "overall_efficiency_ratio": (
                total_tool_iterations / total_llm_calls if total_llm_calls > 0 else 0
            ),
            "peak_memory_mb": max(q.peak_memory_mb for q in self._all_queries),
        }
    
    def export(self, path: str) -> None:
        """Export metrics to JSON file."""
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            "exported_at": datetime.utcnow().isoformat(),
            "summary": self.get_summary(),
            "queries": [q.to_dict() for q in self._all_queries],
        }
        
        with open(output_path, "w") as f:
            json.dump(data, f, indent=2, default=str)
        
        logger.info(f"Exported metrics to {path}")
    
    def export_query(self, query_metrics: QueryMetrics, path: str) -> None:
        """Export single query metrics."""
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, "w") as f:
            json.dump(query_metrics.to_dict(), f, indent=2, default=str)
        
        logger.info(f"Exported query metrics to {path}")
