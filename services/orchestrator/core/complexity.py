"""
Query Complexity Classifier.

Scores query complexity across multiple dimensions and returns dynamic
execution limits that scale with the actual work required.

This replaces the static "one size fits all" limits that caused every query
(simple lookup or full portfolio analysis) to generate 3-5 tasks.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from functools import cache

from shared.logging import get_logger
from shared.prompts import get_complexity_config

logger = get_logger(__name__)


@cache
def _complexity_cfg() -> dict:
    """Load and cache complexity.yaml config."""
    return get_complexity_config()


class ComplexityTier(str, Enum):
    """Overall complexity classification."""
    TRIVIAL = "trivial"    # Single fact lookup
    LOW = "low"            # 1-2 data sources, single entity
    MEDIUM = "medium"      # 2-3 entities or data sources, some analysis
    HIGH = "high"          # Multi-entity, multi-source, deep analysis
    EXTREME = "extreme"    # Portfolio-scale, cross-domain, recursive


@dataclass
class ComplexityScore:
    """Multi-dimensional complexity assessment."""
    # Dimension scores (0.0 - 1.0)
    entity_count: int = 1
    depth_score: float = 0.2    # How deep the analysis needs to go
    breadth_score: float = 0.2  # How many data sources / domains
    computation_score: float = 0.1  # How much computation is needed

    # Derived tier
    tier: ComplexityTier = ComplexityTier.LOW

    # Dynamic execution limits
    max_subtasks: int = 5
    max_phases: int = 2
    max_depth: int = 3
    max_parallel: int = 4
    max_research_iterations: int = 2

    @property
    def composite(self) -> float:
        """Composite score from 0.0 to 1.0."""
        entity_factor = min(1.0, self.entity_count / 10)
        return (entity_factor + self.depth_score + self.breadth_score +
                self.computation_score) / 4.0


# ============================================================================
# Keyword Patterns for Classification
# ============================================================================

# Patterns that indicate multiple entities
MULTI_ENTITY_PATTERNS = [
    r'\b(?:all|every|each)\s+(?:stocks?|companies|tickers?|assets?|funds?)',
    r'\b(?:portfolio|basket|index|sector|industry)\b',
    r'\b(?:IDX\d+|LQ45|S&P\s*500|NASDAQ|DOW|NIKKEI|FTSE)',
    r'\bcompare\s+\w+\s+(?:vs\.?|versus|and|with)\s+\w+',
    r'\b\w+\s+vs\.?\s+\w+\s+vs\.?\s+\w+',
    r'(?:top|bottom)\s+\d+',
]

# Patterns that indicate deep analysis
DEPTH_PATTERNS = [
    (r'\b(?:DCF|discounted\s+cash\s+flow|valuation\s+model)', 0.9),
    (r'\b(?:Monte\s*Carlo|simulation|back\s*test|stress\s*test)', 0.9),
    (r'\b(?:regression|correlation|time\s*series|forecast)', 0.8),
    (r'\b(?:comprehensive|thorough|deep|detailed|in-depth|exhaustive)', 0.7),
    (r'\b(?:risk\s*(?:model|analysis|assessment)|VaR|Sharpe)', 0.8),
    (r'\b(?:sensitivity|scenario)\s+analysis', 0.8),
    (r'\b(?:technical\s+analysis|chart\s+pattern)', 0.6),
    (r'\b(?:fundamental\s+analysis|financial\s+statement)', 0.5),
    (r'\b(?:analyze|analysis|evaluate|assess)\b', 0.4),
    (r'\b(?:get|fetch|show|what\s+is|find)\b', 0.1),
]

# Patterns that indicate broad data needs
BREADTH_PATTERNS = [
    (r'\b(?:cross-domain|multi-source|holistic|360|complete\s+picture)', 0.9),
    (r'\b(?:financial|market)\s+(?:and|&|,)\s+(?:news|sentiment)', 0.8),
    (r'\b(?:macro|micro|industry|sector)\s+(?:and|&|,)', 0.7),
    (r'\b(?:income|balance|cash\s*flow).+(?:income|balance|cash\s*flow)', 0.6),
    (r'\b(?:quarterly|annual|historical|time\s*series)', 0.5),
    (r'\b(?:news|sentiment|social\s*media|analyst)', 0.5),
    (r'\b(?:SEC|filing|10-K|10-Q|regulatory)', 0.6),
]

# Patterns that indicate heavy computation
COMPUTATION_PATTERNS = [
    (r'\b(?:build|create|generate)\s+(?:model|dashboard|report)', 0.7),
    (r'\b(?:code|script|program|python|execute)', 0.6),
    (r'\b(?:calculate|compute|derive|transform)', 0.5),
    (r'\b(?:visuali[sz]e|chart|graph|plot)', 0.4),
    (r'\b(?:export|format|convert)', 0.3),
]


def classify_complexity(
    query: str,
    available_tools: list[str] | None = None,
) -> ComplexityScore:
    """
    Classify query complexity and return dynamic execution limits.

    Analyzes the query across four dimensions:
    - Entity count: How many distinct entities (stocks, companies, etc.)
    - Depth: How deep the analysis needs to go
    - Breadth: How many data sources are needed
    - Computation: How much processing is required

    Args:
        query: The user's research query
        available_tools: Optional list of available tool names (for context)

    Returns:
        ComplexityScore with dimension scores and dynamic limits
    """
    query_lower = query.lower()
    score = ComplexityScore()

    # ================================================================
    # 1. Entity Count
    # ================================================================
    score.entity_count = _count_entities(query)

    # ================================================================
    # 2. Depth Score
    # ================================================================
    score.depth_score = _score_patterns(query_lower, DEPTH_PATTERNS)

    # ================================================================
    # 3. Breadth Score
    # ================================================================
    score.breadth_score = _score_patterns(query_lower, BREADTH_PATTERNS)

    # ================================================================
    # 4. Computation Score
    # ================================================================
    score.computation_score = _score_patterns(query_lower, COMPUTATION_PATTERNS)

    # ================================================================
    # 5. Determine Tier
    # ================================================================
    composite = score.composite
    sc = _complexity_cfg().get("scoring", {})
    if composite < sc.get("trivial_threshold", 0.15):
        score.tier = ComplexityTier.TRIVIAL
    elif composite < sc.get("low_threshold", 0.30):
        score.tier = ComplexityTier.LOW
    elif composite < sc.get("medium_threshold", 0.50):
        score.tier = ComplexityTier.MEDIUM
    elif composite < sc.get("high_threshold", 0.75):
        score.tier = ComplexityTier.HIGH
    else:
        score.tier = ComplexityTier.EXTREME

    # ================================================================
    # 6. Set Dynamic Limits Based on Tier
    # ================================================================
    _set_dynamic_limits(score)

    logger.info(
        f"📊 Complexity: tier={score.tier.value} composite={composite:.2f} "
        f"entities={score.entity_count} depth={score.depth_score:.2f} "
        f"breadth={score.breadth_score:.2f} compute={score.computation_score:.2f} "
        f"→ max_subtasks={score.max_subtasks} max_phases={score.max_phases} "
        f"max_depth={score.max_depth}"
    )

    return score


def _count_entities(query: str) -> int:
    """Count distinct entities in the query."""
    count = 1  # Default: at least one entity

    query_upper = query.upper()

    # Count explicit ticker symbols (e.g., BBCA.JK, NVDA, AAPL)
    tickers = re.findall(r'\b[A-Z]{1,5}(?:\.[A-Z]{1,3})?\b', query_upper)
    # Filter out common English words that look like tickers
    noise = {
        'THE', 'AND', 'FOR', 'ALL', 'GET', 'TOP', 'VS', 'ITS', 'HAS',
        'ARE', 'NOT', 'BUT', 'HOW', 'WHY', 'CAN', 'DO', 'IS', 'IT',
        'OF', 'IN', 'TO', 'A', 'I', 'AN', 'AS', 'AT', 'BY', 'IF',
        'ON', 'OR', 'SO', 'UP', 'BE', 'NO', 'WE', 'MY', 'HE', 'ME',
        'DCF', 'SEC', 'IPO', 'ETF', 'PE', 'ROE', 'ROA', 'EPS', 'CEO',
    }
    real_tickers = [t for t in tickers if t not in noise and len(t) >= 2]
    if real_tickers:
        count = max(count, len(set(real_tickers)))

    # Check for multi-entity patterns
    query_lower = query.lower()
    for pattern in MULTI_ENTITY_PATTERNS:
        if re.search(pattern, query_lower):
            # Portfolio/index references imply many entities
            if re.search(r'\b(?:all|every|portfolio|index)\b', query_lower):
                count = max(count, 20)
            elif re.search(r'\b(?:top|bottom)\s+(\d+)', query_lower):
                match = re.search(r'\b(?:top|bottom)\s+(\d+)', query_lower)
                if match:
                    count = max(count, int(match.group(1)))
            elif re.search(r'IDX|LQ45|S&P|NASDAQ', query_upper):
                count = max(count, 30)
            else:
                count = max(count, 3)
            break

    # Count "vs" separated entities
    vs_matches = re.findall(r'\b\w+\s+(?:vs\.?|versus)\s+\w+', query_lower)
    if vs_matches:
        # Each "vs" adds one entity
        count = max(count, len(vs_matches) + 1)

    return count


def _score_patterns(query: str, patterns: list[tuple[str, float]]) -> float:
    """Score query against weighted patterns, return max match score."""
    max_score = 0.0
    total_score = 0.0
    match_count = 0

    for pattern, weight in patterns:
        if re.search(pattern, query, re.IGNORECASE):
            max_score = max(max_score, weight)
            total_score += weight
            match_count += 1

    if match_count == 0:
        return 0.1  # Minimum baseline

    # Blend: mostly the max match, but slightly boosted by having multiple matches
    blended = max_score * 0.7 + min(1.0, total_score / len(patterns)) * 0.3
    return min(1.0, blended)


def _set_dynamic_limits(score: ComplexityScore) -> None:
    """Set execution limits based on complexity tier and entity count."""
    tier = score.tier
    entities = score.entity_count

    # Hardware-aware multiplier (scale based on RAM, not CPU)
    # CPU can run at 100% without crash, but RAM (OOM) kills processes!
    hw_multiplier = 1.0
    try:
        from shared.hardware.detector import detect_hardware
        hw = detect_hardware()
        ram_gb = hw.total_memory_gb

        # RAM-based scaling (the real bottleneck for task spawning)
        # 16GB RAM = 1.0x baseline
        # 31GB RAM (Kaggle) = 1.9x
        # 64GB RAM = 4.0x
        # 256GB RAM = 16x
        # 1TB RAM = 64x (capped at 20x below)
        ram_multiplier = ram_gb / 16.0  # 16GB = 1.0x
        hw_multiplier = max(1.0, min(ram_multiplier, 20.0))  # Cap at 20x

        # GPU factor (bonus multiplier if GPU available)
        gpu_multiplier = 1.0
        if hasattr(hw, 'gpu_count') and hw.gpu_count > 0:
            # GPU helps with embedding calculations, not task spawning
            # Add 0.2x per GPU (up to 1.0x bonus for 5+ GPUs)
            gpu_multiplier = 1.0 + min(hw.gpu_count * 0.2, 1.0)

        hw_multiplier *= gpu_multiplier

        logger.info(
            f"🔧 Hardware multiplier: {hw_multiplier:.1f}x "
            f"(RAM: {ram_gb:.1f}GB, GPUs: {getattr(hw, 'gpu_count', 0)})"
        )
    except Exception as e:
        logger.debug(f"Hardware detection skipped: {e}")

    cfg = _complexity_cfg()
    sc = cfg.get("scoring", {})
    t = cfg.get("tiers", {}).get(tier.value, cfg.get("tiers", {}).get("medium", {}))
    base = t.get("max_subtasks_base", 10)
    per_entity = t.get("max_subtasks_per_entity", 3)
    max_ph = t.get("max_phases", 6)
    max_dp = t.get("max_depth", 4)
    max_par = t.get("max_parallel", 8)
    max_ri = t.get("max_research_iterations", 3)

    score.max_subtasks = int(max(base, entities * per_entity) * hw_multiplier)
    score.max_phases = max(max_ph, int(max_ph * hw_multiplier))
    score.max_depth = max(max_dp, int(max_dp * hw_multiplier))
    score.max_parallel = max(max_par, int(max_par * hw_multiplier))
    score.max_research_iterations = max(max_ri, int(max_ri * hw_multiplier))

    # Apply OOM-safe caps (RAM-aware, prevents crashes)
    try:
        from shared.hardware.detector import detect_hardware
        hw = detect_hardware()

        # Use safe parallel limit (respects RAM pressure, prevents OOM)
        # If RAM > 80%, this will reduce parallelism automatically
        safe_workers = hw.safe_parallel_limit()
        score.max_parallel = min(score.max_parallel, safe_workers)

        # Increased caps to utilize many tools effectively:
        # - 2000 tools available → need many phases to explore them
        # - 3600s timeout → can handle 200+ phases
        # - RAM-based: more RAM = more tasks (OOM is the real bottleneck, not CPU)
        score.max_subtasks = min(score.max_subtasks, int(sc.get("max_subtasks_cap", 1000)))
        score.max_phases = min(score.max_phases, int(sc.get("max_phases_cap", 200)))

        # Log if memory pressure is high
        if hw.should_queue_tasks():
            logger.warning(
                f"⚠️ High memory pressure ({hw.memory_pressure():.0%}). "
                f"Parallel tasks reduced to {safe_workers} to prevent OOM."
            )
    except Exception:
        pass
