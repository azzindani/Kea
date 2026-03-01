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


# --- Mock Asset Pools for Real Simulation ---
SKILLS_POOL = [
    "python_tier_3", "data_analysis", "sql_optimization", "web_scraping", 
    "natural_language_understanding", "cloud_architecture", "api_integration", 
    "security_auditing", "technical_writing", "latency_optimization"
]

TOOLS_POOL = [
    "pandas", "numpy", "scikit_learn", "beautiful_soup", "selenium", 
    "postgresql_client", "docker_engine", "kubernetes_cli", "aws_sdk", "azure_cli", 
    "git_vCS", "jenkins_api", "slack_notifier", "google_workspace_api", "stripe_gateway", 
    "openai_sdk", "anthropic_sdk", "pytorch", "tensorflow_serving", "redis_cache"
]


@pytest.mark.asyncio
@pytest.mark.parametrize("subtasks_list, objective_text", [
    # Scenario 1: Linear dependency (Data Analysis Pipeline)
    (
        [
            SubTaskItem(
                id="t1", 
                description="Fetch raw sales data", 
                domain="data", 
                required_skills=[SKILLS_POOL[3], SKILLS_POOL[6]], # web_scraping, api_integration
                required_tools=[TOOLS_POOL[3], TOOLS_POOL[12]], # beautiful_soup, slack_notifier
                depends_on=[], 
                inputs=[], 
                outputs=["raw_data"], 
                parallelizable=True
            ),
            SubTaskItem(
                id="t2", 
                description="Process and optimize data", 
                domain="analytics", 
                required_skills=[SKILLS_POOL[1], SKILLS_POOL[2]], # data_analysis, sql_optimization
                required_tools=[TOOLS_POOL[0], TOOLS_POOL[5]], # pandas, postgresql_client
                depends_on=["t1"], 
                inputs=["raw_data"], 
                outputs=["analytics_ready"], 
                parallelizable=False
            )
        ],
        "End-to-end Sales Analytics Pipeline"
    ),
    # Scenario 2: Parallel tasks (Cloud Infrastructure Setup)
    (
        [
            SubTaskItem(
                id="t1", 
                description="Provision AWS VPC", 
                domain="infra", 
                required_skills=[SKILLS_POOL[5]], # cloud_architecture
                required_tools=[TOOLS_POOL[8]], # aws_sdk
                depends_on=[], 
                inputs=[], 
                outputs=["vpc_id"], 
                parallelizable=True
            ),
            SubTaskItem(
                id="t2", 
                description="Initialize Kubernetes Cluster", 
                domain="infra", 
                required_skills=[SKILLS_POOL[5], SKILLS_POOL[9]], # cloud_architecture, latency_optimization
                required_tools=[TOOLS_POOL[7], TOOLS_POOL[18]], # kubernetes_cli, tensorflow_serving
                depends_on=[], 
                inputs=[], 
                outputs=["cluster_endpoint"], 
                parallelizable=True
            )
        ],
        "Parallel Hybrid Cloud Provisioning"
    ),
    # Scenario 3: Single task (Security Compliance Check)
    (
        [
            SubTaskItem(
                id="t1", 
                description="Run SOC2 compliance scan", 
                domain="security", 
                required_skills=[SKILLS_POOL[7], SKILLS_POOL[8]], # security_auditing, technical_writing
                required_tools=[TOOLS_POOL[6], TOOLS_POOL[10]], # docker_engine, git_vCS
                depends_on=[], 
                inputs=[], 
                outputs=["audit_report"], 
                parallelizable=True
            )
        ],
        "Automated Security Compliance Audit"
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
