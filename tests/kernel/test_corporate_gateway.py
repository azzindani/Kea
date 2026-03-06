import pytest
from kernel.corporate_gateway.engine import (
    classify_intent,
    assess_strategy,
    synthesize_response,
    handle_interrupt_logic
)
from shared.schemas import (
    CorporateProcessRequest,
)
from kernel.corporate_gateway.types import (
    ClientIntent,
    ScalingMode,
    StrategyAssessment,
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
    
    # In realistic setting, the gateway gets string from the request instead of building process request.
    # However we will test the unit functions which accept strings:
    
    # Tier 9 Entry Point: Intent Classification
    intent = await classify_intent(request_content=query, session=None, kit=inference_kit)
    assert isinstance(intent, ClientIntent)
    
    print(f"   [BRAIN DECISION]: Classified Intent = {intent.upper()}")
    
    if intent == ClientIntent.STATUS_CHECK:
        print("   [ACTION]: Routing to Status retrieval pipeline.")
    elif intent == ClientIntent.INTERRUPT:
        interrupt_res = handle_interrupt_logic(request_content=query, active_mission_id="mission_active_01")
        print(f"   [ACTION]: Interrupt processed -> {interrupt_res.interrupt_type} | Confidence: {interrupt_res.confidence}")
    else:
        # Assuming NEW_TASK or CONVERSATION
        strategy = await assess_strategy(request_content=query, session=None, kit=inference_kit)
        
        print(f"   [STRATEGY]: Complexity Assessment = {strategy.complexity.upper()}")
        print(f"   [STRATEGY]: Scaling Mode Selected = {strategy.scaling_mode.value.upper()}")
        print(f"   [STRATEGY]: Estimated Agents = {strategy.estimated_agents}")

    print(" \033[92m[SIMULATION STABLE]\033[0m")

@pytest.mark.asyncio
async def test_corporate_gateway_synthesis(inference_kit):
    """Verify Gate-Out executive synthesis from multiple agent artifacts."""
    
    objective = "Analyze market and confirm engineering capabilities."
    artifacts = [
        {"content": "Market research shows 20% growth.", "metadata": {"topic": "Market Research", "agent_id": "agent-market"}},
        {"content": "Engineering confirms feasibility.", "metadata": {"topic": "Engineering Feasibility", "agent_id": "agent-eng"}}
    ]
    
    strategy = StrategyAssessment(
        complexity="moderate",
        scaling_mode=ScalingMode.TEAM,
        estimated_agents=2,
    )
    
    quality_report = {"gaps": [], "completion_pct": 1.0}
    
    print(f"\n--- Testing Corporate Gateway Synthesis: Objective='{objective}' ---")
    
    result = await synthesize_response(
        artifacts=artifacts, 
        strategy=strategy, 
        quality_report=quality_report, 
        kit=inference_kit
    )
    
    print(f"   [OUTPUT]: Merged Sections = {len(result.sections)}")
    print(f"   [OUTPUT]: Is Partial = {result.is_partial}")
    print(f"\n\033[1;32m[FINAL EXECUTIVE SUMMARY]:\033[0m\n{result.executive_summary}\n")
    
    assert result.executive_summary != ""
    assert len(result.sections) == 2
    
    print(" \033[92m[SUCCESS]\033[0m")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
