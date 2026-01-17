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

TOOL_CAPABILITIES = {
    # Search & Research
    "web_search": {
        "keywords": ["search", "find", "look up", "what is", "who is", "list of"],
        "server": "search_server",
        "fallbacks": ["news_search"],
    },
    "news_search": {
        "keywords": ["news", "recent", "latest", "announcement", "press release"],
        "server": "search_server",
        "fallbacks": ["web_search"],
    },
    # Data Collection
    "scrape_url": {
        "keywords": ["scrape", "extract", "download", "annual report", "website", "page"],
        "server": "scraper_server",
        "fallbacks": ["web_search"],
    },
    "fetch_data": {
        "keywords": ["data", "historical", "OHLCV", "price", "volume", "stock", "ticker"],
        "server": "data_sources_server",
        "fallbacks": ["web_search"],
    },
    # Analysis
    "run_python": {
        "keywords": ["calculate", "compute", "analyze", "algorithm", "filter", "ratio", "growth"],
        "server": "python_server",
        "fallbacks": [],
    },
    "build_graph": {
        "keywords": ["graph", "relationship", "entity", "network", "connection", "ownership"],
        "server": "analytics_server",
        "fallbacks": [],
    },
    # Document Processing
    "parse_document": {
        "keywords": ["parse", "read", "extract from", "PDF", "report", "financial statement"],
        "server": "document_server",
        "fallbacks": ["scrape_url"],
    },
}


def route_to_tool(task_description: str) -> tuple[str, list[str]]:
    """
    Route a micro-task to the appropriate tool based on keywords.
    
    Returns:
        (primary_tool, fallback_tools)
    """
    task_lower = task_description.lower()
    
    # Score each tool based on keyword matches
    scores = {}
    for tool, config in TOOL_CAPABILITIES.items():
        score = sum(1 for kw in config["keywords"] if kw in task_lower)
        if score > 0:
            scores[tool] = score
    
    if not scores:
        # Default to web_search
        return "web_search", ["news_search"]
    
    # Get highest scoring tool
    best_tool = max(scores, key=scores.get)
    fallbacks = TOOL_CAPABILITIES[best_tool]["fallbacks"]
    
    return best_tool, fallbacks


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
    
    # Use LLM to decompose query
    try:
        import os
        if os.getenv("OPENROUTER_API_KEY"):
            provider = OpenRouterProvider()
            config = LLMConfig(
                model="nvidia/nemotron-3-nano-30b-a3b:free",
                temperature=0.3,
                max_tokens=1000,  # Increased for execution plan
            )
            
            messages = [
                LLMMessage(
                    role=LLMRole.SYSTEM,
                    content="""You are a research planner. Decompose queries into sub-questions AND execution steps.

Output format:
SUB-QUERIES:
1. [question - be specific about what data/information is needed]
2. [question]

HYPOTHESES:
1. [testable claim]
2. [testable claim]

EXECUTION-STEPS:
1. [action verb] [what] [where/how] - e.g. "Search for list of all IDX companies"
2. [action verb] [what] [where/how] - e.g. "Download historical price data for each ticker"
3. [action verb] [what] [where/how] - e.g. "Calculate revenue growth rate using financial data"
4. [action verb] [what] [where/how] - e.g. "Scrape annual reports from company websites"
5. [action verb] [what] [where/how] - e.g. "Build ownership graph from extracted entities"

Be specific about:
- What data to collect
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
            execution_steps = []
            
            lines = response.content.split("\n")
            current_section = None
            
            for line in lines:
                line = line.strip()
                if "SUB-QUERIES" in line.upper():
                    current_section = "sub_queries"
                elif "HYPOTHESES" in line.upper():
                    current_section = "hypotheses"
                elif "EXECUTION" in line.upper():
                    current_section = "execution"
                elif line and line[0].isdigit() and "." in line:
                    text = line.split(".", 1)[1].strip() if "." in line else line
                    if current_section == "sub_queries":
                        sub_queries.append(text)
                    elif current_section == "hypotheses":
                        hypotheses.append(text)
                    elif current_section == "execution":
                        execution_steps.append(text)
            
            state["sub_queries"] = sub_queries or [query]
            state["hypotheses"] = hypotheses
            
            # Generate execution plan from steps
            execution_plan = generate_execution_plan(query, execution_steps)
            state["execution_plan"] = execution_plan.model_dump()
            
            logger.info(
                f"Planner: Generated {len(sub_queries)} sub-queries, "
                f"{len(hypotheses)} hypotheses, "
                f"{len(execution_plan.micro_tasks)} micro-tasks"
            )
            
        else:
            # Fallback without LLM
            state["sub_queries"] = [query]
            state["hypotheses"] = []
            state["execution_plan"] = generate_execution_plan(query, [query]).model_dump()
            logger.info("Planner: No LLM, using query as-is")
            
    except Exception as e:
        logger.error(f"Planner error: {e}")
        state["sub_queries"] = [query]
        state["hypotheses"] = []
        state["execution_plan"] = generate_execution_plan(query, [query]).model_dump()
    
    state["status"] = "planning_complete"
    return state


def generate_execution_plan(query: str, execution_steps: list[str]) -> ExecutionPlan:
    """
    Generate execution plan from LLM-generated steps.
    Routes each step to appropriate tools.
    """
    import uuid
    
    micro_tasks = []
    phases = set()
    
    for i, step in enumerate(execution_steps):
        task_id = f"task_{i+1}"
        
        # Route to tool
        primary_tool, fallbacks = route_to_tool(step)
        
        # Determine phase based on tool
        if primary_tool in ["web_search", "news_search", "fetch_data"]:
            phase = "data_collection"
        elif primary_tool in ["scrape_url", "parse_document"]:
            phase = "extraction"
        elif primary_tool in ["run_python"]:
            phase = "analysis"
        elif primary_tool in ["build_graph"]:
            phase = "synthesis"
        else:
            phase = "research"
        
        phases.add(phase)
        
        # Dependencies: each task depends on previous tasks in same phase
        depends_on = []
        if i > 0:
            # Simple dependency: each task depends on the previous
            depends_on = [f"task_{i}"]
        
        micro_task = MicroTask(
            task_id=task_id,
            description=step,
            tool=primary_tool,
            inputs={"query": step},
            depends_on=depends_on,
            fallback_tools=fallbacks,
            persist=True,  # Always persist (high threshold policy)
        )
        micro_tasks.append(micro_task)
    
    return ExecutionPlan(
        plan_id=f"plan_{uuid.uuid4().hex[:8]}",
        query=query,
        micro_tasks=micro_tasks,
        phases=sorted(phases),
        estimated_tools=len(micro_tasks),
    )

