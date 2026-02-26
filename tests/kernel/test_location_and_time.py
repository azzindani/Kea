import pytest

from kernel.location_and_time.engine import (
    extract_temporal_signals,
    extract_spatial_signals,
    resolve_temporal_hierarchy,
    resolve_spatial_hierarchy,
    adapt_temporal_ambiguity,
    adapt_spatial_scope,
    fuse_spatiotemporal,
    anchor_spatiotemporal
)
from shared.config import get_settings


@pytest.mark.asyncio
@pytest.mark.parametrize("input_text", [
    "Find sales in London yesterday.",
    "Schedule a recurring check for inventory in Tokyo every Monday morning.",
    "Search for historical documents in Rome from the 1st century.",
    "Identify current weather in New York City.",
    ""
])
async def test_location_and_time_comprehensive(input_text, inference_kit):
    """REAL SIMULATION: Verify Location & Time Kernel functions with multiple spatiotemporal inputs."""
    print(f"\n--- Testing Location & Time: Text='{input_text}' ---")

    from datetime import datetime
    now = datetime.now()

    print(f"\n[Test]: extract_temporal_signals")
    print(f"   [INPUT]: text='{input_text}', now='{now}'")
    temporal_signals = extract_temporal_signals(input_text, now)
    assert isinstance(temporal_signals, list)
    print(f"   [OUTPUT]: Temporal Signals found count={len(temporal_signals)}")
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: extract_spatial_signals")
    print(f"   [INPUT]: text='{input_text}'")
    spatial_signals = extract_spatial_signals(input_text, None)
    assert isinstance(spatial_signals, list)
    print(f"   [OUTPUT]: Spatial Signals found count={len(spatial_signals)}")
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: resolve_temporal_hierarchy")
    print(f"   [INPUT]: {len(temporal_signals)} signals")
    temp_range = resolve_temporal_hierarchy(temporal_signals, now)
    assert temp_range is not None
    print(f"   [OUTPUT]: Temporal range resolved")
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: resolve_spatial_hierarchy")
    print(f"   [INPUT]: {len(spatial_signals)} signals")
    from kernel.location_and_time.types import GeoAnchor
    bounds = resolve_spatial_hierarchy(spatial_signals, GeoAnchor(latitude=0, longitude=0))
    assert bounds is not None
    print(f"   [OUTPUT]: Spatial hierarchy resolved")
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: fuse_spatiotemporal")
    print(f"   [INPUT]: Temporal range, Spatial bounds")
    st_block = fuse_spatiotemporal(temp_range, bounds)
    assert st_block is not None
    print(f"   [OUTPUT]: Spatiotemporal fusion complete")
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: anchor_spatiotemporal")
    print(f"   [INPUT]: text='{input_text}'")
    res = await anchor_spatiotemporal(input_text, now, kit=inference_kit)
    assert res.is_success
    print(f"   [OUTPUT]: Status={res.status}, Signals count={len(res.signals)}")
    print(f" \033[92m[SUCCESS]\033[0m")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
