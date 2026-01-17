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
    
    # Execution
    facts: list[dict]
    sources: list[dict]
    artifacts: list[str]
    
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
# Node Implementations
# ============================================================================

async def router_node(state: GraphState) -> GraphState:
    """
    Route query to appropriate execution path using real LLM router.
    
    Paths:
    A - Memory Fork (incremental research)
    B - Shadow Lab (recalculation)
    C - Grand Synthesis (meta-analysis)
    D - Deep Research (full investigation)
    """
    logger.info("Router: Analyzing query", extra={"query": state.get("query", "")[:100]})
    
    router = IntentionRouter()
    context = {
        "prior_research": state.get("prior_research"),
        "data_to_verify": state.get("data_to_verify"),
    }
    
    path = await router.route(state.get("query", ""), context)
    
    logger.info(f"Router: Selected path {path}")
    
    return {
        **state,
        "path": path,
        "status": "running",
    }


async def planner_node(state: GraphState) -> GraphState:
    """
    Decompose query into sub-queries and hypotheses using real LLM.
    Delegates to services/orchestrator/nodes/planner.py
    """
    logger.info("Planner: Decomposing query (REAL LLM)")
    
    # Call real planner that uses OpenRouter LLM
    updated_state = await real_planner_node(dict(state))
    
    # Increment iteration
    updated_state["iteration"] = state.get("iteration", 0) + 1
    
    return {**state, **updated_state}


async def researcher_node(state: GraphState) -> GraphState:
    """
    Execute research using MCP tools.
    
    Uses the MCP orchestrator to:
    1. Search the web
    2. Fetch and scrape URLs
    3. Extract data with Python
    4. Analyze with vision tools
    """
    logger.info("Researcher: Executing research (MCP Tools)")
    
    sub_queries = state.get("sub_queries", [])
    facts = state.get("facts", [])
    sources = state.get("sources", [])
    
    # Import MCP client for tool calls
    try:
        from services.orchestrator.mcp.client import MCPOrchestrator
        
        orchestrator = MCPOrchestrator()
        
        # Execute search for each sub-query
        for sub_query in sub_queries[:3]:  # Limit to 3 to avoid rate limits
            try:
                result = await orchestrator.call_tool(
                    "web_search",
                    {"query": sub_query, "max_results": 5}
                )
                logger.info(f"Researcher: Tool call completed for {sub_query[:50]}")
                
                # Parse search results into facts
                if result and hasattr(result, "content"):
                    for content in result.content:
                        if hasattr(content, "text"):
                            facts.append({
                                "text": content.text[:500],
                                "query": sub_query,
                                "source": "web_search",
                            })
                            
            except Exception as e:
                logger.warning(f"Research tool error: {e}")
                
    except Exception as e:
        logger.error(f"MCP Orchestrator error: {e}")
        # Fallback: generate placeholder facts
        facts.append({
            "text": f"Research in progress for: {sub_queries[0] if sub_queries else 'query'}",
            "source": "fallback",
        })
    
    logger.info(f"Researcher: Collected {len(facts)} facts")
    
    return {
        **state,
        "facts": facts,
        "sources": sources,
    }


async def keeper_node(state: GraphState) -> GraphState:
    """
    Check for context drift and verify progress using real implementation.
    Delegates to services/orchestrator/nodes/keeper.py
    """
    logger.info("Keeper: Checking context drift (REAL)")
    
    # Call real keeper that checks context drift with embeddings
    updated_state = await real_keeper_node(dict(state))
    
    return {**state, **updated_state}


async def generator_node(state: GraphState) -> GraphState:
    """
    Generate initial answer from facts using real LLM (Optimist role).
    Delegates to services/orchestrator/agents/generator.py
    """
    logger.info("Generator: Creating initial answer (REAL LLM)")
    
    facts = state.get("facts", [])
    sources = state.get("sources", [])
    query = state.get("query", "")
    
    generator = GeneratorAgent()
    output = await generator.generate(query, facts, sources)
    
    logger.info(f"Generator: Answer generated ({len(output)} chars)")
    
    return {
        **state,
        "generator_output": output,
    }


async def critic_node(state: GraphState) -> GraphState:
    """
    Critique the generator's output using real LLM (Pessimist role).
    Delegates to services/orchestrator/agents/critic.py
    """
    logger.info("Critic: Reviewing answer (REAL LLM)")
    
    generator_output = state.get("generator_output", "")
    facts = state.get("facts", [])
    sources = state.get("sources", [])
    
    critic = CriticAgent()
    feedback = await critic.critique(generator_output, facts, sources)
    
    logger.info(f"Critic: Critique complete ({len(feedback)} chars)")
    
    return {
        **state,
        "critic_feedback": feedback,
    }


async def judge_node(state: GraphState) -> GraphState:
    """
    Synthesize generator/critic into final verdict using real LLM.
    Delegates to services/orchestrator/agents/judge.py
    """
    logger.info("Judge: Making final decision (REAL LLM)")
    
    query = state.get("query", "")
    generator_output = state.get("generator_output", "")
    critic_feedback = state.get("critic_feedback", "")
    
    judge = JudgeAgent()
    result = await judge.judge(query, generator_output, critic_feedback)
    
    logger.info(f"Judge: Verdict={result.get('verdict')}, Confidence={result.get('confidence')}")
    
    return {
        **state,
        "judge_verdict": result.get("verdict", "Accept"),
        "confidence": result.get("confidence", 0.5),
    }


async def synthesizer_node(state: GraphState) -> GraphState:
    """
    Create final report from all inputs.
    """
    logger.info("Synthesizer: Creating final report")
    
    query = state.get("query", "")
    facts = state.get("facts", [])
    sources = state.get("sources", [])
    generator_output = state.get("generator_output", "")
    confidence = state.get("confidence", 0.0)
    
    report = f"# Research Report: {query}\n\n"
    report += f"**Confidence:** {confidence:.0%}\n"
    report += f"**Sources:** {len(sources)}\n"
    report += f"**Facts Extracted:** {len(facts)}\n\n"
    report += "---\n\n"
    report += generator_output
    report += "\n\n---\n\n"
    report += "## Sources\n\n"
    
    for src in sources[:10]:
        report += f"- [{src.get('title', 'Unknown')}]({src.get('url', '')})\n"
    
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
