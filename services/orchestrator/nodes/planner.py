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

TOOL_CAPABILITIES = {
    # ===========================================
    # SEARCH TOOLS
    # ===========================================
    "web_search": {
        "keywords": ["search", "find", "look up", "what is", "who is", "list of", "query"],
        "server": "search_server",
        "fallbacks": ["news_search", "human_search"],
    },
    "news_search": {
        "keywords": ["news", "recent", "latest", "announcement", "press release"],
        "server": "search_server",
        "fallbacks": ["web_search"],
    },
    "human_search": {
        "keywords": ["research", "investigate", "thorough", "comprehensive", "deep search"],
        "server": "browser_agent_server",
        "fallbacks": ["web_search"],
    },
    
    # ===========================================
    # CRAWLER TOOLS (recursive, unlimited depth)
    # ===========================================
    "web_crawler": {
        "keywords": ["crawl", "explore", "recursive", "all pages", "entire site", "sitemap"],
        "server": "crawler_server",
        "fallbacks": ["link_extractor", "scrape_url"],
    },
    "sitemap_parser": {
        "keywords": ["sitemap", "site map", "all urls", "url list"],
        "server": "crawler_server",
        "fallbacks": ["web_crawler"],
    },
    "link_extractor": {
        "keywords": ["extract links", "get links", "find links", "outbound", "href"],
        "server": "crawler_server",
        "fallbacks": ["web_search"],
    },
    
    # ===========================================
    # SCRAPING TOOLS
    # ===========================================
    "fetch_url": {
        "keywords": ["scrape", "extract", "download", "annual report", "website", "page", "fetch", "read url"],
        "server": "scraper_server",
        "fallbacks": ["web_search", "browser_scrape"],
    },
    "execute_code": {
        "keywords": ["data", "historical", "OHLCV", "price", "volume", "stock", "ticker", "API", "python", "calculate", "dataframe"],
        "server": "python_server",
        "fallbacks": ["web_search"],
    },
    
    # ===========================================
    # FINANCIAL TOOLS
    # ===========================================
    "get_idx_tickers": {
        "keywords": ["IDX", "JKSE", "companies", "list of stocks", "ticker list", "universe"],
        "server": "mcp_host",
        "fallbacks": ["web_search"],
    },
    
    # ===========================================
    # QUALITATIVE TOOLS
    # ===========================================
    "text_coding": {
        "keywords": ["code text", "qualitative coding", "label themes", "categorize text", "nlp coding"],
        "server": "qualitative_server",
        "fallbacks": ["theme_extractor", "execute_code"],
    },
    "entity_extractor": {
        "keywords": ["extract entities", "find people", "identify orgs", "ner", "named entity"],
        "server": "qualitative_server",
        "fallbacks": ["execute_code"],
    },
    "investigation_graph_add": {
        "keywords": ["add to graph", "map relationship", "build graph", "connect entity"],
        "server": "qualitative_server",
        "fallbacks": ["connection_mapper"],
    },
    "investigation_graph_query": {
        "keywords": ["query graph", "search graph", "find path", "graph lookup"],
        "server": "qualitative_server",
        "fallbacks": ["text_coding"],
    },

    # ===========================================
    # ML TOOLS
    # ===========================================
    "auto_ml": {
        "keywords": ["train model", "predict", "machine learning", "classification", "regression", "ml"],
        "server": "ml_server",
        "fallbacks": ["execute_code"],
    },
    "feature_importance": {
        "keywords": ["feature importance", "key drivers", "what matters", "variable significance"],
        "server": "ml_server",
        "fallbacks": ["execute_code"],
    },
    
    # ===========================================
    # BROWSER AGENT TOOLS
    # ===========================================
    "human_like_search": {
        "keywords": ["human search", "browse like human", "natural search"],
        "server": "browser_agent_server",
        "fallbacks": ["web_search"],
    },
    "search_memory_add": {
        "keywords": ["add to memory", "remember search", "cache result"],
        "server": "browser_agent_server",
        "fallbacks": [],
    },
    
    # ===========================================
    # SPECIALIZED TOOLS
    # ===========================================
}


def route_to_tool(task_description: str) -> tuple[str, list[str]]:
    """
    Route a micro-task to the appropriate tool based on keywords.
    
    Returns:
        (primary_tool, fallback_tools)
    """
    task_lower = task_description.lower()
    
    # 1. INTELLIGENCE: Check for direct tool reference from Registry
    try:
        from services.mcp_host.core.session_registry import get_session_registry
        registry = get_session_registry()
        # Look for exact tool names in the task description (e.g. "Use get_idx_tickers...")
        # Sort by length descending to match longest tool name first
        known_tools = sorted(list(registry.tool_to_server.keys()), key=len, reverse=True)
        
        for tool_name in known_tools:
            if tool_name in task_lower or tool_name.replace("_", " ") in task_lower:
                # Found exact tool match!
                return tool_name, []
    except Exception:
        pass

    # 2. TEXTBOOK: Fallback to keyword matching
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

CORE PHILOSOPHY: IMPROVISE AND BUILD.
Do not be limited by "standard" procedures. If a specific dataset/tool is missing, plan to **build it yourself** using the available primitive tools (like Python code and Web Search).
- Treat the web as a raw database to be scraped and parsed.
- Treat Python as your universal adapter to process that raw data.

RULES FOR FINANCIAL DATA:
1. Do NOT use `web_search` to find data tables if better tools exist. Use `get_idx_tickers` for identifying companies.
2. Use `execute_code` (Python) to fetch financial data (e.g. using yfinance) or to perform calculations.
3. You cannot 'Filter' data you do not have. Your first step must always be 'Acquire Dataset'.

Output format:
SUB-QUERIES:
1. [question - be specific about what data/information is needed]
2. [question]

HYPOTHESES:
1. [testable claim]
2. [testable claim]

EXECUTION-STEPS:
1. [action verb] [what] [where/how] - e.g. "Use get_idx_tickers to load JKSE company list"
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
    
    PARALLEL EXECUTION STRATEGY:
    - Tasks in the same "phase" (e.g., data_collection) have NO dependencies
      on each other, allowing batch parallel execution.
    - Dependencies are only created BETWEEN phases (e.g., analysis depends on
      all data_collection tasks being complete).
    """
    import uuid
    
    micro_tasks = []
    phase_order = ["data_collection", "extraction", "analysis", "synthesis"]
    tasks_by_phase: dict[str, list[str]] = {p: [] for p in phase_order}
    tasks_by_phase["research"] = []  # Fallback phase
    
    # First pass: categorize steps by phase
    step_phases = []
    for step in execution_steps:
        primary_tool, _ = route_to_tool(step)
        
        if primary_tool in ["web_search", "news_search", "fetch_data", "human_search", "web_crawler", "multi_browse"]:
            phase = "data_collection"
        elif primary_tool in ["scrape_url", "parse_document", "link_extractor", "sitemap_parser"]:
            phase = "extraction"
        elif primary_tool in ["run_python", "dataframe_ops", "sql_query"]:
            phase = "analysis"
        elif primary_tool in ["build_graph", "source_validator"]:
            phase = "synthesis"
        else:
            phase = "research"
        
        step_phases.append(phase)
    
    # Second pass: create tasks with phase-based dependencies
    for i, step in enumerate(execution_steps):
        task_id = f"task_{i+1}"
        phase = step_phases[i]
        
        primary_tool, fallbacks = route_to_tool(step)
        
        # PARALLEL STRATEGY: Tasks in the SAME phase have NO dependencies on each other.
        # Dependencies are only on the PREVIOUS phase being complete.
        depends_on = []
        
        # Find the previous phase that has tasks
        current_phase_index = phase_order.index(phase) if phase in phase_order else -1
        if current_phase_index > 0:
            # Depend on ALL tasks from the previous phase
            for prev_phase in phase_order[:current_phase_index]:
                depends_on.extend(tasks_by_phase.get(prev_phase, []))
        
        # Track this task in its phase
        tasks_by_phase[phase].append(task_id)
        
        micro_task = MicroTask(
            task_id=task_id,
            description=step,
            tool=primary_tool,
            inputs={"query": step},
            depends_on=depends_on,
            fallback_tools=fallbacks,
            persist=True,
            phase=phase,  # Add phase for debugging/logging
        )
        micro_tasks.append(micro_task)
    
    return ExecutionPlan(
        plan_id=f"plan_{uuid.uuid4().hex[:8]}",
        query=query,
        micro_tasks=micro_tasks,
        phases=[p for p in phase_order if tasks_by_phase.get(p)],
        estimated_tools=len(micro_tasks),
    )

