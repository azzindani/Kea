"""
Agent Spawner and Scaler.

Self-multiplying agent system for massive tasks.
Decomposes tasks, spawns specialized agents, aggregates results.
"""

from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass, field, replace
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
from services.orchestrator.core.utils import build_tool_inputs, extract_url_from_text
from services.mcp_host.core.models import ToolResponse


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
    preferred_tool: str | None = None  # Explicit tool override from Planner
    arguments: dict[str, Any] = field(default_factory=dict)  # Standard I/O arguments


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
    source: str | None = None
    
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

    @property
    def duration_seconds(self) -> float:
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return 0.0


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
        max_subtasks: int = 20,
        strategy: str = "auto",
    ) -> list[SubTask]:
        """Decompose query into subtasks. Limit is now dynamic via complexity classifier."""
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
        logger.debug(result.aggregated_result)
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
    
    def _expand_plan(self, plan: SpawnPlan) -> SpawnPlan:
        """
        Bucket Pattern: Expand massive tasks into parallel shards.
        If a task asks for '10k data' or 'massive collection', spawn multiple farmers.
        """
        expanded_sub = []
        expanded_prompts = []
        
        for i, task in enumerate(plan.subtasks):
            query_lower = task.query.lower()
            
            # Heuristic for expansion
            is_massive = any(w in query_lower for w in ["massive", "10k", "10,000", "all items", "bucket", "parallel"])
            
            if is_massive and task.task_type in [TaskType.EXTRACT, TaskType.RESEARCH]:
                # Determine expansion factor
                factor = 5  # Default shards
                if "100k" in query_lower: factor = 20
                elif "10k" in query_lower or "10,000" in query_lower: factor = 10
                elif "50k" in query_lower: factor = 15
                
                # Cap at plan's max_parallel (now set dynamically by complexity classifier)
                factor = min(factor, plan.max_parallel or 15)
                
                logger.info(f"💥 Expanding massive task '{task.query[:30]}...' into {factor} parallel shards")
                
                # Create shards
                for j in range(1, factor + 1):
                    # Suffix query with batch info (e.g., 'Page 1', 'Batch 1')
                    # This allows build_tool_inputs to map it to pagination args later
                    new_query = f"{task.query} (Batch {j})"
                    
                    new_task = replace(
                        task, 
                        subtask_id=f"{task.subtask_id}_{j}", 
                        query=new_query
                    )
                    expanded_sub.append(new_task)
                    
                    # Replicate prompt (same instructions, just different slice of data)
                    if i < len(plan.prompts):
                        # We don't need deep copy of prompt object, reusing is fine OR shallow copy
                        # GeneratedPrompt is dataclass, immutable-ish
                        expanded_prompts.append(plan.prompts[i])
            else:
                # Keep original
                expanded_sub.append(task)
                if i < len(plan.prompts):
                    expanded_prompts.append(plan.prompts[i])
        
        # Update plan
        plan.subtasks = expanded_sub
        plan.prompts = expanded_prompts
        # Update estimate
        plan.estimated_time_seconds = len(expanded_sub) * 3.0 # Parallel gain
        
        return plan

    async def execute_swarm(
        self,
        plan: SpawnPlan,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> SwarmResult:
        """Execute agent swarm based on plan."""
        
        # 1. Expand Plan (The "Bucket Pattern")
        plan = self._expand_plan(plan)
        
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
        """Run a single agent with REAL execution capabilities."""
        agent_id = str(uuid.uuid4())[:8]
        result = AgentResult(
            agent_id=agent_id,
            subtask_id=subtask.subtask_id,
            status=AgentStatus.RUNNING,
            started_at=datetime.utcnow(),
            prompt_used=prompt.prompt[:200],
        )
        
        logger.info(f"🤖 Agent {agent_id} starting task: {subtask.query[:60]}...")
        
        try:
            # 1. Build Context
            context_str = ""
            
            # Local Swarm Context
            if context_results:
                findings = [str(r.result) for r in context_results if r.result]
                context_str += f"Context from dependent tasks:\n" + "\n".join(findings) + "\n\n"

            # Global Project Context (Crucial for multi-phase workflows)
            try:
                from shared.context_pool import get_context_pool
                ctx = get_context_pool()
                if ctx.fact_pool:
                    global_findings = [f.get("text", "")[:500] for f in ctx.fact_pool[-10:]] # Last 10 facts, truncated
                    context_str += f"Global Context (Previous Phases):\n" + "\n".join(global_findings) + "\n\n"
            except Exception as e:
                logger.warning(f"Failed to fetch global context for LLM: {e}")
            
            # 2. Determine Action (LLM or Direct Tool)
            # For this implementation, we treat the agent as a "Smart Worker"
            # It uses the LLM to decide which tool to call from the registry
            
            from services.mcp_host.core.session_registry import get_session_registry
            registry = get_session_registry()
            
            # Simple heuristic: If it looks like a direct question, ask LLM. 
            # If it looks like "Search for X", assume tool use.
            # We'll use a CodeGenerator prompt to get the tool loop.
            
            response = ""
            
            # Use the LLM callback if provided (The "Brain")
            if self.llm_callback and not subtask.preferred_tool:
                full_prompt = f"{prompt.prompt}\n\nTask: {subtask.query}\n{context_str}"
                response = await self._call_llm(full_prompt, subtask.query)
            else:
                # Fallback to direct tool execution (The "Hands")
                # PRIORITY 1: Explicit Tool from Planner
                if subtask.preferred_tool:
                    tool_name = subtask.preferred_tool
                    server_name = None
                    
                    # Handle "server.tool" format (e.g., "yfinance_server.get_income_statement_quarterly")
                    if "." in tool_name and "_server." in tool_name:
                        parts = tool_name.split(".", 1)
                        server_name = parts[0]
                        tool_name = parts[1]
                        logger.debug(f"   📌 Parsed server.tool format: server={server_name}, tool={tool_name}")
                    else:
                        # Lookup server from static registry
                        server_name = registry.get_server_for_tool(tool_name)
                    
                    if not server_name:
                         # Try mapping legacy names if needed
                         if tool_name == "run_python": tool_name = "execute_code"
                         server_name = registry.get_server_for_tool(tool_name)

                    if server_name:
                        try:
                            session = await registry.get_session(server_name)
                            
                            # Prepare facts for context-aware parameters
                            collected_facts = []
                            
                            # 1. Local Context (from this swarm's dependencies)
                            if context_results:
                                for r in context_results:
                                    if r.result:
                                        collected_facts.append({"text": str(r.result)})
                            
                            # 2. Global Context (from previous phases)
                            try:
                                from shared.context_pool import get_context_pool
                                ctx = get_context_pool()
                                
                                # Add facts from pool
                                for fact in ctx.fact_pool:
                                    collected_facts.append({"text": fact.get("text", "")})
                                
                                # Add specific data items if short enough
                                for key, item in ctx.data_pool.items():
                                    data_str = str(item.get("data", ""))
                                    if len(data_str) < 5000: # Limit size
                                        collected_facts.append({"text": f"Data {key}: {data_str}"})
                                        
                            except Exception as e:
                                logger.warning(f"Failed to fetch global context: {e}")
                            
                            # =========================================================
                            # GLASS-BOX EXECUTION WITH SELF-CORRECTION
                            # =========================================================
                            if tool_name in ["execute_code", "run_python"]:
                                from services.orchestrator.agents.code_generator import generate_python_code

                                
                                attempt = 0
                                max_attempts = 3
                                previous_code = None
                                previous_error = None
                                
                                while attempt < max_attempts:
                                    attempt += 1
                                    
                                    # 1. GENERATE CODE (Autonomous)
                                    logger.info(f"   🧠 Generating Python Code (Attempt {attempt})...")
                                    # Only fetch files once to save IO
                                    if attempt == 1:
                                        files = []
                                        try:
                                            if hasattr(ctx, 'list_files'):
                                                files = ctx.list_files()
                                        except: pass
                                    
                                    code = await generate_python_code(
                                        task_description=subtask.query,
                                        facts=[{"text": f.get("text")} for f in collected_facts],
                                        file_artifacts=files,
                                        previous_code=previous_code,
                                        previous_error=previous_error
                                    )
                                    
                                    # 2. GLASS-BOX LOGGING (Show user the code)
                                    logger.info(f"   📝 CODE TO EXECUTE:\n{'-'*40}\n{code}\n{'-'*40}")
                                    
                                    # 3. EXECUTE
                                    args = {"code": code}
                                    tool_res = await session.call_tool("execute_code", args)
                                    
                                    # 4. EVALUATE
                                    # Normalize Result using Standard I/O
                                    norm_res = ToolResponse.from_mcp_result("execute_code", tool_res)
                                    
                                    if not norm_res.is_error:
                                        # Success!
                                        response = f"Swarm Tool Result (execute_code):\n {norm_res.output.get_for_llm()[:8000]}"
                                        
                                        logger.info(f"   ✅ EXECUTION SUCCESS:\n{norm_res.output.text[:1000]}...")
                                        break
                                    else:
                                        # Failure - Capture error for retry
                                        error_msg = norm_res.output.error or str(norm_res.output.text)
                                        logger.warning(f"   ❌ Execution Failed (Attempt {attempt}): {error_msg[:200]}")
                                        
                                        previous_code = code
                                        previous_error = error_msg
                                        
                                        if attempt == max_attempts:
                                            response = f"Swarm Tool Failed after {max_attempts} attempts: {error_msg}"
                                            logger.error("   🛑 Giving up on code generation.")
                            
                            else:

                                # STANDARD TOOL EXECUTION (Non-Code)
                                # 0. Use Explicit Arguments if available (Standard I/O)
                                if subtask.arguments:
                                    args = subtask.arguments
                                    logger.info(f"   🎯 Used Explicit Arguments from Planner: {args}")
                                else:
                                    # 1. Try heuristic mapping first
                                    args = build_tool_inputs(
                                        tool_name=tool_name, 
                                        description=subtask.query, 
                                        original_inputs={}, 
                                        collected_facts=collected_facts
                                    )
                                
                                # 2. DYNAMIC ARGUMENT GENERATION (The "Smart Hands" fix)
                                # If heuristics failed (returned None or generic 'query') and it's complex tool
                                # We MUST ask the LLM how to call it based on the schema.
                                is_generic_arg = args is None or (len(args) == 1 and "query" in args)
                                is_known_simple = tool_name in ["web_search", "news_search", "fetch_data"]
                                
                                if is_generic_arg and not is_known_simple:
                                    try:
                                        logger.info(f"   🔧 Fetching schema for complex tool: {tool_name}")
                                        # Fetch schema from the live session
                                        tools_list = await session.list_tools()
                                        target_tool = next((t for t in tools_list if t.name == tool_name), None)
                                        
                                        if target_tool:
                                            # Use LLM to map Task -> Arguments
                                            schema_str = str(target_tool.inputSchema)
                                            logger.info(f"   🧠 Mapping arguments using LLM for {tool_name}...")
                                            
                                            arg_prompt = f"""You are an API Argument Generator.
Tool: {tool_name}
Schema: {schema_str}
Task: {subtask.query}

Context Facts:
{str(collected_facts)[:1000] if collected_facts else "None"}

CRITICAL: Return ONLY valid JSON for the tool arguments. No markdown, no explanation."""
                                            
                                            arg_json = await self._call_llm(arg_prompt, "Generate JSON")
                                            
                                            # Clean and parse JSON
                                            import json
                                            cleaned_json = arg_json.replace("```json", "").replace("```", "").strip()
                                            try:
                                                args = json.loads(cleaned_json)
                                                logger.info(f"   🎯 Generated Dynamic Args: {args}")
                                            except:
                                                logger.warning(f"   ⚠️ Failed to parse generated args: {cleaned_json[:50]}")
                                                # Fallback to generic
                                                if args is None: args = {"query": subtask.query}
                                        else:
                                            logger.warning(f"   ⚠️ Tool {tool_name} not found in session list.")
                                    except Exception as map_err:
                                        logger.warning(f"   ⚠️ Dynamic Argument Generation Failed: {map_err}")

                                if args is None:
                                    args = {"query": subtask.query}

                                tool_res = await session.call_tool(tool_name, args)
                                
                                # Normalize Output
                                norm_res = ToolResponse.from_mcp_result(tool_name, tool_res)
                                
                                if not norm_res.is_error:
                                    response = f"Swarm Tool Result ({tool_name}):\n {norm_res.output.get_for_llm()[:8000]}"
                                else:
                                    response = f"Swarm Tool Failed ({tool_name}): {norm_res.output.error or norm_res.output.text}"
                            # =========================================================
                        except Exception as e:
                            response = f"Swarm Tool Exception ({tool_name}): {e}"
                    else:
                        response = f"Tool {subtask.preferred_tool} not found in registry."

                # PRIORITY 2: Heuristic Routing (Legacy)
                elif "search" in subtask.query.lower() or "find" in subtask.query.lower():
                    tool_name = "web_search"
                    server_name = registry.get_server_for_tool(tool_name) or "search_server"
                    
                    try:
                        session = await registry.get_session(server_name)
                        tool_res = await session.call_tool(tool_name, {"query": subtask.query})
                        
                        if not tool_res.isError:
                            response = f"Search Results: {str(tool_res.content)[:500]}..."
                        else:
                            response = f"Search Failed: {tool_res.content}"
                    except Exception as e:
                        response = f"Search failed: {e}"

                else:
                    # Default: Just think about it (Simulated thought, or real if connected to Planner)
                    # Since we want "Real Pipeline", we'll attempt a generic Python solve
                    tool_name = "execute_code" 
                    server_name = registry.get_server_for_tool(tool_name) or "python_server"
                    
                    try:
                        session = await registry.get_session(server_name)
                        # Generate REAL code instead of dummy
                        from services.orchestrator.agents.code_generator import generate_python_code
                        
                        # Gather context for generator
                        facts = []
                        if context_results:
                            for r in context_results:
                                if r.result:
                                    facts.append({"text": str(r.result)})
                        
                        # Autonomous generation
                        code = await generate_python_code(
                            task_description=subtask.query,
                            facts=facts
                        )
                        
                        code_res = await session.call_tool(tool_name, {
                            "code": code
                        })
                        response = f"Execution Result: {str(code_res.content)}"
                    except Exception as e:
                        response = f"Exec failed: {e}"

            result.result = response
            # Extract source metadata if available (provenance tracking)
            if response:
                result.source = extract_url_from_text(str(response))

            # Determine agent status based on result quality
            # If tool execution failed, mark agent as FAILED (not COMPLETED)
            if response and isinstance(response, str):
                error_indicators = [
                    "Swarm Tool Failed",
                    "Swarm Tool Exception",
                    "Tool reported an error",
                    "Exec failed:",
                    "LLM Failure"
                ]

                has_error = any(indicator in response for indicator in error_indicators)

                if has_error:
                    result.status = AgentStatus.FAILED
                    result.error = response[:200]  # Store error message
                    logger.warning(f"⚠️ Agent {agent_id} completed with tool failure.")
                else:
                    result.status = AgentStatus.COMPLETED
                    logger.info(f"✅ Agent {agent_id} completed.")
            else:
                result.status = AgentStatus.COMPLETED
                logger.info(f"✅ Agent {agent_id} completed.")
            
        except Exception as e:
            result.status = AgentStatus.FAILED
            result.error = str(e)
            logger.error(f"❌ Agent {agent_id} failed: {e}")
        
        result.completed_at = datetime.utcnow()
        return result
    
    async def _call_llm(self, system_prompt: str, user_message: str) -> str:
        """Call LLM with prompt."""
        if self.llm_callback:
            try:
                # Support both async and sync callbacks
                res = self.llm_callback(system_prompt, user_message)
                if asyncio.iscoroutine(res):
                    return await res
                return res
            except Exception as e:
                logger.error(f"Agent LLM Call Failed: {e}")
                return "LLM Failure"
        return ""
    
    async def _get_optimal_parallelism(self) -> int:
        """Get optimal parallelism based on resources."""
        try:
            from shared.hardware.detector import detect_hardware
            hw = detect_hardware()
            return min(self.max_parallel, hw.optimal_workers())
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
    """Get or create global agent spawner.

    If an llm_callback is provided and the spawner already exists but has no
    callback, the callback is hot-wired onto the existing instance so that
    the microplanner and agentic nodes can use LLM replanning.
    """
    global _spawner
    if _spawner is None:
        _spawner = AgentSpawner(llm_callback=llm_callback)
    elif llm_callback is not None and _spawner.llm_callback is None:
        _spawner.llm_callback = llm_callback
    return _spawner
