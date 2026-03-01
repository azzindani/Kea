"""
Tier 2: What-If Scenario Module.

Offline counter-factual simulation → SimulationVerdict (Approve/Reject/Modify).

Usage::

    from kernel.what_if_scenario import simulate_outcomes, CompiledDAG
    from kernel.task_decomposition import WorldState

    dag = CompiledDAG(dag_id="dag_1", description="Deploy to prod", nodes=["build", "test", "deploy"])
    state = WorldState(goal="Deploy new version")
    result = await simulate_outcomes(dag, state)
"""

from .engine import (
    calculate_risk_reward,
    generate_outcome_branches,
    predict_consequences,
    simulate_outcomes,
)
from .types import (
    CompiledDAG,
    ConsequencePrediction,
    OutcomeBranch,
    SimulationVerdict,
    VerdictDecision,
)

__all__ = [
    "simulate_outcomes",
    "generate_outcome_branches",
    "predict_consequences",
    "calculate_risk_reward",
    "CompiledDAG",
    "OutcomeBranch",
    "ConsequencePrediction",
    "SimulationVerdict",
    "VerdictDecision",
]
