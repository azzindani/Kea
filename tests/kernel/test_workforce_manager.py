import pytest
from kernel.workforce_manager.engine import (
    match_specialist,
    evaluate_performance,
    compute_scale_decisions
)
from kernel.workforce_manager.types import (
    MissionChunk,
    AgentHandle,
    WorkforcePool,
    AgentStatus,
    PerformanceSnapshot,
    ScaleAction
)

@pytest.mark.asyncio
async def test_match_specialist(inference_kit):
    """Test matching a mission chunk to a specialist profile."""
    chunk = MissionChunk(
        chunk_id="chk-123",
        parent_objective_id="obj-001",
        domain="database",
        sub_objective="Optimize for high read throughput",
        required_skills=["sql", "database_optimization", "distributed_systems"]
    )
    
    available_profiles = [
        {"profile_id": "prof-1", "role_name": "Frontend Developer", "skills": ["react", "typescript", "css"]},
        {"profile_id": "prof-2", "role_name": "Database Architect", "skills": ["sql", "postgres", "distributed_systems", "indexing"]},
        {"profile_id": "prof-3", "role_name": "DevOps Engineer", "skills": ["docker", "kubernetes", "aws"]}
    ]
    
    result = await match_specialist(chunk, available_profiles, kit=inference_kit)
    assert result.is_success
    
    match_data = result.signals[0].body["data"]
    print(f"\n\033[1;36m[WORKFORCE MATCH]\033[0m Chunk: {chunk.sub_objective}")
    print(f"   -> Best Profile ID: {match_data['agent_profile_id']}")
    print(f"   -> Match Score: {match_data['composite_score']:.2f}")
    
    assert match_data['agent_profile_id'] == "prof-2"
    assert match_data['composite_score'] > 0.5

def test_evaluate_performance():
    """Test extracting performance metrics from a result dict."""
    handle = AgentHandle(
        agent_id="agent-007", 
        profile_id="prof-1",
        chunk_id="chk-123",
        role_name="Security Specialist"
    )
    mock_result = {
        "status": "completed",
        "quality_score": 0.9,
        "confidence": 0.85,
        "grounding_rate": 0.95,
        "duration_ms": 2500.0,
        "cost": 0.05,
        "success": True
    }
    
    perf = evaluate_performance(handle, mock_result)
    
    print(f"\n\033[1;32m[PERFORMANCE EVALUATION]\033[0m Agent: {handle.agent_id}")
    print(f"   -> Latency: {perf.latency_ms}ms | Cost: {perf.cost}")
    
    assert perf.agent_id == "agent-007"
    assert perf.quality_score == 0.9
    assert perf.latency_ms == 2500.0

def test_compute_scale_decisions():
    """Test the pure-logic scaling computation."""
    pool = WorkforcePool(
        pool_id="pool-1",
        mission_id="mission-1",
        agents={
            "a1": AgentHandle(agent_id="a1", profile_id="prof-1", chunk_id="c0", status=AgentStatus.ACTIVE)
        },
        budget_remaining=10.0
    )
    
    pending_chunks = [
        MissionChunk(chunk_id="c1", parent_objective_id="o1", domain="d", sub_objective="s1"),
        MissionChunk(chunk_id="c2", parent_objective_id="o1", domain="d", sub_objective="s2"),
        MissionChunk(chunk_id="c3", parent_objective_id="o1", domain="d", sub_objective="s3")
    ]
    
    performance = [
        PerformanceSnapshot(agent_id="a1", quality_score=0.9, cost=0.01)
    ]
    
    hardware = {"safe_parallel_limit": 5}
    
    decisions = compute_scale_decisions(pool, pending_chunks, performance, hardware)
    
    print(f"\n\033[1;33m[SCALING DECISION]\033[0m Pending: {len(pending_chunks)} | Active: 1")
    for d in decisions:
        print(f"   -> Action: {d.action} | Target Chunk: {d.target_chunk_id}")
    
    assert len(decisions) > 0
    assert any(d.action == ScaleAction.HIRE_MORE for d in decisions)

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
