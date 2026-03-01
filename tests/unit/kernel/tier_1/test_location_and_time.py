from datetime import UTC, datetime

from kernel.location_and_time.engine import (
    extract_spatial_signals,
    extract_temporal_signals,
    resolve_temporal_hierarchy,
)
from kernel.location_and_time.types import (
    SpatialSignalType,
    TemporalSignalType,
)


def test_extract_temporal_signals():
    now = datetime.now(UTC)
    text = "I need to schedule a meeting for tomorrow or maybe next week."
    signals = extract_temporal_signals(text, now)

    assert len(signals) == 2
    parsed_values = [s.parsed_value for s in signals]
    assert "tomorrow" in parsed_values
    assert "next_week" in parsed_values


def test_extract_absolute_date():
    now = datetime.now(UTC)
    text = "The deadline is 2024-12-31."
    signals = extract_temporal_signals(text, now)

    assert len(signals) == 1
    assert signals[0].signal_type == TemporalSignalType.ABSOLUTE
    assert signals[0].raw_text == "2024-12-31"


def test_extract_spatial_signals():
    text = "Are there any good restaurants nearby in San Francisco?"
    signals = extract_spatial_signals(text, None)

    # "nearby" -> HINT
    # "in San Francisco" -> EXPLICIT
    assert len(signals) >= 2
    types = [s.signal_type for s in signals]
    assert SpatialSignalType.HINT in types
    assert SpatialSignalType.EXPLICIT in types


def test_resolve_temporal_hierarchy():
    now = datetime.now(UTC)
    text = "Let's review this tomorrow."
    signals = extract_temporal_signals(text, now)

    range_result = resolve_temporal_hierarchy(signals, now)

    assert range_result.confidence > 0.0
    assert range_result.start is not None
    assert range_result.end is not None

    # 'tomorrow' resolution sanity check based on absolute diff
    # Tomorrow starts roughly today/tomorrow depending on the -24h mapping logic
    time_diff = range_result.end - range_result.start
    assert time_diff.total_seconds() > 0
