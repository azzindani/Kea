"""
PHASE 4: EXECUTE

Executes the planned steps using the DAGExecutor.
Converts the abstract PlanResult into concrete WorkflowNodes and orchestrates their execution.
"""

from __future__ import annotations

from typing import Any

from kernel.cognition.base import BasePhase, CycleContext
from kernel.flow.dag_executor import DAGExecutor
from kernel.flow.workflow_nodes import WorkflowNode, NodeType, NodeStatus
from kernel.memory.artifact_store import ArtifactStore


class Executor(BasePhase):
    """
    Execution Phase: Running the plan.
    """

    async def run(self, plan: Any) -> dict[str, Any]:
        """
        Execute the plan using DAGExecutor.
        Returns the execution result dict.
        """
        self.logger.info(f"Executing plan with {len(plan.steps)} steps")
        
        # 1. Convert PlanStep to WorkflowNode
        nodes = self._build_dag(plan)
        if not nodes:
            self.logger.warning("No nodes to execute")
            return {}

        # 2. Setup Artifact Store
        # Use shared store from context to persist artifacts across phases
        store = self.context.artifact_store
        
        # 3. Initialize Executor
        executor = DAGExecutor(
            store=store,
            node_executor=self._execute_node_wrapper,
            max_parallel=5
        )
        
        # 4. Run
        result = await executor.execute(nodes)
        
        # 5. Harvest Results
        # Update context metrics
        self.context.tool_call_count += result.total_nodes # Approx
        
        # Store results in context for Monitor phase
        self.context.execution_history.append(result)
        
        # Return summary
        return {
            "completed": result.completed,
            "failed": result.failed,
            "artifacts": store.list_artifacts()
        }

    def _build_dag(self, plan: Any) -> list[WorkflowNode]:
        """Convert PlanSteps to WorkflowNodes."""
        nodes = []
        for step in plan.steps:
            # Map PlanStep fields to WorkflowNode
            node = WorkflowNode(
                id=step.step_id,
                phase=1, # simplified
                node_type=NodeType.TOOL if step.tool else NodeType.LLM,
                tool=step.tool,
                args=step.args,
                depends_on=step.depends_on,
                description=step.description,
                output_artifact=f"{step.step_id}_output" # Default artifact name
            )
            nodes.append(node)
        return nodes

    async def _execute_node_wrapper(self, node: WorkflowNode, args: dict[str, Any]) -> Any:
        """Wrapper to call context.tool_call or context.llm_call."""
        from kernel.flow.workflow_nodes import NodeResult, NodeStatus
        
        try:
            if node.node_type == NodeType.TOOL and node.tool:
                # Execute Tool
                output = await self.context.tool_call(node.tool, args)
                status = NodeStatus.COMPLETED
            else:
                # Execute LLM (Simple reasoning step)
                # We construct a simple prompt for the LLM node
                desc = node.description or "Process this step"
                prompt = f"Step: {desc}\nTarget: {args}"
                output = await self.context.llm_call(
                    system_prompt="You are an autonomous worker. Execute the task.",
                    user_prompt=prompt
                )
                status = NodeStatus.COMPLETED

            return NodeResult(
                node_id=node.id,
                status=status,
                output=output,
                artifacts={node.output_artifact: output} if node.output_artifact else {}
            )
            
        except Exception as e:
            self.logger.error(f"Node execution failed: {e}")
            return NodeResult(
                node_id=node.id,
                status=NodeStatus.FAILED,
                error=str(e)
            )
