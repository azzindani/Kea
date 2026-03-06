import pytest
from kernel.corporate_ops.engine import (
    hire_team,
    match_profiles,
    run_sprint,
    audit_artifacts
)
from shared.schemas import (
    MissionChunk,
    TeamSprintResult,
    QualityAudit,
    RoleProfile,
    MissionStatus
)
from kernel.task_decomposition.types import SubTaskItem

@pytest.mark.parametrize("scenario, chunks, required_domains", [
    (
        "Simple Feature", 
        [MissionChunk(chunk_id="c1", description="Write a sorting algorithm.", requires_team=False)], 
        ["python", "algorithms"]
    ),
    (
        "Full Stack Application", 
        [
            MissionChunk(chunk_id="t1", description="Design database schema", requires_team=False), 
            MissionChunk(chunk_id="t2", description="Build API endpoints", requires_team=False)
        ], 
        ["engineering", "database"]
    ),
])
@pytest.mark.asyncio
async def test_corporate_ops_hiring_simulation(scenario, chunks, required_domains, inference_kit):
    """
    MIDDLE MANAGEMENT SIMULATION: Team hiring and profile matching based on mission chunks.
    """
    print(f"\n\033[1;34m[OPS SIMULATION] Scenario:\033[0m {scenario}")
    
    # 1. Profile Match Simulation for single task
    if len(chunks) == 1:
        result = await match_profiles(chunks[0], required_skills=required_domains)
        assert result.is_success
        role = RoleProfile(**result.signals[0].body["data"])
        
        print(f"   [PROFILE MATCH]: Picked Specialist = {role.role_name} (Confidence: {role.confidence:.2f})")
        assert role.confidence > 0.0
    
    # 2. Complete Team Assembly
    team_res = await hire_team(mission_chunks=chunks, required_domains=required_domains)
    assert team_res.is_success
    team = team_res.signals[0].body["data"]
    
    print(f"   [TEAM ASSEMBLED]: Total Size = {len(team)}")
    for i, member in enumerate(team):
        print(f"     - Agent {i+1}: {member['role_name']}")

    assert len(team) > 0
    print(" \033[92m[SIMULATION STABLE]\033[0m")

@pytest.mark.asyncio
async def test_corporate_ops_sprint_and_audit(inference_kit):
    """Verify sprint coordination and the post-sprint quality auditing processes."""
    
    sprint_id = "sprint_alpha_01"
    tasks = [
        SubTaskItem(task_id="task_1", description="Draft a greeting message.", required_skills=[]),
        SubTaskItem(task_id="task_2", description="Translate the greeting to Spanish.", required_skills=["translation"])
    ]
    
    print(f"\n--- Testing Ops Sprint Execution: Sprint ID='{sprint_id}' ---")
    
    # 1. Sprint Execution
    sprint_res_pkt = await run_sprint(tasks, sprint_id=sprint_id, kit=inference_kit)
    assert sprint_res_pkt.is_success
    sprint_res = TeamSprintResult(**sprint_res_pkt.signals[0].body["data"])
    
    print(f"   [SPRINT OUTPUT]: Status = {sprint_res.status.value.upper()}")
    print(f"   [SPRINT OUTPUT]: Artifacts Generated = {len(sprint_res.consolidated_artifacts)}")
    print(f"   [SPRINT OUTPUT]: Cohesion Score = {sprint_res.team_cohesion_score:.2f}")
    
    assert sprint_res.status == MissionStatus.COMPLETED
    
    # 2. Quality Audit on contradictory artifacts
    artifacts = [
        {"agent": "Agent A", "content": "The database should use PostgreSQL for production."},
        {"agent": "Agent B", "content": "We must use MongoDB for this database, discard SQL."}
    ]
    
    audit_res_pkt = await audit_artifacts(artifacts, kit=inference_kit)
    assert audit_res_pkt.is_success
    audit = QualityAudit(**audit_res_pkt.signals[0].body["data"])
    
    print(f"\n\033[1;31m[RESOLUTION QUALITY AUDIT]:\033[0m")
    print(f"   -> Contradictions Found: {audit.contradictions_found}")
    print(f"   -> Mitigation Strategy: {audit.resolution_strategy}\n")

    assert audit.contradictions_found is True
    print(" \033[92m[SUCCESS]\033[0m")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
