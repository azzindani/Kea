"""
Tests for Agent Spawner and Scaler.
"""

import pytest
import asyncio


class TestTaskDecomposer:
    """Tests for task decomposition."""
    
    def test_decompose_comparison(self):
        """Test decomposing comparison query."""
        from services.orchestrator.core.agent_spawner import TaskDecomposer
        
        decomposer = TaskDecomposer()
        
        subtasks = decomposer.decompose("Compare Tesla vs Ford")
        
        assert len(subtasks) >= 2
        print(f"\n✅ Decomposed into {len(subtasks)} subtasks")
        for st in subtasks:
            print(f"   - {st.query[:50]}...")
    
    def test_decompose_entity_list(self):
        """Test decomposing query with entity list."""
        from services.orchestrator.core.agent_spawner import TaskDecomposer
        
        decomposer = TaskDecomposer()
        
        subtasks = decomposer.decompose("Analyze Apple, Microsoft, and Google")
        
        assert len(subtasks) >= 1
        print(f"\n✅ Entity decomposition: {len(subtasks)} subtasks")
    
    def test_decompose_comprehensive(self):
        """Test decomposing comprehensive research."""
        from services.orchestrator.core.agent_spawner import TaskDecomposer
        
        decomposer = TaskDecomposer()
        
        subtasks = decomposer.decompose("Comprehensive analysis of EV market")
        
        assert len(subtasks) >= 1
        print(f"\n✅ Comprehensive decomposition: {len(subtasks)} subtasks")
    
    def test_simple_query_single_task(self):
        """Test simple query remains single task."""
        from services.orchestrator.core.agent_spawner import TaskDecomposer
        
        decomposer = TaskDecomposer()
        
        subtasks = decomposer.decompose("What is the weather?")
        
        assert len(subtasks) == 1
        print("\n✅ Simple query = single subtask")


class TestAgentSpawner:
    """Tests for agent spawner."""
    
    @pytest.mark.asyncio
    async def test_plan_execution(self):
        """Test creating execution plan."""
        from services.orchestrator.core.agent_spawner import AgentSpawner
        
        spawner = AgentSpawner()
        
        plan = await spawner.plan_execution("Compare Tesla vs Ford")
        
        assert plan.task_id is not None
        assert len(plan.subtasks) >= 1
        assert len(plan.prompts) == len(plan.subtasks)
        
        print(f"\n✅ Execution plan created:")
        print(f"   Task ID: {plan.task_id}")
        print(f"   Subtasks: {len(plan.subtasks)}")
        print(f"   Max parallel: {plan.max_parallel}")
    
    @pytest.mark.asyncio
    async def test_execute_swarm_simulated(self):
        """Test executing swarm (simulated, no LLM)."""
        from services.orchestrator.core.agent_spawner import AgentSpawner, AgentStatus
        
        spawner = AgentSpawner(llm_callback=None, max_parallel=2)
        
        plan = await spawner.plan_execution("Research Tesla")
        result = await spawner.execute_swarm(plan)
        
        assert result.task_id == plan.task_id
        assert result.total_agents == len(plan.subtasks)
        assert result.successful >= 1
        
        print(f"\n✅ Swarm executed:")
        print(f"   Total agents: {result.total_agents}")
        print(f"   Successful: {result.successful}")
        print(f"   Failed: {result.failed}")
    
    @pytest.mark.asyncio
    async def test_parallel_execution(self):
        """Test parallel agent execution."""
        from services.orchestrator.core.agent_spawner import AgentSpawner
        
        execution_times = []
        
        async def mock_llm(system: str, user: str) -> str:
            await asyncio.sleep(0.1)  # Simulate LLM call
            execution_times.append(asyncio.get_event_loop().time())
            return f"Result for: {user[:30]}"
        
        spawner = AgentSpawner(llm_callback=mock_llm, max_parallel=3)
        
        plan = await spawner.plan_execution("Compare A vs B vs C")
        # Force 3 independent subtasks
        plan.subtasks = plan.subtasks[:3]
        plan.prompts = plan.prompts[:3]
        
        result = await spawner.execute_swarm(plan)
        
        assert result.successful >= 1
        print(f"\n✅ Parallel execution complete: {result.successful} successful")
    
    @pytest.mark.asyncio
    async def test_result_aggregation(self):
        """Test result aggregation."""
        from services.orchestrator.core.agent_spawner import AgentSpawner
        
        async def mock_llm(system: str, user: str) -> str:
            return {"finding": "test result"}
        
        spawner = AgentSpawner(llm_callback=mock_llm)
        
        plan = await spawner.plan_execution("Simple query")
        result = await spawner.execute_swarm(plan)
        
        assert result.aggregated_result is not None
        assert "results" in result.aggregated_result
        
        print(f"\n✅ Aggregated result: {result.aggregated_result}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
