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
async def test_what_if_scenario_comprehensive(action_description, context_data):
    """REAL SIMULATION: Verify What-If Scenario Kernel functions with multiple inputs."""
    print(f"\n--- Testing What-If Scenario: Action='{action_description}' ---")

    ws = WorldState(goal=action_description)

    print(f"\n[Test]: generate_outcome_branches")
    branches = await generate_outcome_branches(action_description, ws, kit=None)
    assert isinstance(branches, list)
    assert len(branches) > 0
    print(f"   Simulation Branches generated: {len(branches)}")
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: predict_consequences")
    consequences = await predict_consequences(branches, kit=None)
    assert len(consequences) == len(branches)
    print(f"   Consequences predicted for all branches")
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: calculate_risk_reward")
    score_ratio = calculate_risk_reward(consequences)
    assert isinstance(score_ratio, float)
    assert score_ratio >= 0.0
    print(f"   Calculated Risk/Reward Ratio: {score_ratio:.2f}")
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: simulate_outcomes")
    res = await simulate_outcomes(action_description, ws, kit=None)
    assert res.is_success
    print(f" \033[92m[SUCCESS]\033[0m")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
