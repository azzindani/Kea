"""
Chronos Helper Utilities.

Cron expression parsing and due-time detection.
"""

from __future__ import annotations
from datetime import datetime
from typing import Any

from shared.config import get_settings
from shared.logging.main import get_logger

logger = get_logger(__name__)

def next_run(cron_expr: str) -> datetime | None:
    """Compute the next UTC run time for a cron expression."""
    try:
        from croniter import croniter

        now = datetime.utcnow()
        return croniter(cron_expr, now).get_next(datetime)
    except Exception as e:
        logger.warning(f"Invalid cron expression '{cron_expr}': {e}")
        return None

def is_due(next_run_at: Any, tolerance_s: float | None = None) -> bool:
    """Return True if the task is due to fire (within tolerance seconds)."""
    settings = get_settings()
    if tolerance_s is None:
        tolerance_s = settings.chronos.due_tolerance
        
    if next_run_at is None:
        return False
        
    if isinstance(next_run_at, str):
        next_run_at = datetime.fromisoformat(next_run_at)
        
        
    now = datetime.utcnow()
    from datetime import timedelta
    return now >= next_run_at - timedelta(seconds=tolerance_s)
