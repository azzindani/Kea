import pytest
from kernel.workforce_manager.engine import evaluate_performance, match_specialist
from kernel.team_orchestrator.engine import plan_sprints
from kernel.quality_resolver.engine import score_sprint_quality
from kernel.workforce_manager.types import MissionChunk
from kernel.quality_resolver.types import QualityAudit

@pytest.mark.asyncio
async def test_corporate_ops_comprehensive(inference_kit):
    """
    APEX SIMULATION: Tier 8 Corporate Operations.
    This simulates the full Ops pipeline: Planning -> Hiring -> Quality Audit.
    """
    print(f"\n\033[1;34m[OPS SIMULATION] Starting Full Corporate Operations Pipeline\033[0m")
    
    # 1. Plan Sprints (Team Orchestrator)
    print("   [ACTION]: Planning sprints for complex mission...")
    chunks = [
        MissionChunk(chunk_id="c1", parent_objective_id="o1", domain="infrastructure", sub_objective="Setup K8s"),
        MissionChunk(chunk_id="c2", parent_objective_id="o1", domain="database", sub_objective="Configure Postgres", depends_on=["c1"]),
    ]
    
    plan_result = await plan_sprints(chunks, mission_id="mission_01", kit=inference_kit)
    assert plan_result.is_success
    sprints = plan_result.signals[0].body["data"]["sprints"]
    print(f"   [ORCHESTRATOR]: Planned {len(sprints)} sprints.")
    
    # 2. Assign Specialists (Workforce Manager)
    print("   [ACTION]: Hiring specialists for Sprint 1...")
    available_profiles = [
        {"profile_id": "prof-devops", "role_name": "DevOps Engineer", "skills": ["aws", "k8s", "docker"]},
        {"profile_id": "prof-db", "role_name": "Database Admin", "skills": ["sql", "postgres"]}
    ]
    
    match_result = await match_specialist(chunks[0], available_profiles, kit=inference_kit)
    assert match_result.is_success
    best_profile = match_result.signals[0].body["data"]["agent_profile_id"]
    print(f"   [WORKFORCE MANAGER]: Assigned {best_profile} to chunk {chunks[0].chunk_id}")
    
    # 3. Quality Audit (Quality Resolver)
    print("   [ACTION]: Auditing sprint results...")
    mock_agent_results = [
        {"agent_id": best_profile, "quality_score": 0.95, "confidence": 0.9, "grounding_rate": 0.99}
    ]
    
    audit_result = await score_sprint_quality(mock_agent_results, sprint_id="sprint_1", kit=inference_kit)
    assert audit_result.is_success
    audit = QualityAudit(**audit_result.signals[0].body["data"])
    
    print(f"   [QUALITY RESOLVER]: Sprint Audit Verdict = {audit.overall.upper()}")
    print(f"   [QUALITY RESOLVER]: Average Quality = {audit.avg_quality:.2f}")

    assert audit.overall == "pass"
    print(" \033[92m[SIMULATION STABLE]\033[0m")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
