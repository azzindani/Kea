import pytest

from kernel.location_and_time.engine import (
    extract_temporal_signals,
    extract_spatial_signals,
    resolve_to_utc_ranges,
    resolve_to_bounding_boxes,
    adapt_to_task_context,
    fuse_spatiotemporal_block,
    run_spatiotemporal_anchoring
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
async def test_location_and_time_comprehensive(input_text):
    """REAL SIMULATION: Verify Location & Time Kernel functions with multiple spatiotemporal inputs."""
    print(f"\n--- Testing Location & Time: Text='{input_text}' ---")

    print(f"\n[Test]: extract_temporal_signals")
    temporal_signals = extract_temporal_signals(input_text)
    assert isinstance(temporal_signals, list)
    print(f"   Temporal Signals found: {len(temporal_signals)}")
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: extract_spatial_signals")
    spatial_signals = extract_spatial_signals(input_text)
    assert isinstance(spatial_signals, list)
    print(f"   Spatial Signals found: {len(spatial_signals)}")
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: resolve_to_utc_ranges")
    utc_ranges = resolve_to_utc_ranges(temporal_signals)
    assert isinstance(utc_ranges, list)
    print(f"   UTC Ranges resolved: {len(utc_ranges)}")
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: resolve_to_bounding_boxes")
    bounding_boxes = resolve_to_bounding_boxes(spatial_signals)
    assert isinstance(bounding_boxes, list)
    print(f"   Bounding Boxes resolved: {len(bounding_boxes)}")
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: adapt_to_task_context")
    # Simulate adaptation with a dummy context
    adapted_ranges, adapted_boxes = adapt_to_task_context(utc_ranges, bounding_boxes, "report_generation")
    assert len(adapted_ranges) == len(utc_ranges)
    assert len(adapted_boxes) == len(bounding_boxes)
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: fuse_spatiotemporal_block")
    st_block = fuse_spatiotemporal_block(adapted_ranges, adapted_boxes)
    assert st_block is not None
    assert hasattr(st_block, 'timestamp_utc')
    print(f"   Fused Timestamp: {st_block.timestamp_utc}")
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: run_spatiotemporal_anchoring")
    res = await run_spatiotemporal_anchoring(input_text, kit=None)
    assert res.is_success
    print(f" \033[92m[SUCCESS]\033[0m")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
