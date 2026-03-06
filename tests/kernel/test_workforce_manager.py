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
        description="Optimize a distributed SQL database for high read throughput.",
        required_skills=["sql", "database_optimization", "distributed_systems"]
    )
    
    available_profiles = [
        {"role_name": "Frontend Developer", "skills": ["react", "typescript", "css"]},
        {"role_name": "Database Architect", "skills": ["sql", "postgres", "distributed_systems", "indexing"]},
        {"role_name": "DevOps Engineer", "skills": ["docker", "kubernetes", "aws"]}
    ]
    
    result = await match_specialist(chunk, available_profiles, kit=inference_kit)
    assert result.is_success
    
    match_data = result.signals[0].body["data"]
    print(f"\n\033[1;36m[WORKFORCE MATCH]\033[0m Chunk: {chunk.description}")
    print(f"   -> Best Profile: {match_data['role_name']}")
    print(f"   -> Match Score: {match_data['score']:.2f}")
    
    assert match_data['role_name'] == "Database Architect"
    assert match_data['score'] > 0.5

def test_evaluate_performance():
    """Test extracting performance metrics from a result dict."""
    handle = AgentHandle(agent_id="agent-007", role="Security Specialist")
    mock_result = {
        "status": "completed",
        "metrics": {
            "total_tokens": 1500,
            "duration_ms": 2500.0,
            "cost_usd": 0.05
        },
        "success": True
    }
    
    perf = evaluate_performance(handle, mock_result)
    
    print(f"\n\033[1;32m[PERFORMANCE EVALUATION]\033[0m Agent: {handle.agent_id}")
    print(f"   -> Tokens: {perf.total_tokens} | Duration: {perf.total_duration_ms}ms")
    
    assert perf.agent_id == "agent-007"
    assert perf.status == AgentStatus.IDLE
    assert perf.total_tokens == 1500

def test_compute_scale_decisions():
    """Test the pure-logic scaling computation."""
    pool = WorkforcePool(
        agents=[AgentHandle(agent_id="a1", role="Dev", status=AgentStatus.BUSY)],
        max_size=5
    )
    
    pending_chunks = [
        MissionChunk(chunk_id="c1", description="Task 1"),
        MissionChunk(chunk_id="c2", description="Task 2"),
        MissionChunk(chunk_id="c3", description="Task 3")
    ]
    
    performance = [
        PerformanceSnapshot(agent_id="a1", status=AgentStatus.BUSY, total_tokens=100, total_duration_ms=100.0, total_cost=0.01)
    ]
    
    hardware = {"cpu_usage": 0.3, "memory_usage": 0.4}
    
    decision_result = compute_scale_decisions(pool, pending_chunks, performance, hardware)
    
    print(f"\n\033[1;33m[SCALING DECISION]\033[0m Pending: {len(pending_chunks)} | Active: 1")
    print(f"   -> Action: {decision_result.action}")
    print(f"   -> Count: {decision_result.count}")
    
    # With 3 pending tasks and only 1 busy agent, we should probably hire more.
    assert decision_result.action == ScaleAction.HIRE_MORE
    assert decision_result.count > 0

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
