"""
Agent Spawner and Scaler.

Self-multiplying agent system for massive tasks.
Decomposes tasks, spawns specialized agents, aggregates results.
"""

from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable

from shared.logging import get_logger
from services.orchestrator.core.prompt_factory import (
    PromptFactory,
    PromptContext,
    GeneratedPrompt,
    Domain,
    TaskType,
)


logger = get_logger(__name__)


class AgentStatus(str, Enum):
    """Agent execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class SubTask:
    """A decomposed subtask."""
    subtask_id: str
    query: str
    domain: Domain
    task_type: TaskType
    priority: int = 1  # 1=highest
    dependencies: list[str] = field(default_factory=list)
    estimated_complexity: int = 1  # 1-5 scale


@dataclass
class AgentResult:
    """Result from a single agent execution."""
    agent_id: str
    subtask_id: str
    status: AgentStatus
    result: Any = None
    error: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    prompt_used: str = ""
    
    @property
    def duration_seconds(self) -> float:
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return 0.0


@dataclass
class SpawnPlan:
    """Plan for spawning multiple agents."""
    task_id: str
    subtasks: list[SubTask]
    max_parallel: int
    prompts: list[GeneratedPrompt] = field(default_factory=list)
    estimated_time_seconds: float = 0.0


@dataclass
class SwarmResult:
    """Aggregated result from agent swarm."""
    task_id: str
    agent_results: list[AgentResult]
    aggregated_result: Any = None
    total_agents: int = 0
    successful: int = 0
    failed: int = 0
    started_at: datetime | None = None
    completed_at: datetime | None = None


class TaskDecomposer:
    """
    Decompose complex tasks into subtasks.
    
    Strategies:
    - Entity-based: One subtask per entity
    - Aspect-based: One subtask per aspect to analyze
    - Sequential: Chain of dependent subtasks
    - Parallel: Independent subtasks
    """
    
    def decompose(
        self,
        query: str,
        max_subtasks: int = 5,
        strategy: str = "auto",
    ) -> list[SubTask]:
        """Decompose query into subtasks."""
        query_lower = query.lower()
        
        # Detect entities (e.g., "Compare A vs B vs C")
        entities = self._extract_entities(query)
        if len(entities) > 1 and strategy in ("auto", "entity"):
            return self._decompose_by_entity(query, entities)
        
        # Detect aspects (e.g., "Analyze revenue, profit, and growth")
        aspects = self._extract_aspects(query)
        if len(aspects) > 1 and strategy in ("auto", "aspect"):
            return self._decompose_by_aspect(query, aspects)
        
        # Detect comparison
        if any(kw in query_lower for kw in ["compare", "vs", "versus", "difference"]):
            return self._decompose_comparison(query)
        
        # Detect research depth
        if any(kw in query_lower for kw in ["comprehensive", "thorough", "deep", "all"]):
            return self._decompose_comprehensive(query)
        
        # Default: single task
        return [SubTask(
            subtask_id=str(uuid.uuid4())[:8],
            query=query,
            domain=Domain.GENERAL,
            task_type=TaskType.RESEARCH,
        )]
    
    def _extract_entities(self, query: str) -> list[str]:
        """Extract entity names from query."""
        # Simple pattern matching
        import re
        
        # "Compare X vs Y" or "X versus Y"
        vs_pattern = r'(\w+(?:\s+\w+)?)\s+(?:vs\.?|versus)\s+(\w+(?:\s+\w+)?)'
        matches = re.findall(vs_pattern, query, re.IGNORECASE)
        if matches:
            entities = []
            for match in matches:
                entities.extend(match)
            return list(set(entities))
        
        # "X, Y, and Z"
        list_pattern = r'(\w+(?:\s+\w+)?),\s*(\w+(?:\s+\w+)?),?\s+and\s+(\w+(?:\s+\w+)?)'
        matches = re.findall(list_pattern, query, re.IGNORECASE)
        if matches:
            return list(matches[0])
        
        return []
    
    def _extract_aspects(self, query: str) -> list[str]:
        """Extract aspects to analyze."""
        import re
        
        # "revenue, profit, and growth"
        aspect_pattern = r'(\w+),\s*(\w+),?\s+and\s+(\w+)'
        matches = re.findall(aspect_pattern, query, re.IGNORECASE)
        if matches:
            return list(matches[0])
        
        return []
    
    def _decompose_by_entity(self, query: str, entities: list[str]) -> list[SubTask]:
        """Create one subtask per entity."""
        subtasks = []
        for i, entity in enumerate(entities):
            subtasks.append(SubTask(
                subtask_id=str(uuid.uuid4())[:8],
                query=f"Research {entity}: {query}",
                domain=Domain.GENERAL,
                task_type=TaskType.RESEARCH,
                priority=i + 1,
            ))
        return subtasks
    
    def _decompose_by_aspect(self, query: str, aspects: list[str]) -> list[SubTask]:
        """Create one subtask per aspect."""
        subtasks = []
        for i, aspect in enumerate(aspects):
            subtasks.append(SubTask(
                subtask_id=str(uuid.uuid4())[:8],
                query=f"Analyze {aspect}: {query}",
                domain=Domain.GENERAL,
                task_type=TaskType.ANALYSIS,
                priority=i + 1,
            ))
        return subtasks
    
    def _decompose_comparison(self, query: str) -> list[SubTask]:
        """Decompose comparison into research + compare."""
        entities = self._extract_entities(query)
        subtasks = []
        
        # Research each entity
        for entity in entities:
            subtasks.append(SubTask(
                subtask_id=str(uuid.uuid4())[:8],
                query=f"Research {entity}",
                domain=Domain.GENERAL,
                task_type=TaskType.RESEARCH,
            ))
        
        # Final comparison (depends on all research)
        subtasks.append(SubTask(
            subtask_id=str(uuid.uuid4())[:8],
            query=query,
            domain=Domain.GENERAL,
            task_type=TaskType.COMPARE,
            dependencies=[st.subtask_id for st in subtasks],
        ))
        
        return subtasks
    
    def _decompose_comprehensive(self, query: str) -> list[SubTask]:
        """Decompose comprehensive research into phases."""
        return [
            SubTask(
                subtask_id=str(uuid.uuid4())[:8],
                query=f"Initial research: {query}",
                domain=Domain.GENERAL,
                task_type=TaskType.RESEARCH,
                priority=1,
            ),
            SubTask(
                subtask_id=str(uuid.uuid4())[:8],
                query=f"Deep dive: {query}",
                domain=Domain.GENERAL,
                task_type=TaskType.ANALYSIS,
                priority=2,
            ),
            SubTask(
                subtask_id=str(uuid.uuid4())[:8],
                query=f"Synthesize findings: {query}",
                domain=Domain.GENERAL,
                task_type=TaskType.SUMMARIZE,
                priority=3,
            ),
        ]


class AgentSpawner:
    """
    Spawn and manage parallel agents.
    
    Example:
        spawner = AgentSpawner(llm_callback=my_llm_call)
        
        # Analyze and create plan
        plan = await spawner.plan_execution("Compare Tesla vs Ford vs GM")
        
        # Execute swarm
        result = await spawner.execute_swarm(plan)
        
        # Get aggregated result
        print(result.aggregated_result)
    """
    
    def __init__(
        self,
        llm_callback: Callable[[str, str], Any] | None = None,
        max_parallel: int = 4,
    ):
        self.llm_callback = llm_callback
        self.max_parallel = max_parallel
        self.prompt_factory = PromptFactory()
        self.decomposer = TaskDecomposer()
    
    async def plan_execution(self, query: str) -> SpawnPlan:
        """Create execution plan for query."""
        # Decompose task
        subtasks = self.decomposer.decompose(query)
        
        # Generate prompts for each
        prompts = []
        for subtask in subtasks:
            context = PromptContext(
                query=subtask.query,
                domain=subtask.domain,
                task_type=subtask.task_type,
            )
            prompts.append(self.prompt_factory.generate(context))
        
        # Calculate parallelism based on resources
        max_parallel = await self._get_optimal_parallelism()
        
        return SpawnPlan(
            task_id=str(uuid.uuid4())[:8],
            subtasks=subtasks,
            max_parallel=max_parallel,
            prompts=prompts,
            estimated_time_seconds=len(subtasks) * 5.0,  # Rough estimate
        )
    
    async def execute_swarm(
        self,
        plan: SpawnPlan,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> SwarmResult:
        """Execute agent swarm based on plan."""
        swarm_result = SwarmResult(
            task_id=plan.task_id,
            agent_results=[],
            total_agents=len(plan.subtasks),
            started_at=datetime.utcnow(),
        )
        
        # Group subtasks by dependencies
        independent = [st for st in plan.subtasks if not st.dependencies]
        dependent = [st for st in plan.subtasks if st.dependencies]
        
        logger.info(
            f"Executing swarm: {len(independent)} independent, "
            f"{len(dependent)} dependent subtasks"
        )
        
        # Execute independent tasks in parallel
        semaphore = asyncio.Semaphore(plan.max_parallel)
        
        async def run_agent(subtask: SubTask, prompt: GeneratedPrompt) -> AgentResult:
            async with semaphore:
                return await self._run_single_agent(subtask, prompt)
        
        # Run independent tasks
        independent_prompts = plan.prompts[:len(independent)]
        tasks = [
            run_agent(st, prompt)
            for st, prompt in zip(independent, independent_prompts)
        ]
        
        independent_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in independent_results:
            if isinstance(result, AgentResult):
                swarm_result.agent_results.append(result)
                if result.status == AgentStatus.COMPLETED:
                    swarm_result.successful += 1
                else:
                    swarm_result.failed += 1
            else:
                swarm_result.failed += 1
        
        if progress_callback:
            progress_callback(len(independent), len(plan.subtasks))
        
        # Run dependent tasks sequentially (they need previous results)
        for i, subtask in enumerate(dependent):
            prompt_idx = len(independent) + i
            if prompt_idx < len(plan.prompts):
                result = await self._run_single_agent(
                    subtask,
                    plan.prompts[prompt_idx],
                    context_results=[
                        r for r in swarm_result.agent_results
                        if r.subtask_id in subtask.dependencies
                    ],
                )
                swarm_result.agent_results.append(result)
                
                if result.status == AgentStatus.COMPLETED:
                    swarm_result.successful += 1
                else:
                    swarm_result.failed += 1
        
        # Aggregate results
        swarm_result.completed_at = datetime.utcnow()
        swarm_result.aggregated_result = self._aggregate_results(swarm_result)
        
        logger.info(
            f"Swarm complete: {swarm_result.successful}/{swarm_result.total_agents} successful"
        )
        
        return swarm_result
    
    async def _run_single_agent(
        self,
        subtask: SubTask,
        prompt: GeneratedPrompt,
        context_results: list[AgentResult] | None = None,
    ) -> AgentResult:
        """Run a single agent."""
        agent_id = str(uuid.uuid4())[:8]
        result = AgentResult(
            agent_id=agent_id,
            subtask_id=subtask.subtask_id,
            status=AgentStatus.RUNNING,
            started_at=datetime.utcnow(),
            prompt_used=prompt.prompt[:200],  # Truncate for logging
        )
        
        try:
            # Build context from dependencies
            context = ""
            if context_results:
                findings = [r.result for r in context_results if r.result]
                context = f"Previous findings:\n{findings}\n\n"
            
            # Call LLM
            if self.llm_callback:
                llm_result = await self._call_llm(
                    system_prompt=prompt.prompt,
                    user_message=context + subtask.query,
                )
                result.result = llm_result
                result.status = AgentStatus.COMPLETED
            else:
                # Simulate for testing
                result.result = f"[Simulated result for: {subtask.query}]"
                result.status = AgentStatus.COMPLETED
                await asyncio.sleep(0.1)  # Simulate work
            
        except Exception as e:
            result.status = AgentStatus.FAILED
            result.error = str(e)
            logger.error(f"Agent {agent_id} failed: {e}")
        
        result.completed_at = datetime.utcnow()
        return result
    
    async def _call_llm(self, system_prompt: str, user_message: str) -> str:
        """Call LLM with prompt."""
        if self.llm_callback:
            result = self.llm_callback(system_prompt, user_message)
            if asyncio.iscoroutine(result):
                return await result
            return result
        return ""
    
    async def _get_optimal_parallelism(self) -> int:
        """Get optimal parallelism based on resources."""
        try:
            from shared.hardware import detect_hardware
            profile = detect_hardware()
            return min(self.max_parallel, profile.optimal_workers())
        except ImportError:
            return self.max_parallel
    
    def _aggregate_results(self, swarm: SwarmResult) -> dict:
        """Aggregate results from all agents."""
        successful_results = [
            r.result for r in swarm.agent_results
            if r.status == AgentStatus.COMPLETED and r.result
        ]
        
        return {
            "task_id": swarm.task_id,
            "total_agents": swarm.total_agents,
            "successful": swarm.successful,
            "failed": swarm.failed,
            "results": successful_results,
            "duration_seconds": (
                (swarm.completed_at - swarm.started_at).total_seconds()
                if swarm.started_at and swarm.completed_at else 0
            ),
        }


# Global instance
_spawner: AgentSpawner | None = None


def get_spawner(llm_callback: Callable | None = None) -> AgentSpawner:
    """Get or create global agent spawner."""
    global _spawner
    if _spawner is None:
        _spawner = AgentSpawner(llm_callback=llm_callback)
    return _spawner
