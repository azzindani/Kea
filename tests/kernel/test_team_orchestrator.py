import pytest
from kernel.team_orchestrator.engine import (
    plan_sprints,
    build_sprint_dag,
    review_sprint
)
from kernel.workforce_manager.types import MissionChunk
from kernel.team_orchestrator.types import Sprint, SprintResult

@pytest.mark.asyncio
async def test_plan_sprints(inference_kit):
    """Test grouping mission chunks into dependency-aware sprints."""
    chunks = [
        MissionChunk(chunk_id="c1", parent_objective_id="o1", domain="d1", sub_objective="s1", description="Foundation Tasks", depends_on=[]),
        MissionChunk(chunk_id="c2", parent_objective_id="o1", domain="d2", sub_objective="s2", description="Database Setup", depends_on=["c1"]),
        MissionChunk(chunk_id="c3", parent_objective_id="o1", domain="d3", sub_objective="s3", description="API Implementation", depends_on=["c2"]),
        MissionChunk(chunk_id="c4", parent_objective_id="o1", domain="d4", sub_objective="s4", description="Documentation", depends_on=["c1"])
    ]
    
    result = await plan_sprints(chunks, mission_id="mission_complex", kit=inference_kit)
    assert result.is_success
    
    sprints = result.signals[0].body["data"]["sprints"]
    print(f"\n\033[1;36m[SPRINT PLANNING]\033[0m Total Chunks: {len(chunks)}")
    for s in sprints:
        print(f"   -> Sprint {s['sprint_number']}: {s['chunks']}") # Note: plan_sprints returns chunks as dicts
    
    # Should have at least 3 levels (c1 -> c2/c4 -> c3)
    assert len(sprints) >= 3
    assert len(sprints[0]["chunks"]) > 0

@pytest.mark.asyncio
async def test_build_sprint_dag(inference_kit):
    """Test compiling a sprint into an ExecutableDAG."""
    sprint = Sprint(
        sprint_id="s1",
        mission_id="m1",
        sprint_number=1,
        objective="Initial foundation",
        chunks=[
            MissionChunk(chunk_id="c1", parent_objective_id="o1", domain="d1", sub_objective="s1"),
            MissionChunk(chunk_id="c4", parent_objective_id="o1", domain="d4", sub_objective="s4")
        ]
    )
    
    result = await build_sprint_dag(sprint, kit=inference_kit)
    assert result.is_success
    
    dag = result.signals[0].body["data"]
    print(f"\n\033[1;34m[SPRINT DAG BUILDING]\033[0m Sprint ID: {sprint.sprint_id}")
    print(f"   -> Node Count: {len(dag['nodes'])}")
    
    # Each chunk should become a node
    assert len(dag['nodes']) == 2

@pytest.mark.asyncio
async def test_review_sprint(inference_kit):
    """Test the post-sprint retrospective logic."""
    sprint = Sprint(
        sprint_id="s1", 
        mission_id="m1", 
        sprint_number=1, 
        objective="Initial foundation",
        chunks=[]
    )
    result_data = SprintResult(
        sprint_id="s1",
        completed_chunks=["c1"],
        failed_chunks=[],
        artifacts_produced=["art-1", "art-2"],
        duration_ms=5000.0,
        total_cost=0.04
    )
    
    result = await review_sprint(sprint, result_data, kit=inference_kit)
    assert result.is_success
    
    review = result.signals[0].body["data"]
    print(f"\n\033[1;35m[SPRINT REVIEW]\033[0m Sprint: {sprint.sprint_id}")
    print(f"   -> Quality Assessment: {review['quality_assessment']}")
    print(f"   -> Next Sprint Approved: {review.get('next_sprint_approved', True)}")
    
    assert review['next_sprint_approved'] is True

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
