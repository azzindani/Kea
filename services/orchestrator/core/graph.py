"""
LangGraph Research State Machine.

Implements the cyclic research flow with checkpointing.
This is the PRODUCTION version that uses real LLM and MCP implementations.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Literal, TypedDict

from langgraph.graph import StateGraph, END
from pydantic import BaseModel, Field

from shared.schemas import ResearchState, ResearchStatus, QueryPath
from shared.logging import get_logger

# Import real implementations
from services.orchestrator.nodes.planner import planner_node as real_planner_node
from services.orchestrator.nodes.keeper import keeper_node as real_keeper_node
from services.orchestrator.agents.generator import GeneratorAgent
from services.orchestrator.agents.critic import CriticAgent
from services.orchestrator.agents.judge import JudgeAgent
from services.orchestrator.core.router import IntentionRouter


logger = get_logger(__name__)


# ============================================================================
# Node Names
# ============================================================================

class NodeName(str, Enum):
    """LangGraph node names."""
    ROUTER = "router"
    PLANNER = "planner"
    RESEARCHER = "researcher"
    KEEPER = "keeper"
    GENERATOR = "generator"
    CRITIC = "critic"
    JUDGE = "judge"
    SYNTHESIZER = "synthesizer"


# ============================================================================
# Graph State (TypedDict for LangGraph)
# ============================================================================

class GraphState(TypedDict, total=False):
    """State passed between LangGraph nodes."""
    # Core
    job_id: str
    query: str
    path: str
    status: str
    
    # Planning
    sub_queries: list[str]
    hypotheses: list[str]
    execution_plan: dict  # Execution plan from planner
    
    # Execution
    facts: list[dict]
    sources: list[dict]
    artifacts: list[str]
    tool_invocations: list[dict]  # Record of tool calls
    
    # Consensus
    generator_output: str
    critic_feedback: str
    judge_verdict: str
    
    # Output
    report: str
    confidence: float
    
    # Control
    iteration: int
    max_iterations: int
    should_continue: bool
    error: str | None


# ============================================================================
# Node Implementations (VERBOSE MODE)
# ============================================================================

async def router_node(state: GraphState) -> GraphState:
    """Route query to appropriate execution path."""
    query = state.get("query", "")
    
    logger.info("\n" + "="*70)
    logger.info("📍 STEP 1: ROUTER NODE")
    logger.info("="*70)
    logger.info(f"Query: {query[:200]}...")
    
    router = IntentionRouter()
    context = {
        "prior_research": state.get("prior_research"),
        "data_to_verify": state.get("data_to_verify"),
    }
    
    path = await router.route(query, context)
    
    logger.info(f"✅ Selected Path: {path}")
    logger.info(f"   A = Memory Fork | B = Shadow Lab | C = Grand Synthesis | D = Deep Research")
    logger.info("="*70 + "\n")
    
    logger.info(f"Router: Selected path {path}")
    
    return {
        **state,
        "path": path,
        "status": "running",
    }


async def planner_node(state: GraphState) -> GraphState:
    """Decompose query into sub-queries, hypotheses, and execution plan using real LLM."""
    logger.info("\n" + "="*70)
    logger.info("📍 STEP 2: PLANNER NODE (LLM Call)")
    logger.info("="*70)
    logger.info(f"Query: {state.get('query', '')[:200]}...")
    logger.info("-"*70)
    logger.info("Calling LLM to decompose query into sub-queries and execution plan...")
    
    # Call real planner that uses OpenRouter LLM
    updated_state = await real_planner_node(dict(state))
    
    sub_queries = updated_state.get("sub_queries", [])
    hypotheses = updated_state.get("hypotheses", [])
    execution_plan = updated_state.get("execution_plan", {})
    
    logger.info(f"\n✅ Sub-Queries Generated ({len(sub_queries)}):")
    for i, sq in enumerate(sub_queries, 1):
        logger.info(f"   {i}. {sq}")
    
    logger.info(f"\n✅ Hypotheses Generated ({len(hypotheses)}):")
    for i, h in enumerate(hypotheses, 1):
        logger.info(f"   {i}. {h}")
    
    # Log execution plan
    micro_tasks = execution_plan.get("micro_tasks", [])
    if micro_tasks:
        logger.info(f"\n✅ Execution Plan Generated ({len(micro_tasks)} micro-tasks):")
        for task in micro_tasks:
            logger.info(f"   [{task.get('task_id')}] {task.get('tool')}: {task.get('description', '')[:60]}...")
        logger.info(f"   Phases: {execution_plan.get('phases', [])}")
    
    logger.info("="*70 + "\n")
    
    # Increment iteration
    updated_state["iteration"] = state.get("iteration", 0) + 1
    
    return {**state, **updated_state}

async def researcher_node(state: GraphState) -> GraphState:
    """Execute research using execution plan with dynamic tool routing."""
    iteration = state.get("iteration", 1)
    
    logger.info("\n" + "="*70)
    logger.info(f"📍 STEP 3: RESEARCHER NODE (Iteration {iteration}) - Dynamic Tool Routing")
    logger.info("="*70)
    
    execution_plan = state.get("execution_plan", {})
    micro_tasks = execution_plan.get("micro_tasks", [])
    sub_queries = state.get("sub_queries", [])
    query = state.get("query", "")
    facts = state.get("facts", [])
    sources = state.get("sources", [])
    tool_invocations = state.get("tool_invocations", [])
    
    # If no execution plan, fall back to sub-queries with web_search
    if not micro_tasks:
        logger.info("No execution plan, falling back to sub-query based web search")
        micro_tasks = [
            {"task_id": f"task_{i+1}", "description": sq, "tool": "web_search", 
             "inputs": {"query": sq}, "fallback_tools": ["news_search"], "persist": True}
            for i, sq in enumerate(sub_queries or [query])
        ]
    
    logger.info(f"Executing {len(micro_tasks)} micro-tasks from execution plan")
    
    # Tool registry for dynamic routing - Wire ALL existing MCP tools
    from services.orchestrator.mcp.client import get_mcp_orchestrator
    
    # Search tools
    from mcp_servers.search_server.tools.web_search import web_search_tool
    
    # Scraper tools
    from mcp_servers.scraper_server.tools.fetch_url import fetch_url_tool
    
    # Python execution tools
    from mcp_servers.python_server.tools.execute_code import execute_code_tool
    from mcp_servers.python_server.tools.dataframe_ops import dataframe_ops_tool
    from mcp_servers.python_server.tools.sql_query import sql_query_tool
    
    # Crawler tools
    from mcp_servers.crawler_server.server import web_crawler_tool, sitemap_parser_tool, link_extractor_tool
    
    # Browser agent tools
    from mcp_servers.browser_agent_server.server import human_like_search_tool, source_validator_tool
    
    # Direct tool implementations - ALL available tools wired here
    direct_tools = {
        # ===========================================
        # SEARCH TOOLS (parallel capable)
        # ===========================================
        "web_search": web_search_tool,
        "news_search": web_search_tool,
        "human_search": human_like_search_tool,  # Human-like with delays
        
        # ===========================================
        # SCRAPING TOOLS (recursive capable)
        # ===========================================
        "scrape_url": fetch_url_tool,
        "fetch_url": fetch_url_tool,
        "fetch_data": lambda args: web_search_tool({"query": args.get("query", ""), "max_results": 10}),
        
        # ===========================================
        # CRAWLER TOOLS (depth unlimited)
        # ===========================================
        "web_crawler": web_crawler_tool,      # Recursive crawl - depth/pages configurable
        "sitemap_parser": sitemap_parser_tool,  # Parse sitemap for URLs
        "link_extractor": link_extractor_tool,  # Extract all links from page
        
        # ===========================================
        # BROWSER TOOLS (parallel browse)
        # ===========================================
        "multi_browse": lambda args: BrowserAgentServer()._handle_multi_browse(args),  # Browse 10+ URLs parallel
        "source_validator": source_validator_tool,  # Check credibility
        
        # ===========================================
        # DATA TOOLS (DataFrame/SQL)
        # ===========================================
        "dataframe_ops": dataframe_ops_tool,  # Load, filter, aggregate DataFrames
        "sql_query": sql_query_tool,          # DuckDB SQL queries
        "run_python": execute_code_tool,
        "execute_code": execute_code_tool,
        "analyze_data": dataframe_ops_tool,   # Alias for clarity
    }
    
    # Import for multi_browse
    from mcp_servers.browser_agent_server.server import BrowserAgentServer
    
    def build_tool_inputs(tool_name: str, description: str, original_inputs: dict) -> dict:
        """Build proper inputs based on tool requirements."""
        
        # =====================================================
        # PYTHON TOOLS
        # =====================================================
        if tool_name in ["run_python", "execute_code"]:
            if "code" in original_inputs:
                return original_inputs
            return {"code": f"# Task: {description}\nprint('Analysis would be performed here')"}
        
        if tool_name in ["dataframe_ops", "analyze_data"]:
            if "operation" in original_inputs:
                return original_inputs
            # Default to describe operation with web search to find data
            return None  # Use fallback
        
        if tool_name == "sql_query":
            if "query" in original_inputs:
                return original_inputs
            return None  # Use fallback
        
        # =====================================================
        # SCRAPING TOOLS
        # =====================================================
        if tool_name in ["scrape_url", "fetch_url"]:
            if "url" in original_inputs:
                return original_inputs
            return None  # Signal to use fallback
        
        # =====================================================
        # CRAWLER TOOLS (support unlimited depth)
        # =====================================================
        if tool_name == "web_crawler":
            if "start_url" in original_inputs:
                # Allow LLM to specify depth - no hard limit
                return {
                    "start_url": original_inputs["start_url"],
                    "max_depth": original_inputs.get("max_depth", 5),  # Default 5, can go higher
                    "max_pages": original_inputs.get("max_pages", 100),  # 100 pages per crawl
                    "same_domain": original_inputs.get("same_domain", True),
                }
            return None  # Need URL
        
        if tool_name in ["sitemap_parser", "link_extractor"]:
            if "url" in original_inputs:
                return original_inputs
            return None  # Need URL
        
        # =====================================================
        # BROWSER TOOLS (parallel capable)
        # =====================================================
        if tool_name in ["human_search"]:
            if "query" in original_inputs:
                return {
                    "query": original_inputs["query"],
                    "max_sites": original_inputs.get("max_sites", 10),  # 10 parallel
                }
            return {"query": description, "max_sites": 10}
        
        if tool_name == "multi_browse":
            if "urls" in original_inputs:
                return {
                    "urls": original_inputs["urls"],
                    "max_concurrent": original_inputs.get("max_concurrent", 10),  # 10 parallel
                    "extract": original_inputs.get("extract", "text"),
                }
            return None  # Need URLs
        
        if tool_name == "source_validator":
            if "url" in original_inputs:
                return original_inputs
            return None
        
        # =====================================================
        # SEARCH TOOLS (default)
        # =====================================================
        if tool_name in ["web_search", "news_search", "fetch_data"]:
            if "query" in original_inputs:
                return original_inputs
            return {"query": description, "max_results": 20}  # Increased from 10
        
        # Default: pass as-is
        return original_inputs
    
    client = get_mcp_orchestrator()
    use_direct = len(client.tool_names) == 0  # No MCP tools registered
    
    # Execute each micro-task (increased limit for comprehensive research)
    for i, task in enumerate(micro_tasks[:100], 1):  # Allow up to 100 tasks
        task_id = task.get("task_id", f"task_{i}")
        tool_name = task.get("tool", "web_search")
        description = task.get("description", "")
        fallbacks = task.get("fallback_tools", []) or ["web_search"]  # Default fallback
        persist = task.get("persist", True)
        original_inputs = task.get("inputs", {})
        
        logger.info(f"\n🔧 Micro-Task {task_id}: {tool_name}")
        logger.info(f"   Description: {description[:80]}...")
        logger.info(f"   Persist: {persist} | Fallbacks: {fallbacks}")
        
        result = None
        used_tool = tool_name
        error = None
        success = False
        
        # Build proper inputs for this tool
        tool_inputs = build_tool_inputs(tool_name, description, original_inputs)
        
        # If inputs are None, tool can't run (e.g., scrape_url without URL)
        if tool_inputs is None:
            logger.info(f"   ⚠️ Cannot build inputs for {tool_name}, using fallback")
            tool_name = fallbacks[0] if fallbacks else "web_search"
            tool_inputs = {"query": description, "max_results": 10}
            used_tool = tool_name
        
        try:
            # Try primary tool
            if use_direct and tool_name in direct_tools:
                logger.info(f"   🔌 Direct call: {tool_name}")
                result = await direct_tools[tool_name](tool_inputs)
            elif not use_direct:
                logger.info(f"   📡 MCP call: {tool_name}")
                result = await client.call_tool(tool_name, tool_inputs)
            else:
                logger.info(f"   ⚠️ Tool {tool_name} not available, trying fallbacks")
                raise ValueError(f"Tool {tool_name} not available")
            
            # Check for error response - trigger fallback
            if result and hasattr(result, "isError") and result.isError:
                error_text = ""
                for c in result.content:
                    if hasattr(c, "text"):
                        error_text = c.text
                        break
                logger.info(f"   ⚠️ Tool returned error: {error_text[:100]}")
                raise ValueError(f"Tool error: {error_text[:100]}")
                
        except Exception as e:
            error = str(e)
            logger.info(f"   ❌ Primary tool failed: {e}")
            
            # Try fallbacks
            for fallback in fallbacks:
                try:
                    logger.info(f"   🔄 Fallback: {fallback}")
                    fallback_inputs = build_tool_inputs(fallback, description, original_inputs)
                    if fallback_inputs is None:
                        fallback_inputs = {"query": description, "max_results": 10}
                    
                    if fallback in direct_tools:
                        result = await direct_tools[fallback](fallback_inputs)
                        # Check for fallback error too
                        if result and hasattr(result, "isError") and result.isError:
                            continue  # Try next fallback
                        used_tool = fallback
                        error = None
                        success = True
                        break
                except Exception as fe:
                    logger.info(f"   ❌ Fallback {fallback} failed: {fe}")
        
        # Process result
        if result and hasattr(result, "content"):
            for content in result.content:
                if hasattr(content, "text"):
                    if hasattr(result, "isError") and result.isError:
                        logger.info(f"   ⚠️ Tool returned error: {content.text[:100]}")
                    else:
                        fact = {
                            "text": content.text[:1000],
                            "query": description[:200],
                            "source": used_tool,
                            "task_id": task_id,
                            "persist": persist,
                        }
                        facts.append(fact)
                        success = True  # Mark as successful when we got valid content
                        logger.info(f"   ✅ Result extracted ({len(content.text)} chars)")
                        
                        # Extract URLs as sources
                        if "http" in content.text:
                            import re
                            urls = re.findall(r'\((https?://[^\)]+)\)', content.text)
                            for url in urls[:3]:
                                sources.append({"url": url, "title": description[:100], "tool": used_tool})
        
        # Record tool invocation with proper success tracking
        tool_invocations.append({
            "task_id": task_id,
            "tool": used_tool,
            "success": success or (error is None and result is not None),
            "error": error,
            "persist": persist,
        })
    
    # Count successes for logging
    successes = sum(1 for inv in tool_invocations if inv.get("success", False))
    logger.info(f"\n📊 Research Summary:")
    logger.info(f"   Tasks executed: {len(tool_invocations)}")
    logger.info(f"   Tasks succeeded: {successes}")
    logger.info(f"   Facts collected: {len(facts)}")
    logger.info(f"   Sources found: {len(sources)}")
    logger.info("="*70 + "\n")
    
    logger.info(f"\n✅ Total Facts Collected: {len(facts)}")
    logger.info(f"✅ Total Sources Found: {len(sources)}")
    logger.info("="*70 + "\n")
    
    return {
        **state,
        "facts": facts,
        "sources": sources,
        "tool_invocations": tool_invocations,
    }


async def keeper_node(state: GraphState) -> GraphState:
    """Check for context drift and verify progress."""
    iteration = state.get("iteration", 0)
    max_iterations = state.get("max_iterations", 3)
    facts = state.get("facts", [])
    
    logger.info("\n" + "="*70)
    logger.info(f"📍 STEP 4: KEEPER NODE (Context Guard)")
    logger.info("="*70)
    logger.info(f"Iteration: {iteration}/{max_iterations}")
    logger.info(f"Facts collected: {len(facts)}")
    
    # Call real keeper that checks context drift
    updated_state = await real_keeper_node(dict(state))
    
    should_continue = updated_state.get("should_continue", False)
    drift_detected = updated_state.get("drift_detected", False)
    
    if drift_detected:
        logger.info("⚠️ Context drift detected!")
    
    if should_continue:
        logger.info("🔄 Decision: CONTINUE research loop")
    else:
        logger.info("✅ Decision: STOP research, proceed to synthesis")
    
    logger.info("="*70 + "\n")
    
    return {**state, **updated_state}


async def generator_node(state: GraphState) -> GraphState:
    """Generate initial answer from facts using real LLM (Optimist role)."""
    logger.info("\n" + "="*70)
    logger.info("📍 STEP 5: GENERATOR NODE (LLM Call - The Optimist)")
    logger.info("="*70)
    
    facts = state.get("facts", [])
    sources = state.get("sources", [])
    query = state.get("query", "")
    
    logger.info(f"Query: {query[:100]}...")
    logger.info(f"Facts available: {len(facts)}")
    logger.info("-"*70)
    logger.info("Calling LLM to generate comprehensive answer...")
    
    generator = GeneratorAgent()
    output = await generator.generate(query, facts, sources)
    
    logger.info(f"\n✅ Generator Output ({len(output)} chars):")
    logger.info("-"*70)
    # Print full output
    logger.info(output)
    logger.info("-"*70)
    logger.info("="*70 + "\n")
    
    return {
        **state,
        "generator_output": output,
    }


async def critic_node(state: GraphState) -> GraphState:
    """Critique the generator's output using real LLM (Pessimist role)."""
    logger.info("\n" + "="*70)
    logger.info("📍 STEP 6: CRITIC NODE (LLM Call - The Pessimist)")
    logger.info("="*70)
    
    generator_output = state.get("generator_output", "")
    facts = state.get("facts", [])
    sources = state.get("sources", [])
    
    logger.info(f"Reviewing answer ({len(generator_output)} chars)")
    logger.info("-"*70)
    logger.info("Calling LLM to critique and find weaknesses...")
    
    critic = CriticAgent()
    feedback = await critic.critique(generator_output, facts, sources)
    
    logger.info(f"\n✅ Critic Feedback ({len(feedback)} chars):")
    logger.info("-"*70)
    # Print full feedback
    logger.info(feedback)
    logger.info("-"*70)
    logger.info("="*70 + "\n")
    
    return {
        **state,
        "critic_feedback": feedback,
    }


async def judge_node(state: GraphState) -> GraphState:
    """Synthesize generator/critic into final verdict using real LLM."""
    logger.info("\n" + "="*70)
    logger.info("📍 STEP 7: JUDGE NODE (LLM Call - The Arbiter)")
    logger.info("="*70)
    
    query = state.get("query", "")
    generator_output = state.get("generator_output", "")
    critic_feedback = state.get("critic_feedback", "")
    
    logger.info(f"Evaluating: Generator ({len(generator_output)} chars) vs Critic ({len(critic_feedback)} chars)")
    logger.info("-"*70)
    logger.info("Calling LLM to make final judgment...")
    
    judge = JudgeAgent()
    result = await judge.judge(query, generator_output, critic_feedback)
    
    verdict = result.get("verdict", "Accept")
    confidence = result.get("confidence", 0.5)
    reasoning = result.get("reasoning", "")
    
    logger.info(f"\n✅ Judge Verdict: {verdict}")
    logger.info(f"✅ Confidence: {confidence:.0%}")
    logger.info(f"\n📝 Reasoning:")
    logger.info("-"*70)
    logger.info(reasoning[:500] if len(reasoning) > 500 else reasoning)
    logger.info("-"*70)
    logger.info("="*70 + "\n")
    
    return {
        **state,
        "judge_verdict": verdict,
        "confidence": confidence,
    }


async def synthesizer_node(state: GraphState) -> GraphState:
    """Create final report from all inputs."""
    logger.info("\n" + "="*70)
    logger.info("📍 STEP 8: SYNTHESIZER NODE (Final Report)")
    logger.info("="*70)
    
    query = state.get("query", "")
    facts = state.get("facts", [])
    sources = state.get("sources", [])
    generator_output = state.get("generator_output", "")
    confidence = state.get("confidence", 0.0)
    verdict = state.get("judge_verdict", "Unknown")
    
    logger.info(f"Query: {query[:100]}...")
    logger.info(f"Facts collected: {len(facts)}")
    logger.info(f"Sources: {len(sources)}")
    logger.info(f"Judge Verdict: {verdict}")
    logger.info(f"Confidence: {confidence:.0%}")
    logger.info("-"*70)
    logger.info("Generating final report...")
    
    report = f"# Research Report: {query}\n\n"
    report += f"**Confidence:** {confidence:.0%}\n"
    report += f"**Sources:** {len(sources)}\n"
    report += f"**Facts Extracted:** {len(facts)}\n"
    report += f"**Judge Verdict:** {verdict}\n\n"
    report += "---\n\n"
    report += generator_output
    report += "\n\n---\n\n"
    report += "## Facts Collected\n\n"
    
    for i, fact in enumerate(facts[:10], 1):
        if isinstance(fact, dict):
            report += f"{i}. {fact.get('text', str(fact))[:150]}...\n"
        else:
            report += f"{i}. {str(fact)[:150]}...\n"
    
    report += "\n## Sources\n\n"
    
    for src in sources[:10]:
        report += f"- [{src.get('title', 'Unknown')}]({src.get('url', '')})\n"
    
    logger.info(f"\n✅ Final Report Generated ({len(report)} chars)")
    logger.info("="*70)
    logger.info("\n" + "🏁"*35)
    logger.info("                    RESEARCH COMPLETE")
    logger.info("🏁"*35 + "\n")
    
    return {
        **state,
        "report": report,
        "status": "completed",
    }


# ============================================================================
# Routing Functions
# ============================================================================

def should_continue_research(state: GraphState) -> Literal["researcher", "generator"]:
    """Decide whether to continue research or move to synthesis."""
    if state.get("should_continue", False):
        return "researcher"
    return "generator"


# ============================================================================
# Build Graph
# ============================================================================

def build_research_graph() -> StateGraph:
    """
    Build the LangGraph research state machine.
    
    Flow:
    router -> planner -> researcher -> keeper
                              ^            |
                              |            v
                              +-- (loop) --+
                                           |
                                           v
                              generator -> critic -> judge -> synthesizer -> END
    """
    graph = StateGraph(GraphState)
    
    # Add nodes
    graph.add_node(NodeName.ROUTER.value, router_node)
    graph.add_node(NodeName.PLANNER.value, planner_node)
    graph.add_node(NodeName.RESEARCHER.value, researcher_node)
    graph.add_node(NodeName.KEEPER.value, keeper_node)
    graph.add_node(NodeName.GENERATOR.value, generator_node)
    graph.add_node(NodeName.CRITIC.value, critic_node)
    graph.add_node(NodeName.JUDGE.value, judge_node)
    graph.add_node(NodeName.SYNTHESIZER.value, synthesizer_node)
    
    # Add edges
    graph.set_entry_point(NodeName.ROUTER.value)
    graph.add_edge(NodeName.ROUTER.value, NodeName.PLANNER.value)
    graph.add_edge(NodeName.PLANNER.value, NodeName.RESEARCHER.value)
    graph.add_edge(NodeName.RESEARCHER.value, NodeName.KEEPER.value)
    
    # Conditional edge: continue research or synthesize
    graph.add_conditional_edges(
        NodeName.KEEPER.value,
        should_continue_research,
        {
            "researcher": NodeName.RESEARCHER.value,
            "generator": NodeName.GENERATOR.value,
        }
    )
    
    # Consensus flow
    graph.add_edge(NodeName.GENERATOR.value, NodeName.CRITIC.value)
    graph.add_edge(NodeName.CRITIC.value, NodeName.JUDGE.value)
    graph.add_edge(NodeName.JUDGE.value, NodeName.SYNTHESIZER.value)
    graph.add_edge(NodeName.SYNTHESIZER.value, END)
    
    return graph


def compile_research_graph():
    """Compile the research graph for execution."""
    graph = build_research_graph()
    return graph.compile()
