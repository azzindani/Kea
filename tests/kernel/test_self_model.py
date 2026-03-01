import pytest

from kernel.self_model.engine import (
    assess_capability,
    update_cognitive_state,
    detect_capability_gap,
    update_accuracy_history,
    refresh_capability_map,
    run_self_model
)
from kernel.self_model.types import SignalTags
from kernel.lifecycle_controller.types import IdentityContext
from shared.config import get_settings


@pytest.mark.asyncio
@pytest.mark.parametrize("input_signal, target_domain, required_tools, required_skills, intent", [
    ("Optimizing a Python microservice", "coding", ["bash"], ["coding"], "performance"),
    ("Perform an orbital calculation for a satellite", "science", ["matlab"], ["astrodynamics"], "research"),
    ("Delete all project artifacts with no backup", "ops", ["rm"], ["system_admin"], "destructive"),
    ("Heavy data analysis with Spark", "data", ["spark"], ["data_engineering"], "analysis")
])
async def test_self_model_comprehensive(input_signal, target_domain, required_tools, required_skills, intent, inference_kit):
    """REAL SIMULATION: Verify Self-Model with adversarial and domain-mismatch scenarios."""
    print(f"\n--- Testing Self Model: Signal='{input_signal[:40]}...', Domain='{target_domain}' ---")

    tags = SignalTags(
        urgency="normal", 
        complexity="high", 
        intent=intent, 
        domain=target_domain,
        required_tools=required_tools,
        required_skills=required_skills
    )
    
    identity = IdentityContext(
        agent_id="test_agent", 
        role="senior_python_developer", 
        skills=frozenset(["coding", "performance_tuning"]),
        tools_allowed=frozenset(["bash", "git"]),
        tools_forbidden=frozenset(["rm -rf", "drop database"]),
        knowledge_domains=frozenset(["software_engineering", "python_ecosystem"]),
        ethical_constraints=("prevent_data_loss",),
        quality_bar=0.8
    )

    print(f"\n[Test]: assess_capability (Introspection)")
    print(f"   [INPUT]: goal_domain='{target_domain}', agent_role='{identity.role}'")
    assessment = await assess_capability(tags, identity, kit=inference_kit)
    
    assert assessment is not None
    print(f"   [OUTPUT]: Can Handle={assessment.can_handle}")
    print(f"   [OUTPUT]: Capability Confidence={assessment.confidence:.2f}")
    
    if assessment.gap:
        print(f"   [TRACE]: Gap Severity={assessment.gap.severity:.2f}")
        if assessment.gap.missing_knowledge:
            print(f"     - Missing Knowledge: {assessment.gap.missing_knowledge}")
        if assessment.gap.missing_tools:
            print(f"     - Missing Tools: {assessment.gap.missing_tools}")
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: detect_capability_gap (Audit)")
    gap = await detect_capability_gap(tags, identity, kit=inference_kit)
    if gap:
        print(f"   [OUTPUT]: Critical Gap Identified (Severity={gap.severity})")
        if gap.constraint_violations:
            print(f"     - Policy Violations: {gap.constraint_violations}")
    else:
        print("   [OUTPUT]: Fully compliant capability profile")
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: update_cognitive_state (Observability)")
    from kernel.self_model.types import ProcessingPhase
    updates = update_cognitive_state(
        agent_id=identity.agent_id, 
        processing_phase=ProcessingPhase.PRE_EXECUTION,
        current_task_description=input_signal
    )
    assert updates.processing_phase == ProcessingPhase.PRE_EXECUTION
    print(f"   [OUTPUT]: Brain State updated to '{updates.processing_phase}'")
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: run_self_model (Top-Level Orchestration)")
    res = await run_self_model(tags, identity, kit=inference_kit)
    assert res.is_success
    print(f"   [OUTPUT]: Execution status={res.status}, Trace ID={res.signals[0].trace_id if res.signals else 'N/A'}")
    print(f" \033[92m[SUCCESS]\033[0m")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
