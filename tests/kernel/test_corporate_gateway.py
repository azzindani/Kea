import pytest
from kernel.corporate_gateway.engine import (
    classify_intent,
    assess_strategy,
    synthesize_response,
    handle_interrupt_logic
)
from shared.schemas import (
    CorporateProcessRequest,
    ClientIntent,
    ScalingMode,
    CorporateProcessResponse,
    CorporateQuality,
    MissionSummary
)
from kernel.task_decomposition.types import GoalComplexity

@pytest.mark.parametrize("query", [
    "Please analyze the competitor data and build a report.",
    "What is the status of my report?",
    "Stop what you are doing and abort the mission.",
    "Build a full software platform with frontend, backend, and deployment."
])
@pytest.mark.asyncio
async def test_corporate_gateway_comprehensive(query, inference_kit):
    """
    APEX SIMULATION: Gateway request routing and strategy.
    The Gateway classifies intent, assesses strategy, and triggers actions based on the query.
    """
    print(f"\n\033[1;36m[GATEWAY SIMULATION] Incoming Signal:\033[0m {query}")
    
    request = CorporateProcessRequest(message=query)
    
    # Tier 9 Entry Point: Intent Classification
    intent_res = await classify_intent(request, kit=inference_kit)
    assert intent_res.is_success
    intent = intent_res.signals[0].body["data"]["intent"]
    
    print(f"   [BRAIN DECISION]: Classified Intent = {intent.upper()}")
    
    if intent == ClientIntent.STATUS_CHECK:
        print("   [ACTION]: Routing to Status retrieval pipeline.")
    elif intent == ClientIntent.INTERRUPT:
        interrupt_res = await handle_interrupt_logic(request, active_mission_id="mission_active_01")
        assert interrupt_res.is_success
        data = interrupt_res.signals[0].body["data"]
        print(f"   [ACTION]: Interrupt processed -> {data['action']} over {data['mission_id']}")
    else:
        # Assuming NEW_TASK or CONVERSATION
        # Mock complexity for demo purposes based on keywords
        complexity = GoalComplexity.COMPOUND if "platform" in query.lower() else GoalComplexity.SIMPLE
        
        strategy_res = await assess_strategy(request, complexity, kit=inference_kit)
        assert strategy_res.is_success
        strategy = strategy_res.signals[0].body["data"]
        
        print(f"   [STRATEGY]: Complexity Assessment = {complexity.value.upper()}")
        print(f"   [STRATEGY]: Scaling Mode Selected = {strategy['selected_mode'].upper()}")
        print(f"   [STRATEGY]: Required Domains = {strategy['required_domains']}")

    print(" \033[92m[SIMULATION STABLE]\033[0m")

@pytest.mark.asyncio
async def test_corporate_gateway_synthesis(inference_kit):
    """Verify Gate-Out executive synthesis from multiple agent artifacts."""
    
    objective = "Analyze market and confirm engineering capabilities."
    artifacts = [
        "Artifact 1: Market research shows 20% growth.",
        "Artifact 2: Engineering confirms feasibility."
    ]
    report = CorporateQuality(
        contradictions_found=False,
        quality_score=0.92,
        resolution_notes="All clear."
    )
    summary = MissionSummary(
        total_tasks=2,
        failed_tasks=0,
        total_duration_ms=1500.0,
        total_cost=0.04
    )
    
    request = CorporateProcessRequest(
        message=objective,
        require_executive_summary=True
    )
    
    print(f"\n--- Testing Corporate Gateway Synthesis: Objective='{objective}' ---")
    
    result = await synthesize_response(request, artifacts, report, summary, kit=inference_kit)
    assert result.is_success
    
    resp_obj = CorporateProcessResponse(**result.signals[0].body["data"])
    
    print(f"   [OUTPUT]: Merged Artifacts = {len(resp_obj.artifacts)}")
    print(f"   [OUTPUT]: Quality Score = {resp_obj.quality_metrics.quality_score:.2f}")
    print(f"\n\033[1;32m[FINAL EXECUTIVE SUMMARY]:\033[0m\n{resp_obj.executive_summary}\n")
    
    assert resp_obj.executive_summary is not None
    assert len(resp_obj.artifacts) == 2
    
    print(" \033[92m[SUCCESS]\033[0m")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
