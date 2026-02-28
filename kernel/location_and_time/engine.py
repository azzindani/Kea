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
from shared.knowledge import load_system_knowledge
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
    GeographicScope,
    SpatialBounds,
    SpatialSignal,
    SpatialSignalType,
    SpatiotemporalBlock,
    TemporalRange,
    TemporalSignal,
    TemporalSignalType,
    TimeGranularity,
)

_GEO_REGIONS = load_system_knowledge("geo_regions.yaml")
_GEO_CITIES = load_system_knowledge("geo_cities.yaml")

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
    # Complex relative patterns
    "last_x_days": re.compile(r"\blast\s+(\d+)\s+days?\b", re.IGNORECASE),
    "last_x_weeks": re.compile(r"\blast\s+(\d+)\s+weeks?\b", re.IGNORECASE),
    "last_x_months": re.compile(r"\blast\s+(\d+)\s+months?\b", re.IGNORECASE),
    "last_x_years": re.compile(r"\blast\s+(\d+)\s+years?\b", re.IGNORECASE),
    "last_x_decades": re.compile(r"\blast\s+(\d+)\s+decades?\b", re.IGNORECASE),
    "last_decade": re.compile(r"\blast\s+decade\b", re.IGNORECASE),
    "last_semester": re.compile(r"\blast\s+semester\b", re.IGNORECASE),
    "quarterly": re.compile(r"\b(q[1-4])\b\s*(?:\d{4})?", re.IGNORECASE),
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
                parsed_value=f"{key}:{match.group(1)}" if "x" in key or key == "quarterly" else key,
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

    # 2. Named places: look for capitalized multi-word sequences
    place_pattern = re.compile(r"\b(?:in|at|near|from|to)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b")
    for match in place_pattern.finditer(text):
        place_name = match.group(1)
        signals.append(SpatialSignal(
            signal_type=SpatialSignalType.EXPLICIT,
            raw_text=place_name,
            start_offset=match.start(1),
            end_offset=match.end(1),
        ))

    # 3. Macro-regions from knowledge
    regions_map = _GEO_REGIONS.get("regions", {})
    orgs_map = _GEO_REGIONS.get("organizations", {})
    all_macro = {**regions_map, **orgs_map}
    
    for key, info in all_macro.items():
        pattern = re.compile(rf"\b{key}\b", re.IGNORECASE)
        for match in pattern.finditer(text):
            signals.append(SpatialSignal(
                signal_type=SpatialSignalType.EXPLICIT,
                raw_text=match.group(),
                start_offset=match.start(),
                end_offset=match.end(),
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

    # Complex relative logic
    if ":" in key:
        base_key, value_str = key.split(":", 1)
        try:
            val = int(value_str)
        except ValueError:
            val = 1 # Fallback for non-numeric groups if any

        start = system_time
        end = system_time
        granularity = TimeGranularity.UNDEFINED
        labels = []

        if base_key == "last_x_days":
            start = system_time - timedelta(days=val)
            granularity = TimeGranularity.DAY
            labels = [(system_time - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(val)]
        elif base_key == "last_x_weeks":
            start = system_time - timedelta(weeks=val)
            granularity = TimeGranularity.WEEK
            labels = [f"Week {(system_time - timedelta(weeks=i)).isocalendar()[1]}" for i in range(val)]
        elif base_key == "last_x_months":
            # Rough approximation: 30 days per month
            start = system_time - timedelta(days=30 * val)
            granularity = TimeGranularity.MONTH
            # Generate Month-Year labels
            curr = system_time
            for _ in range(val):
                labels.append(curr.strftime("%b %Y"))
                # Go back 1 month
                if curr.month == 1:
                    curr = curr.replace(year=curr.year-1, month=12)
                else:
                    curr = curr.replace(month=curr.month-1)
        elif base_key == "last_x_years":
            start = system_time.replace(year=system_time.year - val)
            granularity = TimeGranularity.YEAR
            labels = [str(system_time.year - i) for i in range(val)]
        elif base_key == "last_x_decades":
            start = system_time.replace(year=system_time.year - 10 * val)
            granularity = TimeGranularity.DECADE
            labels = [f"{system_time.year - 10*i - 10}-{system_time.year - 10*i}" for i in range(val)]
        elif base_key == "quarterly":
            q_num = int(value_str.lower().strip("q"))
            curr_year = system_time.year
            # Q1: Jan-Mar, Q2: Apr-Jun, Q3: Jul-Sep, Q4: Oct-Dec
            q_starts = {1: 1, 2: 4, 3: 7, 4: 10}
            start = datetime(curr_year, q_starts[q_num], 1)
            end = (start + timedelta(days=92)).replace(day=1) # Roughly 3 months
            granularity = TimeGranularity.QUARTER
            labels = [f"Q{q_num} {curr_year}"]

        return TemporalRange(
            start=start,
            end=end,
            granularity=granularity,
            granular_labels=labels,
            confidence=0.9,
            source_signals=[signal.raw_text],
        )
    
    # Static but semantic relative keys
    if key == "last_decade":
        return TemporalRange(
            start=system_time.replace(year=system_time.year - 10),
            end=system_time,
            granularity=TimeGranularity.DECADE,
            granular_labels=[f"{system_time.year-10}-{system_time.year}"],
            confidence=0.9,
            source_signals=[signal.raw_text]
        )
    if key == "last_semester":
        return TemporalRange(
            start=system_time - timedelta(days=182),
            end=system_time,
            granularity=TimeGranularity.SEMESTER,
            granular_labels=["Last 6 Months"],
            confidence=0.8,
            source_signals=[signal.raw_text]
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


async def resolve_spatial_hierarchy(
    signals: list[SpatialSignal],
    geo_anchor: GeoAnchor | None,
) -> SpatialBounds:
    """Map spatial signals to geographic bounding boxes.
    
    Resolution Tiers:
    0. Knowledge Base (High speed cache)
    1. External Map Provider (Google/Nominatim)
    2. LLM Reasoning (Estimation)
    """
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
            scope=GeographicScope.POINT,
            confidence=0.5,
            label=geo_anchor.label or "anchor",
        )

    # Resolution Tier 0: City Knowledge (High Precision Cache)
    cities_map = _GEO_CITIES.get("cities", {})
    for signal in signals:
        name = signal.raw_text.strip()
        if name in cities_map:
            info = cities_map[name]
            return SpatialBounds(
                min_lat=info["lat"] - 0.05,
                max_lat=info["lat"] + 0.05,
                min_lon=info["lon"] - 0.05,
                max_lon=info["lon"] + 0.05,
                scope=GeographicScope.CITY,
                label=f"{name}, {info['country']}",
                confidence=0.95
            )

    # Resolution Tier 1: External Map Provider (e.g., Google, Nominatim)
    # We try to resolve using the configured provider for addresses not in cache
    for signal in signals:
        if signal.signal_type == SpatialSignalType.EXPLICIT:
            external_res = await _resolve_spatial_external(signal.raw_text)
            if external_res:
                return external_res

    # Resolution Tier 2: Macro-regions
    regions_map = _GEO_REGIONS.get("regions", {})
    orgs_map = _GEO_REGIONS.get("organizations", {})
    all_macro = {**regions_map, **orgs_map}

    for signal in signals:
        key = signal.raw_text.upper()
        if key in all_macro:
            info = all_macro[key]
            return SpatialBounds(
                scope=GeographicScope(info.get("scope", "region")),
                constituent_labels=info.get("constituents", []),
                confidence=0.9,
                label=info.get("label", key)
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

    # Named place: return a wide approximation (LLM will usually refine this later)
    return SpatialBounds(
        confidence=0.4,
        label=best_signal.raw_text,
    )


async def _resolve_spatial_external(query: str) -> SpatialBounds | None:
    """Resolve a location using the configured external map provider."""
    settings = get_settings().kernel
    provider = settings.geocoding_provider
    api_key = settings.geocoding_api_key
    user_agent = settings.geocoding_user_agent

    try:
        from geopy.geocoders import Nominatim, GoogleV3, Bing, MapBox
        
        geocoder = None
        if provider == "nominatim":
            geocoder = Nominatim(user_agent=user_agent)
        elif provider == "google" and api_key:
            geocoder = GoogleV3(api_key=api_key)
        elif provider == "bing" and api_key:
            geocoder = Bing(api_key=api_key)
        elif provider == "mapbox" and api_key:
            geocoder = MapBox(api_key=api_key)

        if not geocoder:
            return None

        # Perform the actual lookup
        # Wrap in a thread pool since geopy is usually synchronous
        import asyncio
        loop = asyncio.get_event_loop()
        location = await loop.run_in_executor(None, lambda: geocoder.geocode(query, timeout=5))

        if location:
            # Determine scope based on location raw geometry or type if available
            # For simplicity, we assume explicit map matches are TOWN/CITY level or better
            return SpatialBounds(
                min_lat=location.latitude - 0.01,
                max_lat=location.latitude + 0.01,
                min_lon=location.longitude - 0.01,
                max_lon=location.longitude + 0.01,
                scope=GeographicScope.POINT,
                label=location.address,
                confidence=0.92
            )

    except (ImportError, Exception) as e:
        log.warning("External geocoding failed", provider=provider, query=query, error=str(e))
        return None

    return None


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
        spatial = await resolve_spatial_hierarchy(spatial_signals, geo_anchor)

        # Step 3: Adaptive adjustment
        if task_context:
            temporal = adapt_temporal_ambiguity(temporal, task_context)
            spatial = adapt_spatial_scope(spatial, task_context)

        # Step 4: Semantic Bridge (LLM Reasoning)
        # This connects Time & Location (e.g., local seasons, holidays, events)
        if kit and kit.has_llm:
            try:
                system_prompt = (
                    "You are the Kea Spatiotemporal Reasoning Engine. "
                    "Your goal is to connect Location and Time to resolve semantic ambiguities. "
                    "Consider:\n"
                    "1. Local Seasons: (e.g., Winter in Southern Hemisphere vs Northern).\n"
                    "2. Business Logic: (e.g., Weekends in Dubai vs NYC, local holidays).\n"
                    "3. Events: (e.g., 'During the last G20', 'After the Olympics').\n\n"
                    "Respond ONLY with a JSON block:\n"
                    "{\n"
                    "  \"reasoning\": \"string explaining the connection\",\n"
                    "  \"temporal\": {\"start\": \"ISO8601\", \"end\": \"ISO8601\", \"granularity\": \"day|week|month|year\", \"labels\": []},\n"
                    "  \"spatial\": {\"label\": \"string\", \"scope\": \"city|country|region\", \"constituents\": []}\n"
                    "}"
                )
                
                user_content = (
                    f"Query: '{text}'\n"
                    f"System Time: {system_time.isoformat()}\n"
                    f"Initial Resolution: Location={spatial.label}, Time={temporal.start} to {temporal.end}\n"
                    f"Context: {task_context}"
                )

                resp = await kit.llm.complete(
                    [LLMMessage(role="system", content=system_prompt),
                     LLMMessage(role="user", content=user_content)],
                    kit.llm_config
                )

                data = json.loads(resp.content.strip().strip("`").replace("json", ""))
                
                # Apply LLM Refinements if confidence is higher or rules were vague
                if "temporal" in data:
                    t = data["temporal"]
                    if t.get("start") and t.get("end"):
                        temporal = TemporalRange(
                            start=datetime.fromisoformat(t["start"].replace("Z", "+00:00")),
                            end=datetime.fromisoformat(t["end"].replace("Z", "+00:00")),
                            granularity=TimeGranularity(t.get("granularity", "undefined")),
                            granular_labels=t.get("labels", []),
                            confidence=0.95,
                            source_signals=[text, "LLM Reasoning"]
                        )
                
                if "spatial" in data:
                    s = data["spatial"]
                    if s.get("label"):
                        spatial.label = s["label"]
                        spatial.scope = GeographicScope(s.get("scope", "undefined"))
                        if s.get("constituents"):
                            spatial.constituent_labels = s["constituents"]
                        spatial.confidence = 0.95

                log.info("Semantic reasoning complete", reasoning=data.get("reasoning"))

            except Exception as e:
                log.warning("Semantic spatiotemporal reasoning failed", error=str(e))
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
