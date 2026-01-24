"""
Planner Node.

Decomposes research queries into sub-queries, hypotheses, and EXECUTION PLANS.
Each micro-task is routed to specific tools with dependencies and fallbacks.
"""

from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field
from shared.logging import get_logger
from shared.llm import OpenRouterProvider, LLMConfig
from shared.llm.provider import LLMMessage, LLMRole
import asyncio

logger = get_logger(__name__)


# ============================================================================
# Execution Plan Schema
# ============================================================================

class MicroTask(BaseModel):
    """A single micro-task in the execution plan."""
    task_id: str
    description: str
    tool: str  # Which tool to call
    inputs: dict[str, Any] = Field(default_factory=dict)
    depends_on: list[str] = Field(default_factory=list)  # task_ids this depends on
    fallback_tools: list[str] = Field(default_factory=list)  # If primary fails
    persist: bool = True  # Always persist by default (high threshold policy)
    phase: str = "research"  # Execution phase for parallel batching
    
    
class ExecutionPlan(BaseModel):
    """Full execution plan for a research query."""
    plan_id: str
    query: str
    micro_tasks: list[MicroTask] = Field(default_factory=list)
    phases: list[str] = Field(default_factory=list)  # Phase names
    estimated_tools: int = 0
    

# ============================================================================
# Tool Routing Logic
# ============================================================================

from services.orchestrator.core.tool_loader import route_to_tool_dynamic

def route_to_tool(task_description: str) -> tuple[str, list[str]]:
    """
    Route a micro-task to the appropriate tool based on keywords.
    Delegates to dynamic loader.
    """
    return route_to_tool_dynamic(task_description)


# ============================================================================
# Planner Node
# ============================================================================

async def planner_node(state: dict[str, Any]) -> dict[str, Any]:
    """
    Planner node: Decompose query into sub-queries AND execution plan.
    
    Takes a complex research query and breaks it down into:
    - Sub-queries (atomic research questions)
    - Hypotheses (testable claims)
    - Execution plan (micro-tasks with tool routing)
    
    Args:
        state: Current graph state with 'query'
        
    Returns:
        Updated state with 'sub_queries', 'hypotheses', 'execution_plan'
    """
    logger.info("Planner: Decomposing query", extra={"query": state.get("query", "")[:100]})
    
    query = state.get("query", "")
    
    # ============================================================
    # RELATED FACT LOOKUP (Semantic Search for Past Research)
    # ============================================================
    related_facts = []
    try:
        import asyncio
        from services.rag_service.core.fact_store import FactStore
        store = FactStore()
        
        # Search for related past research with timeout to avoid blocking
        related_facts = await asyncio.wait_for(
            store.search(query, limit=5),
            timeout=5.0  # 5 second timeout to avoid blocking research
        )
        
        if related_facts:
            logger.info(f"Planner: Found {len(related_facts)} related past facts")
            state["related_facts"] = [
                {"entity": f.entity, "value": f.value[:200], "source": f.source_url}
                for f in related_facts
            ]
    except asyncio.TimeoutError:
        logger.warning("Planner: Related fact lookup timed out, skipping")
    except Exception as e:
        logger.debug(f"Related fact lookup skipped: {e}")
    
    # Use LLM to decompose query
    try:
        import os
        if os.getenv("OPENROUTER_API_KEY"):
            provider = OpenRouterProvider()
            from shared.config import get_settings
            app_config = get_settings()
            
            config = LLMConfig(
                model=app_config.models.planner_model,
                temperature=0.3,
                max_tokens=32768,  # Maximum for task generation
            )
            
            # Discover relevant tools (INTELLIGENCE INJECTION)
            try:
                from services.mcp_host.core.session_registry import get_session_registry
                registry = get_session_registry()
                # Get all tools (Plan: Maybe in future use vector search here?)
                # For now, listing all is safer for "Awareness"
                
                # Check if registry is populated, if not, might need a moment or just rely on what's there
                # Since Planner is usually called AFTER host start, it should be fine.
                # If running purely standalone without host, this might be empty.
                
                # We can't easily wait for async list_all_tools inside this sync/async boundary without blocking
                # But planner_node is async.
                
                # NOTE: listing all tools on every request might be slow if many tools.
                # Optimization: Cache this or use search_tools if implemented in SessionRegistry
                # SessionRegistry doesn't have search_tools yet.
                # Let's just peer into registry.tool_to_server which is instant RAM access
                
                if not registry.tool_to_server:
                     # Try to list if empty (First run)
                     # Use quiet timeout
                     try:
                        await asyncio.wait_for(registry.list_all_tools(), timeout=2.0)
                     except asyncio.TimeoutError:
                        pass
                
                known_tools = list(registry.tool_to_server.keys())
                
                # Format for LLM
                tools_context = f"ACTIVE SYSTEM TOOLS ({len(known_tools)} available):\n"
                tools_context += ", ".join(known_tools)
                
            except Exception as e:
                logger.warning(f"Planner tool discovery failed: {e}")
                tools_context = "Basic tools available (Discovery Failed)."

            messages = [
                LLMMessage(
                    role=LLMRole.SYSTEM,
                    content=f"""You are a research planner with the resourcefulness of an elite engineer (e.g., Tony Stark).
Your mission is to decompose complex queries into actionable execution plans, finding creative ways to get data even when no direct tool exists.

AVAILABLE TOOLS (Use these if relevant):
{tools_context}

CRITICAL: GENERATE MAXIMUM MICRO-TASKS (up to 32768 tasks).
- Each individual data point = 1 task
- If analyzing 800 companies, create 800 individual tasks
- If scraping 100 pages, create 100 separate tasks
- MORE GRANULAR is ALWAYS BETTER for parallel execution

CORE PHILOSOPHY: IMPROVISE AND BUILD.
Do not be limited by "standard" procedures. If a specific dataset/tool is missing, plan to **build it yourself** using the available primitive tools (like Python code and Web Search).
- Treat the web as a raw database to be scraped and parsed.
- Treat Python as your universal adapter to process that raw data.

RULES FOR FINANCIAL DATA:
1. Do NOT use `web_search` to find data tables if better tools exist. Use `get_idx_tickers` for identifying companies.
2. Use `execute_code` (Python) to fetch financial data (e.g. using yfinance) or to perform calculations.
3. You cannot 'Filter' data you do not have. Your first step must always be 'Acquire Dataset'.

PHASES FOR LARGE TASKS (CRITICAL: PREVENT RACE CONDITIONS):
1. DISCOVERY - Find all entities (companies, URLs, documents)
2. COLLECTION - Create ONE task per entity to collect data (e.g. "Download data").
3. VALIDATION - Verify collected data
4. ANALYSIS - Process and calculate (MUST depend on Collection)
5. SYNTHESIS - Combine results

IMPORTANT: Do not mix "Fetching" and "Analyzing" in the same description. Split them.
- BAD: "Fetch data for ASII and calculate Dupont" (Atomic violation)
- GOOD: "Task 1: Fetch data for ASII" (Collection) -> "Task 2: Calculate Dupont for ASII" (Analysis)

Output format:
SUB-QUERIES:
1. [question]
...

HYPOTHESES:
1. [claim]
...

PHASE: [PHASE_NAME]
1. [action verb] [what] [where/how]
2. ...

PHASE: [NEXT_PHASE_NAME]
1. [action that depends on previous phase]
...

Be specific about:
- What data to collect (create one task per item)
- What calculations to perform
- What to extract from documents
- What relationships to map"""
                ),
                LLMMessage(role=LLMRole.USER, content=f"Decompose this research query:\n\n{query}")
            ]
            
            response = await provider.complete(messages, config)
            
            # Parse response
            sub_queries = []
            hypotheses = []
            # New structure: Ordered dictionary of phases
            execution_phases = {}  # { "discovery": ["step 1", "step 2"], ... }
            current_phase_name = "default"
            
            lines = response.content.split("\n")
            current_section = None
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                if "SUB-QUERIES" in line.upper():
                    current_section = "sub_queries"
                    continue
                elif "HYPOTHESES" in line.upper():
                    current_section = "hypotheses"
                    continue
                elif "PHASE:" in line.upper():
                    current_section = "execution"
                    # Extract phase name: "PHASE: DISCOVERY" -> "discovery"
                    try:
                        current_phase_name = line.split(":", 1)[1].strip().lower()
                    except:
                        current_phase_name = "unknown"
                    if current_phase_name not in execution_phases:
                        execution_phases[current_phase_name] = []
                    continue
                elif "EXECUTION" in line.upper():
                    # Fallback for old prompt style or if LLM forgets PHASE header
                    current_section = "execution"
                    continue
                
                # Extract content
                text = None
                if line[0].isdigit() and "." in line:
                    text = line.split(".", 1)[1].strip()
                elif line.startswith("-") or line.startswith("*") or line.startswith("•"):
                    text = line[1:].strip()
                else:
                    # Allow non-bullet text if it looks like a task in execution section
                    if current_section == "execution" and len(line) > 10:
                        text = line
                
                if text and current_section:
                    if current_section == "sub_queries":
                        sub_queries.append(text)
                    elif current_section == "hypotheses":
                        hypotheses.append(text)
                    elif current_section == "execution":
                        if current_phase_name not in execution_phases:
                            execution_phases[current_phase_name] = []
                        execution_phases[current_phase_name].append(text)
            
            state["sub_queries"] = sub_queries or [query]
            state["hypotheses"] = hypotheses
            
            # Generate execution plan from phases
            execution_plan = generate_execution_plan_phased(query, execution_phases)
            state["execution_plan"] = execution_plan.model_dump()
            
            logger.info(
                f"Planner: Generated {len(sub_queries)} sub-queries, "
                f"{len(hypotheses)} hypotheses, "
                f"{len(execution_plan.micro_tasks)} micro-tasks across {len(execution_phases)} phases"
            )
            
        else:
            # Fallback without LLM
            state["sub_queries"] = [query]
            state["hypotheses"] = []
            state["execution_plan"] = generate_execution_plan_phased(query, {"research": [query]}).model_dump()
            logger.info("Planner: No LLM, using query as-is")
            
    except Exception as e:
        logger.error(f"Planner error: {e}")
        state["sub_queries"] = [query]
        state["hypotheses"] = []
        state["execution_plan"] = generate_execution_plan_phased(query, {"research": [query]}).model_dump()
    
    state["status"] = "planning_complete"
    return state


def generate_execution_plan_phased(query: str, execution_phases: dict[str, list[str]]) -> ExecutionPlan:
    """
    Generate execution plan from Phased LLM output.
    
    STRICT DEPENDENCY LOGIC:
    - All tasks in Phase N depend on ALL tasks in Phase N-1.
    - Tasks within the same Phase are independent (Parallel).
    """
    import uuid
    
    micro_tasks = []
    task_id_counter = 1
    
    # Track tasks by phase for dependency linking
    # We maintain order of phases as they appeared in the dict (insertion order preserved in Py3.7+)
    phase_names = list(execution_phases.keys())
    phase_task_ids: dict[str, list[str]] = {p: [] for p in phase_names}
    
    for i, phase_name in enumerate(phase_names):
        steps = execution_phases[phase_name]
        
        # Determine dependencies: All tasks from previous phase
        depends_on = []
        if i > 0:
            previous_phase = phase_names[i-1]
            depends_on = phase_task_ids[previous_phase]
            
        for step in steps:
            task_id = f"task_{task_id_counter}"
            task_id_counter += 1
            
            primary_tool, fallbacks = route_to_tool(step)
            
            # Handle special case: execute_code needs "python_server" usually
            # route_to_tool logic might need checking, but usually returns 'execute_code'
            
            micro_task = MicroTask(
                task_id=task_id,
                description=step,
                tool=primary_tool,
                inputs={"query": step},  # Basic input, refined by researcher_node
                depends_on=depends_on,   # STRICT DEPENDENCY
                fallback_tools=fallbacks,
                persist=True,
                phase=phase_name,
            )
            
            micro_tasks.append(micro_task)
            phase_task_ids[phase_name].append(task_id)
            
    return ExecutionPlan(
        plan_id=f"plan_{uuid.uuid4().hex[:8]}",
        query=query,
        micro_tasks=micro_tasks,
        phases=phase_names,
        estimated_tools=len(micro_tasks),
    )

