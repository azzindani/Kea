"""
Spatial Awareness Engine.

Gives the kernel a sense of "place" and jurisdiction.
Handles:
- Locale detection (US vs UK vs ID)
- Regulatory context (GDPR vs CCPA vs OJK)
- Market awareness (NYSE vs IDX vs LSE)
- Cultural calibration (units, currency, formality)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from shared.logging import get_logger

logger = get_logger(__name__)


@dataclass
class SpatialContext:
    """Spatial awareness snapshot for the current task."""
    
    # Location
    country_code: str = "US"       # ISO 3166-1 alpha-2
    timezone: str = "UTC"
    language: str = "en"           # ISO 639-1
    locale: str = "en-US"          # Full locale
    
    # Jurisdiction
    jurisdiction: str = "US-FED"   # Legal jurisdiction
    currency: str = "USD"          # Primary currency
    regulations: list[str] = field(default_factory=list)
    
    # Market
    primary_exchange: str = "NYSE" # Likely exchange based on region
    market_sensitive: bool = False # Does this region have strict financial rules?
    
    # Culture
    units: str = "imperial"        # metric vs imperial
    formality: str = "professional" # casual vs formal
    
    def to_prompt_section(self) -> str:
        """Generate awareness section for LLM system prompt."""
        lines = [
            "## 🌍 Spatial & Jurisdictional Context",
            f"- **User Location**: {self.country_code} ({self.timezone})",
            f"- **Jurisdiction**: {self.jurisdiction}",
            f"- **Currency**: {self.currency}",
            f"- **Primary Exchange**: {self.primary_exchange}",
            f"- **Units**: {self.units.upper()}",
        ]
        
        if self.regulations:
            lines.append(f"- **Active Regulations**: {', '.join(self.regulations)}")
            
        if self.market_sensitive:
            lines.append("⚠️Financial advice in this jurisdiction is regulated. Provide data, not advice.")
            
        return "\n".join(lines)


class SpatialDetector:
    """Detects spatial context from user profile and query hints."""
    
    def __init__(self):
        # Mapping: Country -> (Currency, Exchange, Units, Regulations)
        self._region_map = {
            "US": ("USD", "NYSE/NASDAQ", "imperial", ["SEC", "FCC"]),
            "GB": ("GBP", "LSE", "metric", ["FCA", "GDPR"]),
            "EU": ("EUR", "Euronext", "metric", ["GDPR", "MiFID II"]),
            "ID": ("IDR", "IDX", "metric", ["OJK", "BI"]),
            "SG": ("SGD", "SGX", "metric", ["MAS"]),
            "JP": ("JPY", "TSE", "metric", ["FSA"]),
            "CN": ("CNY", "SSE/SZSE", "metric", ["CSRC"]),
            # Default fallback
            "__DEFAULT__": ("USD", "Global", "metric", [])
        }

    def analyze(self, user_profile: dict[str, Any] | None = None) -> SpatialContext:
        """
        Analyze context based on user profile.
        
        Args:
            user_profile: Dict containing 'country', 'timezone', 'language', etc.
        """
        profile = user_profile or {}
        country = profile.get("country", "US").upper()
        
        # Look up region data
        if country in self._region_map:
            currency, exchange, units, regs = self._region_map[country]
        else:
            currency, exchange, units, regs = self._region_map["__DEFAULT__"]
            
        # Refine context
        is_market_sensitive = any(r in ["SEC", "FCA", "MAS", "OJK"] for r in regs)
        
        # Build context
        context = SpatialContext(
            country_code=country,
            timezone=profile.get("timezone", "UTC"),
            language=profile.get("language", "en"),
            locale=f"{profile.get('language', 'en')}-{country}",
            jurisdiction=f"{country}-NATIONAL",
            currency=currency,
            regulations=regs,
            primary_exchange=exchange,
            market_sensitive=is_market_sensitive,
            units=units,
            formality=profile.get("preference_formality", "professional")
        )
        
        logger.debug(
            "Spatial analysis complete", 
            country=country, 
            jurisdiction=context.jurisdiction
        )
        return context

