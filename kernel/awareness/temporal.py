"""
Temporal Awareness Engine.

Gives the kernel a sense of "time" relative to the task.
Handles:
- Time anchoring (past, present, future)
- Recency scoring (how fresh is this fact?)
- Temporal decay (how quickly does this info become stale?)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any

from shared.logging import get_logger

logger = get_logger(__name__)


class TemporalAnchor(str, Enum):
    """Refers to when the user's intent is focused."""
    LIVE = "live"            # Right now (stock prices, weather, breaking news)
    RECENT = "recent"        # Within days to weeks
    HISTORICAL = "historical"  # Months to years ago
    FUTURE = "future"        # Predictions, forecasts
    TIMELESS = "timeless"    # Facts that don't change (math, geography)


@dataclass
class TemporalContext:
    """Temporal awareness snapshot for the current task."""
    
    # System Time
    current_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    local_time: datetime | None = None
    timezone_str: str = "UTC"
    
    # Intent
    anchor: TemporalAnchor = TemporalAnchor.RECENT
    explicit_dates: list[datetime] = field(default_factory=list)
    freshness_requirement: str = "any"  # e.g. "< 24h", "live"
    
    # Reasoning Aids
    is_market_hours: bool = False
    is_weekend: bool = False
    
    def to_prompt_section(self) -> str:
        """Generate awareness section for LLM system prompt."""
        local_str = self.local_time.strftime("%Y-%m-%d %H:%M %Z") if self.local_time else "Unknown"
        lines = [
            "## ⏱️ Temporal Context",
            f"- **Current System Time**: {self.current_time.strftime('%Y-%m-%d %H:%M UTC')}",
            f"- **User Local Time**: {local_str}",
            f"- **Query Focus**: {self.anchor.value.upper()}",
        ]
        
        if self.anchor == TemporalAnchor.LIVE:
            lines.append("- **Requirement**: REAL-TIME data only. Do not use training data.")
        elif self.anchor == TemporalAnchor.RECENT:
            lines.append("- **Requirement**: Recent data (last 30 days) preferred.")
            
        if self.explicit_dates:
            dates = [d.strftime("%Y-%m-%d") for d in self.explicit_dates]
            lines.append(f"- **Explicit Dates Mentioned**: {', '.join(dates)}")
            
        if self.is_market_hours:
            lines.append("- **Market Status**: OPEN (Live financial data available)")
            
        return "\n".join(lines)


class TemporalDetector:
    """Detects temporal intent from queries."""
    
    def __init__(self):
        # Regex patterns for time anchoring
        self._live_patterns = [
            r"\b(now|current|live|real-time|today|latest|price)\b",
            r"\b(right now|at the moment)\b"
        ]
        self._future_patterns = [
            r"\b(prediction|forecast|outgoing|outlook|future|next|coming)\b",
            r"\b(will|going to|expect)\b"
        ]
        self._historical_patterns = [
            r"\b(history|past|was|did|yesterday|last year|ago)\b",
            r"\b(19\d{2}|20[0-2]\d)\b"  # Years 1900-2029 (rough)
        ]

    def analyze(self, query: str, user_timezone: str = "UTC") -> TemporalContext:
        """Analyze query to build temporal context."""
        now = datetime.now(timezone.utc)
        
        # 1. Detect Anchor
        anchor = self._detect_anchor(query)
        
        # 2. Extract Dates (simplified heuristic for v3 phase 1)
        dates = self._extract_dates(query)
        
        # 3. Market Hours (Simple heuristic: Mon-Fri 13:30-20:00 UTC ~ 9:30-16:00 ET)
        # In a real implementation this would use a proper market schedule library
        is_weekend = now.weekday() >= 5
        hour = now.hour
        is_market = not is_weekend and (13 <= hour <= 20)
        
        # 4. Local Time
        # Placeholder: In production this would use zoneinfo
        local_time = now # Default to UTC for now
        
        context = TemporalContext(
            current_time=now,
            local_time=local_time,
            timezone_str=user_timezone,
            anchor=anchor,
            explicit_dates=dates,
            is_market_hours=is_market,
            is_weekend=is_weekend
        )
        
        logger.debug(
            "Temporal analysis complete", 
            anchor=anchor.value, 
            market_open=is_market
        )
        return context

    def _detect_anchor(self, query: str) -> TemporalAnchor:
        q = query.lower()
        
        for pat in self._live_patterns:
            if re.search(pat, q):
                return TemporalAnchor.LIVE
                
        for pat in self._future_patterns:
            if re.search(pat, q):
                return TemporalAnchor.FUTURE
                
        for pat in self._historical_patterns:
            if re.search(pat, q):
                return TemporalAnchor.HISTORICAL
                
        return TemporalAnchor.RECENT  # Default to recent

    def _extract_dates(self, query: str) -> list[datetime]:
        """Rough extraction of YYYY-MM-DD or specific years."""
        dates = []
        # ISO Date
        iso_matches = re.findall(r"\b(\d{4}-\d{2}-\d{2})\b", query)
        for d_str in iso_matches:
            try:
                dates.append(datetime.strptime(d_str, "%Y-%m-%d"))
            except ValueError:
                pass
                
        # Years (contextual)
        year_matches = re.findall(r"\b(19\d{2}|20\d{2})\b", query)
        for y_str in year_matches:
             try:
                # 1st of Jan for just a year
                dates.append(datetime(int(y_str), 1, 1))
             except ValueError:
                pass
                
        return dates

