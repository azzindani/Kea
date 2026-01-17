"""
LangGraph Research State Machine.

Implements the cyclic research flow with checkpointing.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Literal, TypedDict

from langgraph.graph import StateGraph, END
from pydantic import BaseModel, Field

from shared.schemas import ResearchState, ResearchStatus, QueryPath
from shared.logging import get_logger


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
    Route query to appropriate execution path.
    
    Paths:
    A - Memory Fork (incremental research)
    B - Shadow Lab (recalculation)
    C - Grand Synthesis (meta-analysis)
    D - Deep Research (full investigation)
    """
    logger.info("Router: Analyzing query", extra={"query": state.get("query", "")[:100]})
    
    query = state.get("query", "").lower()
    
    # Simple routing logic (in production, use LLM classification)
    if "recalculate" in query or "what if" in query:
        path = "B"  # SHADOW_LAB
    elif "compare" in query and "across" in query:
        path = "C"  # GRAND_SYNTHESIS
    elif "update" in query or "latest" in query:
        path = "A"  # MEMORY_FORK
    else:
        path = "D"  # DEEP_RESEARCH
    
    logger.info(f"Router: Selected path {path}")
    
    return {
        **state,
        "path": path,
        "status": "running",
    }


async def planner_node(state: GraphState) -> GraphState:
    """
    Decompose query into sub-queries and hypotheses.
    """
    logger.info("Planner: Decomposing query")
    
    query = state.get("query", "")
    
    # Generate sub-queries (in production, use LLM)
    sub_queries = [
        f"Find recent data about: {query}",
        f"Identify key metrics for: {query}",
        f"Find expert sources on: {query}",
    ]
    
    hypotheses = [
        f"The data about {query} will show clear trends",
        f"Multiple reliable sources will confirm the findings",
    ]
    
    return {
        **state,
        "sub_queries": sub_queries,
        "hypotheses": hypotheses,
        "iteration": state.get("iteration", 0) + 1,
    }


async def researcher_node(state: GraphState) -> GraphState:
    """
    Execute research using MCP tools.
    
    This node would use the MCP orchestrator to:
    1. Search the web
    2. Fetch and scrape URLs
    3. Extract data with Python
    4. Analyze with vision tools
    """
    logger.info("Researcher: Executing research")
    
    sub_queries = state.get("sub_queries", [])
    
    # Placeholder: In production, this calls MCP tools
    facts = [
        {
            "entity": "example",
            "attribute": "value",
            "value": "100",
            "source": "https://example.com",
        }
    ]
    
    sources = [
        {
            "url": "https://example.com",
            "title": "Example Source",
            "domain": "example.com",
        }
    ]
    
    return {
        **state,
        "facts": state.get("facts", []) + facts,
        "sources": state.get("sources", []) + sources,
    }


async def keeper_node(state: GraphState) -> GraphState:
    """
    Check for context drift and verify progress.
    
    Decides if research should continue or pivot.
    """
    logger.info("Keeper: Checking context drift")
    
    iteration = state.get("iteration", 0)
    max_iterations = state.get("max_iterations", 3)
    facts = state.get("facts", [])
    
    # Determine if we should continue
    should_continue = (
        iteration < max_iterations
        and len(facts) < 10  # Not enough facts yet
    )
    
    return {
        **state,
        "should_continue": should_continue,
    }


async def generator_node(state: GraphState) -> GraphState:
    """
    Generate initial answer from facts (Optimist role).
    """
    logger.info("Generator: Creating initial answer")
    
    facts = state.get("facts", [])
    query = state.get("query", "")
    
    # Placeholder: In production, use LLM
    output = f"## Research Findings for: {query}\n\n"
    output += f"Based on {len(facts)} facts gathered:\n\n"
    
    for fact in facts[:5]:
        output += f"- {fact.get('entity')}: {fact.get('value')}\n"
    
    output += "\n### Analysis\n"
    output += "The data suggests positive trends..."
    
    return {
        **state,
        "generator_output": output,
    }


async def critic_node(state: GraphState) -> GraphState:
    """
    Critique the generator's output (Pessimist role).
    """
    logger.info("Critic: Reviewing answer")
    
    generator_output = state.get("generator_output", "")
    
    # Placeholder: In production, use LLM with critic persona
    feedback = "## Critical Review\n\n"
    feedback += "- Source reliability: Could be improved\n"
    feedback += "- Data recency: Needs verification\n"
    feedback += "- Missing context: Some gaps identified\n"
    
    return {
        **state,
        "critic_feedback": feedback,
    }


async def judge_node(state: GraphState) -> GraphState:
    """
    Synthesize generator/critic into final verdict.
    """
    logger.info("Judge: Making final decision")
    
    generator_output = state.get("generator_output", "")
    critic_feedback = state.get("critic_feedback", "")
    
    # Placeholder: In production, use LLM with judge persona
    verdict = "APPROVED_WITH_CAVEATS"
    confidence = 0.75
    
    return {
        **state,
        "judge_verdict": verdict,
        "confidence": confidence,
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
