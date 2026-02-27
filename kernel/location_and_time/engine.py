"""
Tier 1 Location & Time — Engine.

Spatiotemporal anchoring pipeline:
    1. Extract temporal and spatial signals from text
    2. Resolve hierarchies (relative → UTC, place → bounding box)
    3. Adaptive adjustment (domain-aware scoping)
    4. Hybrid fusion (merge time + space with confidence)
"""

from __future__ import annotations

import json
import re
import time
from datetime import datetime, timedelta

from shared.config import get_settings
from shared.inference_kit import InferenceKit
from shared.llm.provider import LLMMessage
from shared.logging.main import get_logger
from shared.standard_io import (
    Metrics,
    ModuleRef,
    Result,
    create_data_signal,
    fail,
    ok,
    processing_error,
)

from .types import (
    GeoAnchor,
    SpatialBounds,
    SpatialSignal,
    SpatialSignalType,
    SpatiotemporalBlock,
    TemporalRange,
    TemporalSignal,
    TemporalSignalType,
)

log = get_logger(__name__)

_MODULE = "location_and_time"
_TIER = 1


def _ref(fn: str) -> ModuleRef:
    return ModuleRef(tier=_TIER, module=_MODULE, function=fn)


# ============================================================================
# Temporal Signal Extraction
# ============================================================================

_RELATIVE_PATTERNS: dict[str, re.Pattern[str]] = {
    "yesterday": re.compile(r"\byesterday\b", re.IGNORECASE),
    "today": re.compile(r"\btoday\b", re.IGNORECASE),
    "tomorrow": re.compile(r"\btomorrow\b", re.IGNORECASE),
    "last_week": re.compile(r"\blast\s+week\b", re.IGNORECASE),
    "this_week": re.compile(r"\bthis\s+week\b", re.IGNORECASE),
    "next_week": re.compile(r"\bnext\s+week\b", re.IGNORECASE),
    "last_month": re.compile(r"\blast\s+month\b", re.IGNORECASE),
    "this_month": re.compile(r"\bthis\s+month\b", re.IGNORECASE),
    "recently": re.compile(r"\brecently\b", re.IGNORECASE),
    "now": re.compile(r"\bright?\s*now\b", re.IGNORECASE),
    "last_hour": re.compile(r"\blast\s+hour\b", re.IGNORECASE),
}

_ABSOLUTE_DATE_PATTERN = re.compile(
    r"\b(\d{4}-\d{2}-\d{2})\b"
    r"|(\b\d{1,2}/\d{1,2}/\d{2,4}\b)"
    r"|(\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+\d{1,2},?\s*\d{4}\b)",
    re.IGNORECASE,
)


def extract_temporal_signals(
    text: str,
    system_time: datetime,
) -> list[TemporalSignal]:
    """Extract temporal references from raw text."""
    signals: list[TemporalSignal] = []

    # Relative patterns
    for key, pattern in _RELATIVE_PATTERNS.items():
        for match in pattern.finditer(text):
            signals.append(TemporalSignal(
                signal_type=TemporalSignalType.RELATIVE,
                raw_text=match.group(),
                start_offset=match.start(),
                end_offset=match.end(),
                parsed_value=key,
            ))

    # Absolute date patterns
    for match in _ABSOLUTE_DATE_PATTERN.finditer(text):
        signals.append(TemporalSignal(
            signal_type=TemporalSignalType.ABSOLUTE,
            raw_text=match.group(),
            start_offset=match.start(),
            end_offset=match.end(),
        ))

    return signals


# ============================================================================
# Spatial Signal Extraction
# ============================================================================

_SPATIAL_HINT_PATTERNS = re.compile(
    r"\b(nearby|near\s+me|around\s+here|close\s+by|local)\b",
    re.IGNORECASE,
)


def extract_spatial_signals(
    text: str,
    geo_anchor: GeoAnchor | None,
) -> list[SpatialSignal]:
    """Identify location references in text."""
    signals: list[SpatialSignal] = []

    # Directional hints
    for match in _SPATIAL_HINT_PATTERNS.finditer(text):
        signals.append(SpatialSignal(
            signal_type=SpatialSignalType.HINT,
            raw_text=match.group(),
            start_offset=match.start(),
            end_offset=match.end(),
        ))

    # Named places: look for capitalized multi-word sequences
    place_pattern = re.compile(r"\b(?:in|at|near|from|to)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b")
    for match in place_pattern.finditer(text):
        place_name = match.group(1)
        signals.append(SpatialSignal(
            signal_type=SpatialSignalType.EXPLICIT,
            raw_text=place_name,
            start_offset=match.start(1),
            end_offset=match.end(1),
        ))

    return signals


# ============================================================================
# Temporal Resolution
# ============================================================================


def resolve_temporal_hierarchy(
    signals: list[TemporalSignal],
    system_time: datetime,
) -> TemporalRange:
    """Convert extracted signals into a concrete UTC time range."""
    if not signals:
        # No temporal signals → use a wide default range
        return TemporalRange(
            start=system_time - timedelta(days=7),
            end=system_time,
            confidence=0.3,
        )

    # Process the most specific signal first
    ranges: list[TemporalRange] = []
    for signal in signals:
        resolved = _resolve_single_temporal(signal, system_time)
        if resolved:
            ranges.append(resolved)

    if not ranges:
        return TemporalRange(
            start=system_time - timedelta(days=7),
            end=system_time,
            confidence=0.3,
        )

    # Merge: use the tightest range
    best = max(ranges, key=lambda r: r.confidence)
    return best


def _resolve_single_temporal(
    signal: TemporalSignal,
    system_time: datetime,
) -> TemporalRange | None:
    """Resolve a single temporal signal against system time."""
    key = signal.parsed_value or ""

    _relative_offsets: dict[str, tuple[timedelta, timedelta]] = {
        "now": (timedelta(hours=0), timedelta(hours=0)),
        "today": (timedelta(hours=0), timedelta(hours=24)),
        "yesterday": (timedelta(hours=24), timedelta(hours=0)),
        "tomorrow": (timedelta(hours=0), timedelta(hours=24)),
        "last_hour": (timedelta(hours=1), timedelta(hours=0)),
        "last_week": (timedelta(weeks=1), timedelta(hours=0)),
        "this_week": (timedelta(days=system_time.weekday()), timedelta(hours=0)),
        "next_week": (timedelta(hours=0), timedelta(weeks=1)),
        "last_month": (timedelta(days=30), timedelta(hours=0)),
        "this_month": (timedelta(days=system_time.day - 1), timedelta(hours=0)),
        "recently": (timedelta(days=7), timedelta(hours=0)),
    }

    if key in _relative_offsets:
        back, forward = _relative_offsets[key]
        start = system_time - back
        end = system_time + forward if forward else system_time
        confidence = 0.9 if key not in ("recently",) else 0.6
        return TemporalRange(
            start=start,
            end=end,
            confidence=confidence,
            source_signals=[signal.raw_text],
        )

    # Absolute date parsing
    if signal.signal_type == TemporalSignalType.ABSOLUTE:
        try:
            for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y"):
                try:
                    parsed = datetime.strptime(signal.raw_text.strip(), fmt)
                    return TemporalRange(
                        start=parsed,
                        end=parsed + timedelta(days=1),
                        confidence=0.95,
                        source_signals=[signal.raw_text],
                    )
                except ValueError:
                    continue
        except Exception:
            pass

    return None


# ============================================================================
# Spatial Resolution
# ============================================================================


def resolve_spatial_hierarchy(
    signals: list[SpatialSignal],
    geo_anchor: GeoAnchor | None,
) -> SpatialBounds:
    """Map spatial signals to geographic bounding boxes."""
    if not signals and not geo_anchor:
        # Global scope
        return SpatialBounds(confidence=0.1, label="global")

    if not signals and geo_anchor:
        # Use anchor with default scope
        settings = get_settings().kernel
        default_scope = settings.spatial_scope_multipliers.get("default", 0.1)
        return SpatialBounds(
            min_lat=geo_anchor.latitude - default_scope,
            max_lat=geo_anchor.latitude + default_scope,
            min_lon=geo_anchor.longitude - default_scope,
            max_lon=geo_anchor.longitude + default_scope,
            confidence=0.5,
            label=geo_anchor.label or "anchor",
        )

    # Use the most explicit signal
    best_signal = None
    for signal in signals:
        if signal.signal_type == SpatialSignalType.EXPLICIT:
            best_signal = signal
            break
    if not best_signal:
        best_signal = signals[0]

    if best_signal.signal_type == SpatialSignalType.HINT and geo_anchor:
        settings = get_settings().kernel
        scope = settings.spatial_scope_multipliers.get("default", 0.1)
        return SpatialBounds(
            min_lat=geo_anchor.latitude - scope,
            max_lat=geo_anchor.latitude + scope,
            min_lon=geo_anchor.longitude - scope,
            max_lon=geo_anchor.longitude + scope,
            confidence=0.6,
            label=best_signal.raw_text,
        )

    # Named place: return a wide approximation
    return SpatialBounds(
        confidence=0.4,
        label=best_signal.raw_text,
    )


# ============================================================================
# Adaptive Adjustment
# ============================================================================


def adapt_temporal_ambiguity(
    temporal_range: TemporalRange,
    task_context: str,
) -> TemporalRange:
    """Adjust ambiguous temporal terms based on task domain."""
    settings = get_settings().kernel
    context_lower = task_context.lower()

    # Find matching domain
    for domain, seconds in settings.temporal_recency_mappings.items():
        if domain in context_lower:
            adjusted_start = temporal_range.end - timedelta(seconds=seconds)
            if adjusted_start > temporal_range.start:
                return TemporalRange(
                    start=adjusted_start,
                    end=temporal_range.end,
                    confidence=temporal_range.confidence * 0.9,
                    source_signals=temporal_range.source_signals,
                )
            break

    return temporal_range


def adapt_spatial_scope(
    spatial_bounds: SpatialBounds,
    task_context: str,
) -> SpatialBounds:
    """Widen or narrow spatial bounding box based on task requirements."""
    settings = get_settings().kernel
    context_lower = task_context.lower()

    for domain, multiplier in settings.spatial_scope_multipliers.items():
        if domain in context_lower:
            center_lat = (spatial_bounds.min_lat + spatial_bounds.max_lat) / 2
            center_lon = (spatial_bounds.min_lon + spatial_bounds.max_lon) / 2
            return SpatialBounds(
                min_lat=max(-90.0, center_lat - multiplier),
                max_lat=min(90.0, center_lat + multiplier),
                min_lon=max(-180.0, center_lon - multiplier),
                max_lon=min(180.0, center_lon + multiplier),
                confidence=spatial_bounds.confidence,
                label=spatial_bounds.label,
            )

    return spatial_bounds


# ============================================================================
# Spatiotemporal Fusion
# ============================================================================


def fuse_spatiotemporal(
    temporal: TemporalRange,
    spatial: SpatialBounds,
) -> SpatiotemporalBlock:
    """Merge resolved temporal and spatial dimensions into unified block."""
    # Combined confidence: geometric mean of individual confidences
    fusion_confidence = (temporal.confidence * spatial.confidence) ** 0.5

    return SpatiotemporalBlock(
        temporal=temporal,
        spatial=spatial,
        fusion_confidence=fusion_confidence,
    )


# ============================================================================
# Top-Level Orchestrator
# ============================================================================


async def anchor_spatiotemporal(
    text: str,
    system_time: datetime,
    geo_anchor: GeoAnchor | None = None,
    task_context: str = "",
    kit: InferenceKit | None = None,
) -> Result:
    """Top-level spatiotemporal orchestrator.

    Extracts, resolves, adapts, and fuses temporal and spatial signals
    into a rigid SpatiotemporalBlock for Tier 2 consumption.
    """
    ref = _ref("anchor_spatiotemporal")
    start_perf = time.perf_counter()

    try:
        # Step 1: Extract signals
        temporal_signals = extract_temporal_signals(text, system_time)
        spatial_signals = extract_spatial_signals(text, geo_anchor)

        # Step 2: Resolve hierarchies
        temporal = resolve_temporal_hierarchy(temporal_signals, system_time)
        spatial = resolve_spatial_hierarchy(spatial_signals, geo_anchor)

        # Step 3: Adaptive adjustment
        if task_context:
            temporal = adapt_temporal_ambiguity(temporal, task_context)
            spatial = adapt_spatial_scope(spatial, task_context)

        # Step 4: LLM refinement
        if kit and kit.has_llm:
            try:
                system_msg = LLMMessage(
                    role="system",
                    content=(
                        "Extract precise temporal ranges or spatial locations. If no precise info exists, return blank fields. "
                        "Respond EXACTLY with JSON: {\"temporal\": {\"start\": \"YYYY-MM-DDTHH:MM:SSZ\", \"end\": \"...\"}, \"spatial\": {\"min_lat\": float, \"max_lat\": float, \"min_lon\": float, \"max_lon\": float}}"
                    )
                )
                user_msg = LLMMessage(role="user", content=f"Text: {text}\nCurrent Time: {system_time.isoformat()}\nContext: {task_context}")
                resp = await kit.llm.complete([system_msg, user_msg], kit.llm_config)

                content = resp.content.strip()
                if content.startswith("```json"):
                    content = content[7:-3].strip()
                elif content.startswith("```"):
                    content = content[3:-3].strip()
                data = json.loads(content)

                temp_data = data.get("temporal")
                if temp_data and "start" in temp_data and "end" in temp_data:
                    try:
                        start = datetime.fromisoformat(temp_data["start"].replace("Z", "+00:00"))
                        end = datetime.fromisoformat(temp_data["end"].replace("Z", "+00:00"))
                        temporal = TemporalRange(start=start, end=end, confidence=0.9, source_signals=["LLM Extracted"])
                    except Exception:
                        pass

                spat_data = data.get("spatial")
                if spat_data and all(k in spat_data for k in ["min_lat", "max_lat", "min_lon", "max_lon"]):
                    try:
                        spatial = SpatialBounds(
                            min_lat=float(spat_data["min_lat"]),
                            max_lat=float(spat_data["max_lat"]),
                            min_lon=float(spat_data["min_lon"]),
                            max_lon=float(spat_data["max_lon"]),
                            confidence=0.9,
                            label="LLM Extracted"
                        )
                    except Exception:
                        pass
            except Exception as e:
                log.warning("LLM spatiotemporal extraction failed", error=str(e))
                pass

        # Step 5: Fusion
        block = fuse_spatiotemporal(temporal, spatial)

        elapsed = (time.perf_counter() - start_perf) * 1000
        metrics = Metrics(duration_ms=elapsed, module_ref=ref)

        signal = create_data_signal(
            data=block.model_dump(mode="json"),
            schema="SpatiotemporalBlock",
            origin=ref,
            trace_id="",
            tags={
                "has_temporal": str(block.temporal is not None),
                "has_spatial": str(block.spatial is not None),
                "confidence": f"{block.fusion_confidence:.2f}",
            },
        )

        log.info(
            "Spatiotemporal anchoring complete",
            temporal_signals=len(temporal_signals),
            spatial_signals=len(spatial_signals),
            confidence=round(block.fusion_confidence, 3),
            duration_ms=round(elapsed, 2),
        )

        return ok(signals=[signal], metrics=metrics)

    except Exception as exc:
        elapsed = (time.perf_counter() - start_perf) * 1000
        metrics = Metrics(duration_ms=elapsed, module_ref=ref)
        error = processing_error(
            message=f"Spatiotemporal anchoring failed: {exc}",
            source=ref,
            detail={"error_type": type(exc).__name__},
        )
        log.error("Spatiotemporal anchoring failed", error=str(exc))
        return fail(error=error, metrics=metrics)
