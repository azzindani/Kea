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
    """Decompose query into sub-queries and hypotheses using real LLM."""
    logger.info("\n" + "="*70)
    logger.info("📍 STEP 2: PLANNER NODE (LLM Call)")
    logger.info("="*70)
    logger.info(f"Query: {state.get('query', '')[:200]}...")
    logger.info("-"*70)
    logger.info("Calling LLM to decompose query into sub-queries...")
    
    # Call real planner that uses OpenRouter LLM
    updated_state = await real_planner_node(dict(state))
    
    sub_queries = updated_state.get("sub_queries", [])
    hypotheses = updated_state.get("hypotheses", [])
    
    logger.info(f"\n✅ Sub-Queries Generated ({len(sub_queries)}):")
    for i, sq in enumerate(sub_queries, 1):
        logger.info(f"   {i}. {sq}")
    
    logger.info(f"\n✅ Hypotheses Generated ({len(hypotheses)}):")
    for i, h in enumerate(hypotheses, 1):
        logger.info(f"   {i}. {h}")
    
    logger.info("="*70 + "\n")
    
    # Increment iteration
    updated_state["iteration"] = state.get("iteration", 0) + 1
    
    return {**state, **updated_state}


async def researcher_node(state: GraphState) -> GraphState:
    """Execute research using direct tool calls (bypassing MCP server layer)."""
    iteration = state.get("iteration", 1)
    
    logger.info("\n" + "="*70)
    logger.info(f"📍 STEP 3: RESEARCHER NODE (Iteration {iteration}) - Web Search")
    logger.info("="*70)
    
    sub_queries = state.get("sub_queries", [])
    query = state.get("query", "")
    facts = state.get("facts", [])
    sources = state.get("sources", [])
    
    # If no sub_queries, use the main query
    if not sub_queries:
        sub_queries = [query]
    
    logger.info(f"Sub-queries to research: {len(sub_queries)}")
    
    # Import the tool directly (bypasses MCP server layer)
    try:
        from mcp_servers.search_server.tools.web_search import web_search_tool
        
        # Execute search for each sub-query
        for i, sub_query in enumerate(sub_queries[:5], 1):  # Up to 5 searches
            logger.info(f"\n🔍 Tool Call {i}: web_search (DIRECT)")
            logger.info(f"   Query: {sub_query[:80]}...")
            
            try:
                result = await web_search_tool({
                    "query": sub_query, 
                    "max_results": 5
                })
                
                # Parse search results into facts
                if result and hasattr(result, "content"):
                    for content in result.content:
                        if hasattr(content, "text"):
                            # Check if it's an error
                            if result.isError:
                                logger.info(f"   ⚠️ Search returned error: {content.text[:100]}")
                            else:
                                fact = {
                                    "text": content.text[:1000],
                                    "query": sub_query,
                                    "source": "web_search",
                                }
                                facts.append(fact)
                                logger.info(f"   ✅ Search results extracted ({len(content.text)} chars)")
                                logger.info(f"   Preview: {content.text[:200]}...")
                                
                                # Extract sources from results
                                if "http" in content.text:
                                    # Simple URL extraction
                                    import re
                                    urls = re.findall(r'\((https?://[^\)]+)\)', content.text)
                                    for url in urls[:3]:
                                        sources.append({"url": url, "title": sub_query})
                else:
                    logger.info(f"   ⚠️ No content returned from search")
                            
            except Exception as e:
                logger.info(f"   ❌ Tool error: {e}")
                logger.warning(f"Research tool error: {e}")
                
    except ImportError as e:
        logger.error(f"Could not import web_search_tool: {e}")
        # Fallback: use LLM knowledge only
        facts.append({
            "text": f"Research context for: {query}. Using LLM knowledge as external search unavailable.",
            "query": query,
            "source": "llm_fallback",
        })
    except Exception as e:
        logger.info(f"❌ Search error: {e}")
        logger.error(f"Research error: {e}")
        facts.append({
            "text": f"Research in progress for: {sub_queries[0] if sub_queries else query}",
            "source": "fallback",
        })
    
    logger.info(f"\n✅ Total Facts Collected: {len(facts)}")
    logger.info(f"✅ Total Sources Found: {len(sources)}")
    logger.info("="*70 + "\n")
    
    return {
        **state,
        "facts": facts,
        "sources": sources,
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
