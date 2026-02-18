"""
Swarm Execution Engine.

Executes a plan using the Agent Spawner (Swarm) and DAG Executor.
Logic extracted from graph.py's researcher_node to promote modularity.
"""

from __future__ import annotations

import asyncio
import os
from datetime import datetime
from typing import Any, Dict, List, Set, Tuple

from kernel.actions.agent_spawner import (
    Domain,
    SpawnPlan,
    SubTask,
    TaskType,
    get_spawner,
)
from kernel.core.prompt_factory import PromptContext, PromptFactory
from kernel.flow.dag_executor import DAGExecutor
from kernel.flow.microplanner import Microplanner
from kernel.flow.workflow_nodes import (
    NodeResult,
    NodeStatus,
    WorkflowNode,
    parse_blueprint,
)
from shared.config import get_settings
from shared.context_pool import get_context_pool
from shared.llm import LLMConfig, OpenRouterProvider
from shared.llm.provider import LLMMessage, LLMRole
from shared.logging import get_logger

logger = get_logger(__name__)


# Helper for Tool Citation Construction
def _build_tool_citation(
    tool_name: str,
    server_name: str,
    arguments: dict,
    result_preview: str,
    duration_ms: float = 0.0,
    is_error: bool = False,
    invoked_at: datetime | None = None,
    source_url: str = "",
) -> dict:
    return {
        "tool_name": tool_name,
        "server_name": server_name,
        "arguments": arguments,
        "result_preview": result_preview[:500],
        "is_error": is_error,
        "duration_ms": round(duration_ms, 2),
        "invoked_at": (invoked_at or datetime.utcnow()).isoformat(),
        "source_url": source_url,
    }


class SwarmExecutor:
    """
    Executes tasks using a swarm of spawned agents tailored to each node.
    """

    def __init__(self, job_id: str):
        self.job_id = job_id
        self.prompt_factory = PromptFactory()
        self.completed_calls: Set[str] = set()

    async def execute(
        self,
        micro_tasks: List[Dict[str, Any]],
        state: Dict[str, Any],
        assembler: Any,
    ) -> Tuple[Any, List[dict], List[dict], List[dict], List[dict]]:
        """
        Run the DAG of micro-tasks using Swarm Agents.
        
        Returns:
            (dag_result, facts, sources, tool_invocations, error_feedback)
        """
        # Callbacks
        async def _llm_callback(system_prompt: str, user_message: str) -> str:
            try:
                if not os.getenv("OPENROUTER_API_KEY"):
                    return ""
                app_cfg = get_settings()
                provider = OpenRouterProvider()
                cfg = LLMConfig(
                    model=app_cfg.models.planner_model,
                    temperature=0.3,
                    max_tokens=32768,
                )
                msgs = [
                    LLMMessage(role=LLMRole.SYSTEM, content=system_prompt),
                    LLMMessage(role=LLMRole.USER, content=user_message),
                ]
                resp = await provider.complete(msgs, cfg)
                return resp.content
            except Exception as e:
                logger.warning(f"LLM callback failed: {e}")
                return ""

        spawner = get_spawner(llm_callback=_llm_callback)
        complexity_info = state.get("complexity", {})
        max_parallel = complexity_info.get("max_parallel", 6)
        workflow_nodes = parse_blueprint(micro_tasks)

        logger.info(
            f"  SwarmExecutor: {len(workflow_nodes)} nodes, max_parallel={max_parallel}"
        )

        # Execution Logic for Single Node
        async def execute_workflow_node(
            node: WorkflowNode,
            args: dict,
        ) -> NodeResult:
            subtask = SubTask(
                subtask_id=node.id,
                query=node.description or f"{node.tool}: {str(args)[:100]}",
                domain=Domain.RESEARCH,
                task_type=TaskType.RESEARCH,
                preferred_tool=node.tool,
                arguments=args,
            )

            try:
                ctx_pool = get_context_pool()
                global_facts = [f.get("text", "") for f in ctx_pool.fact_pool]
            except Exception:
                global_facts = []

            prompt_ctx = PromptContext(
                query=subtask.query,
                domain=subtask.domain,
                task_type=subtask.task_type,
                previous_findings=global_facts,
            )
            prompt = self.prompt_factory.generate(prompt_ctx)

            plan = SpawnPlan(
                task_id=f"{self.job_id}_{node.id}",
                subtasks=[subtask],
                prompts=[prompt],
                max_parallel=1,
            )

            swarm_result = await spawner.execute_swarm(plan)

            if swarm_result.successful > 0:
                agent_res = next(
                    (r for r in swarm_result.agent_results if r.status == "completed"),
                    None,
                )
                output = agent_res.result if agent_res else None

                # Store in context pool
                try:
                    ctx_pool = get_context_pool()
                    ctx_pool.store_data(
                        key=f"task_output_{node.id}",
                        data=str(output),
                        description=f"Output from node {node.id}",
                    )
                    ctx_pool.add_fact(
                        text=str(output),
                        source=f"task_{node.id}",
                        task_id=node.id,
                    )
                except Exception as e:
                    logger.warning(f"Context pool update failed: {e}")

                _duration_ms = (agent_res.duration_seconds * 1000.0) if agent_res else 0.0
                _dag_citation = _build_tool_citation(
                    tool_name=node.tool or "dag_executor",
                    server_name="swarm_agent",
                    arguments=args,
                    result_preview=str(output)[:500] if output else "",
                    duration_ms=_duration_ms,
                    invoked_at=agent_res.started_at if agent_res else None,
                    source_url=agent_res.source if agent_res and agent_res.source.startswith("http") else "",
                )
                return NodeResult(
                    node_id=node.id,
                    status=NodeStatus.COMPLETED,
                    output=output,
                    artifacts={node.output_artifact: str(output)} if node.output_artifact else {},
                    metadata={
                        "source": agent_res.source if agent_res else None,
                        "tool_citation": _dag_citation,
                        "tool_name": node.tool,
                    },
                )
            else:
                return NodeResult(
                    node_id=node.id,
                    status=NodeStatus.FAILED,
                    error="Agents failed",
                )

        # Microplanner & DAG Execution
        microplanner = Microplanner(
            query=state.get("query", ""),
            llm_callback=spawner.llm_callback,
            max_replans=complexity_info.get("max_research_iterations", 3),
        )

        dag_executor = DAGExecutor(
            store=assembler.store,
            node_executor=execute_workflow_node,
            max_parallel=max_parallel,
            microplanner=microplanner.checkpoint,
        )

        dag_result = await dag_executor.execute(workflow_nodes)
        
        # Harvest Results
        facts = []
        sources = []
        tool_invocations = []
        error_feedback = []
        
        from shared.vocab import load_vocab
        _VOCAB = load_vocab("classification")
        _STANDARD_ERRORS = _VOCAB.get("error_keywords", {}).get("standard", [])

        for node_id, node_result in dag_result.node_results.items():
            if node_result.status == NodeStatus.COMPLETED and node_result.output:
                output_text = str(node_result.output)
                
                # Strict Error Filtering
                is_error = False
                for keyword in _STANDARD_ERRORS:
                    if keyword in output_text.lower():
                        is_error = True
                        break
                
                if len(output_text.strip()) < 5:
                    is_error = True
                
                if not is_error:
                    metadata = node_result.metadata or {}
                    tool_name = (
                        metadata.get("tool_name")
                        or metadata.get("source")
                        or metadata.get("tool")
                        or "dag_executor"
                    )
                    # Convert tool_name to string if purely numeric or None
                    tool_name = str(tool_name) if tool_name else "unknown_tool"

                    # Build citation
                    tool_citation = metadata.get("tool_citation") or _build_tool_citation(
                        tool_name=tool_name,
                        server_name="swarm_agent",
                        arguments=metadata.get("arguments", {}),
                        result_preview=output_text,
                    )
                    source_url = tool_citation.get("source_url", "")
                    
                    facts.append(
                        {
                            "text": output_text,
                            "query": f"DAG Node {node_id}",
                            "source": tool_name,
                            "source_url": source_url,
                            "task_id": node_id,
                            "persist": True,
                            "tool_citation": tool_citation,
                        }
                    )
                    
                    if source_url and source_url not in [s.get("url") for s in sources]:
                        sources.append(
                            {
                                "url": source_url,
                                "title": f"DAG Node {node_id}",
                                "tool": tool_name,
                                "task_id": node_id,
                            }
                        )
                
                # Always record invocation
                _ti_citation = (node_result.metadata or {}).get("tool_citation") or _build_tool_citation(
                     tool_name=(node_result.metadata or {}).get("tool_name", "dag_executor"),
                     server_name="swarm_agent",
                     arguments=(node_result.metadata or {}).get("arguments", {}),
                     result_preview=str(node_result.output)[:500],
                     is_error=False,
                )
                tool_invocations.append(
                    {
                        "task_id": node_id,
                        "tool": (node_result.metadata or {}).get("tool_name", "dag_executor"),
                        "success": True,
                        "persist": True,
                        "tool_citation": _ti_citation,
                    }
                )

            elif node_result.status == NodeStatus.FAILED:
                # Capture Error
                error_str = str(node_result.error or "Unknown error")[:500]
                error_feedback.append(
                    {
                        "tool": "unknown", # Could lookup workflow node if passed
                        "task_id": node_id,
                        "error": error_str,
                        "args": {},
                        "description": "",
                        "suggestion": "",
                    }
                )

        return dag_result, facts, sources, tool_invocations, error_feedback
