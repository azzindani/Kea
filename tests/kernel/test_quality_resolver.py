import pytest
from kernel.quality_resolver.engine import (
    detect_conflicts,
    resolve_conflict,
    score_sprint_quality
)
from kernel.quality_resolver.types import Conflict, Resolution, QualityAudit

@pytest.mark.asyncio
async def test_detect_conflicts(inference_kit):
    """Test detecting semantic contradictions between agent artifacts."""
    artifacts = [
        {"id": "art-1", "agent": "Alice", "content": "The system must use an async Postgres driver."},
        {"id": "art-2", "agent": "Bob", "content": "The system should use a synchronous SQLite database for simplicity."},
        {"id": "art-3", "agent": "Charlie", "content": "Async Postgres is the best choice for scaling."}
    ]
    
    result = await detect_conflicts(artifacts, kit=inference_kit)
    assert result.is_success
    
    conflicts = result.signals[0].body["data"]["conflicts"]
    print(f"\n\033[1;31m[CONFLICT DETECTION]\033[0m Artifacts: {len(artifacts)}")
    for c in conflicts:
        print(f"   -> Found: {c['description']}")
    
    # Alice and Bob clearly conflict on Async/Sync and DB type
    assert len(conflicts) > 0

@pytest.mark.asyncio
async def test_resolve_conflict(inference_kit):
    """Test resolving a detected conflict via weighted consensus."""
    conflict = Conflict(
        artifact_a_id="art-1",
        artifact_b_id="art-2",
        description="Async Postgres vs Sync SQLite",
        severity="high"
    )
    
    art_a = {
        "artifact_id": "art-1", 
        "metadata": {"confidence": 0.9, "quality_score": 0.9}
    }
    art_b = {
        "artifact_id": "art-2", 
        "metadata": {"confidence": 0.6, "quality_score": 0.6}
    }
    
    result = await resolve_conflict(conflict, art_a, art_b, kit=inference_kit)
    assert result.is_success
    
    resolution = result.signals[0].body["data"]
    print(f"\n\033[1;33m[CONFLICT RESOLUTION]\033[0m {conflict.description}")
    print(f"   -> Winner ID: {resolution['winning_artifact_id']}")
    print(f"   -> Strategy: {resolution.get('strategy_used', 'consensus')}")
    
    # Alice has higher confidence, she should win
    assert resolution['winning_artifact_id'] == "art-1"

@pytest.mark.asyncio
async def test_score_sprint_quality(inference_kit):
    """Test generating a quality score for an entire sprint's results."""
    agent_results = [
        {"quality_score": 0.9, "confidence": 0.85, "grounding_rate": 0.95},
        {"quality_score": 0.8, "confidence": 0.9, "grounding_rate": 0.88},
        {"quality_score": 0.4, "confidence": 0.5, "grounding_rate": 0.3}  # One outlier
    ]
    
    result = await score_sprint_quality(agent_results, sprint_id="sprint_beta", kit=inference_kit)
    assert result.is_success
    
    audit = result.signals[0].body["data"]
    print(f"\n\033[1;32m[SPRINT QUALITY AUDIT]\033[0m Sprint: {audit['sprint_id']}")
    print(f"   -> Overall Score: {audit['avg_quality']:.2f}")
    print(f"   -> Verdict: {audit['overall']}")
    
    assert audit['avg_quality'] < 0.8  # Pull down by the third result
    assert audit['overall'] in ["pass", "warning", "fail"]

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
