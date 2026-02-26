import pytest

from kernel.what_if_scenario.engine import (
    generate_outcome_branches,
    predict_consequences,
    calculate_risk_reward,
    simulate_outcomes
)
from kernel.task_decomposition.types import WorldState
from shared.config import get_settings


@pytest.mark.asyncio
@pytest.mark.parametrize("action_description, context_data", [
    ("Delete all files in the current working directory", {"user_role": "admin", "env": "prod"}),
    ("Update the project documentation with latest API changes", {"user_role": "dev", "env": "local"}),
    ("Restart the main web server", {"user_role": "ops", "env": "staging"}),
    ("Draft a sensitive internal email about executive changes", {"user_role": "hr", "env": "secure"})
])
async def test_what_if_scenario_comprehensive(action_description, context_data, inference_kit):
    """REAL SIMULATION: Verify What-If Scenario Kernel functions with multiple inputs."""
    print(f"\n--- Testing What-If Scenario: Action='{action_description}' ---")

    from kernel.what_if_scenario.types import CompiledDAG, SimulationVerdict
    action = CompiledDAG(description=action_description, nodes=["node_1", "node_2"])
    ws = WorldState(goal=action_description)

    print(f"\n[Test]: generate_outcome_branches")
    print(f"   [INPUT]: action='{action_description}'")
    branches = generate_outcome_branches(action, ws)
    assert isinstance(branches, list)
    assert len(branches) > 0
    print(f"   [OUTPUT]: Simulation Branches generated count={len(branches)}")
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: predict_consequences")
    print(f"   [INPUT]: {len(branches)} branches")
    consequences = await predict_consequences(branches, kit=inference_kit)
    assert len(consequences) == len(branches)
    print(f"   [OUTPUT]: Consequences predicted for all branches")
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: calculate_risk_reward")
    print(f"   [INPUT]: {len(consequences)} consequences")
    verdict = calculate_risk_reward(consequences)
    assert isinstance(verdict, SimulationVerdict)
    assert verdict.risk_score >= 0.0
    print(f"   [OUTPUT]: Calculated Risk Score={verdict.risk_score:.2f}")
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: simulate_outcomes")
    print(f"   [INPUT]: action='{action_description}'")
    res = await simulate_outcomes(action, ws, kit=inference_kit)
    assert res.is_success
    print(f"   [OUTPUT]: Status={res.status}, Signals count={len(res.signals)}")
    print(f" \033[92m[SUCCESS]\033[0m")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
