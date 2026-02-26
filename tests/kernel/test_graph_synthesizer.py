import pytest

from kernel.graph_synthesizer.engine import (
    map_subtasks_to_nodes,
    calculate_dependency_edges,
    compile_dag,
    review_dag_with_simulation,
    synthesize_plan
)
from kernel.task_decomposition.types import SubTaskItem, WorldState
from shared.config import get_settings


@pytest.mark.asyncio
@pytest.mark.parametrize("subtasks_list, objective_text", [
    # Scenario 1: Linear dependency
    (
        [
            SubTaskItem(id="t1", description="Init", domain="core", required_skills=[], required_tools=[], depends_on=[], inputs=[], outputs=["state"], parallelizable=True),
            SubTaskItem(id="t2", description="Work", domain="core", required_skills=[], required_tools=[], depends_on=["t1"], inputs=["state"], outputs=["done"], parallelizable=False)
        ],
        "Standard multi-step task"
    ),
    # Scenario 2: Parallel tasks
    (
        [
            SubTaskItem(id="t1", description="Part A", domain="gen", required_skills=[], required_tools=[], depends_on=[], inputs=[], outputs=["a"], parallelizable=True),
            SubTaskItem(id="t2", description="Part B", domain="gen", required_skills=[], required_tools=[], depends_on=[], inputs=[], outputs=["b"], parallelizable=True)
        ],
        "Parallel data gathering"
    ),
    # Scenario 3: Single task
    (
        [SubTaskItem(id="t1", description="Only task", domain="simple", required_skills=[], required_tools=[], depends_on=[], inputs=[], outputs=[], parallelizable=True)],
        "Single action goal"
    )
])
async def test_graph_synthesizer_comprehensive(subtasks_list, objective_text, inference_kit):
    """REAL SIMULATION: Verify Graph Synthesizer Kernel functions with multiple scenarios."""
    print(f"\n--- Testing Graph Synthesizer: Objective='{objective_text}' ---")

    print(f"\n[Test]: map_subtasks_to_nodes")
    print(f"   [INPUT]: {len(subtasks_list)} subtasks")
    nodes = await map_subtasks_to_nodes(subtasks_list, kit=inference_kit)
    assert len(nodes) == len(subtasks_list)
    print(f"   [OUTPUT]: Nodes mapped count={len(nodes)}")
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: calculate_dependency_edges")
    print(f"   [INPUT]: {len(nodes)} nodes")
    edges = calculate_dependency_edges(nodes)
    print(f"   [OUTPUT]: Dependency Edges count={len(edges)}")
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: compile_dag")
    print(f"   [INPUT]: {len(nodes)} nodes, {len(edges)} edges")
    dag = compile_dag(nodes, edges, objective_text)
    assert dag is not None
    assert dag.description == objective_text
    print(f"   [OUTPUT]: DAG ID={dag.dag_id}, Description='{dag.description}'")
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: review_dag_with_simulation")
    print(f"   [INPUT]: DAG ID={dag.dag_id}")
    simulation_verdict = await review_dag_with_simulation(dag)
    assert simulation_verdict is not None
    assert hasattr(simulation_verdict, 'decision')
    print(f"   [OUTPUT]: Simulation Verdict={simulation_verdict.decision.value}")
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: synthesize_plan")
    print(f"   [INPUT]: objective='{objective_text}'")
    res = await synthesize_plan(objective_text)
    assert res.is_success
    print(f"   [OUTPUT]: Status={res.status}, Signals count={len(res.signals)}")
    print(f" \033[92m[SUCCESS]\033[0m")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
