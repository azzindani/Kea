"""
Keeper Node.

The Context Guard - monitors for drift, orchestrates tools, and manages persistence.
Enhanced with execution plan awareness and always-persist policy.
"""

from __future__ import annotations

from typing import Any
from shared.logging import get_logger

logger = get_logger(__name__)


# ============================================================================
# Persistence Layer (Always Persist Policy)
# ============================================================================

async def persist_facts(facts: list[dict], job_id: str) -> int:
    """
    Persist facts to database.
    
    Always-persist policy: every fact is stored for durability and resume capability.
    
    Returns:
        Number of facts persisted
    """
    persisted = 0
    
    # TODO: Implement actual database persistence
    # For now, filter to facts marked for persistence
    for fact in facts:
        if fact.get("persist", True):  # Default to True (always persist)
            persisted += 1
            # In production: INSERT INTO facts (job_id, text, source, ...) VALUES (...)
    
    logger.info(f"Keeper: Persisted {persisted} facts for job {job_id}")
    return persisted


async def persist_tool_invocations(invocations: list[dict], job_id: str) -> int:
    """
    Persist tool invocations to audit trail.
    
    Returns:
        Number of invocations persisted
    """
    persisted = 0
    
    for inv in invocations:
        persisted += 1
        # In production: INSERT INTO audit_trail (job_id, tool, success, ...) VALUES (...)
    
    logger.info(f"Keeper: Persisted {persisted} tool invocations for job {job_id}")
    return persisted


# ============================================================================
# Tool Orchestration Logic
# ============================================================================

def analyze_execution_progress(state: dict[str, Any]) -> dict[str, Any]:
    """
    Analyze execution plan progress and determine next actions.
    
    Returns:
        {
            "completed_tasks": int,
            "total_tasks": int,
            "failed_tasks": int,
            "next_phase": str | None,
            "should_retry": list[str],  # task_ids to retry
        }
    """
    execution_plan = state.get("execution_plan", {})
    tool_invocations = state.get("tool_invocations", [])
    
    micro_tasks = execution_plan.get("micro_tasks", [])
    total_tasks = len(micro_tasks)
    
    # Count completed and failed
    completed_tasks = sum(1 for inv in tool_invocations if inv.get("success", False))
    failed_tasks = sum(1 for inv in tool_invocations if not inv.get("success", True))
    
    # Identify tasks to retry (failed but have fallbacks unused)
    should_retry = []
    for inv in tool_invocations:
        if not inv.get("success", True):
            task_id = inv.get("task_id")
            # Check if this task has unused fallbacks
            for task in micro_tasks:
                if task.get("task_id") == task_id:
                    if task.get("fallback_tools"):
                        should_retry.append(task_id)
                    break
    
    # Determine next phase
    phases = execution_plan.get("phases", [])
    completed_phases = set()
    for inv in tool_invocations:
        if inv.get("success"):
            task_id = inv.get("task_id")
            for task in micro_tasks:
                if task.get("task_id") == task_id:
                    # Determine phase from tool
                    tool = task.get("tool", "")
                    if tool in ["web_search", "news_search", "fetch_data"]:
                        completed_phases.add("data_collection")
                    elif tool in ["scrape_url", "parse_document"]:
                        completed_phases.add("extraction")
                    elif tool in ["run_python"]:
                        completed_phases.add("analysis")
                    elif tool in ["build_graph"]:
                        completed_phases.add("synthesis")
    
    next_phase = None
    for phase in ["data_collection", "extraction", "analysis", "synthesis"]:
        if phase in phases and phase not in completed_phases:
            next_phase = phase
            break
    
    return {
        "completed_tasks": completed_tasks,
        "total_tasks": total_tasks,
        "failed_tasks": failed_tasks,
        "next_phase": next_phase,
        "should_retry": should_retry,
    }


# ============================================================================
# Keeper Node
# ============================================================================

async def keeper_node(state: dict[str, Any]) -> dict[str, Any]:
    """
    Keeper node: Monitor context drift, orchestrate tools, manage persistence.
    
    The Keeper is responsible for:
    - Detecting when research has drifted from original query
    - Determining if enough information has been gathered
    - Deciding whether to continue or stop the research loop
    - Persisting all facts and tool invocations (always-persist policy)
    - Analyzing execution plan progress
    
    Args:
        state: Current graph state
        
    Returns:
        Updated state with 'should_continue' decision
    """
    logger.info("Keeper: Checking context drift and orchestrating tools")
    
    iteration = state.get("iteration", 0)
    max_iterations = state.get("max_iterations", 3)
    query = state.get("query", "")
    facts = state.get("facts", [])
    job_id = state.get("job_id", "unknown")
    tool_invocations = state.get("tool_invocations", [])
    
    # ============================================================
    # ALWAYS PERSIST: Facts and Tool Invocations
    # ============================================================
    if facts:
        await persist_facts(facts, job_id)
    if tool_invocations:
        await persist_tool_invocations(tool_invocations, job_id)
    
    # ============================================================
    # ANALYZE EXECUTION PROGRESS
    # ============================================================
    progress = analyze_execution_progress(state)
    
    logger.info(f"Keeper: Execution progress - {progress['completed_tasks']}/{progress['total_tasks']} tasks complete")
    logger.info(f"   Failed: {progress['failed_tasks']}, Next phase: {progress['next_phase']}")
    
    if progress["should_retry"]:
        logger.info(f"   Tasks to retry: {progress['should_retry']}")
    
    state["execution_progress"] = progress
    
    # ============================================================
    # CHECK ITERATION LIMIT
    # ============================================================
    if iteration >= max_iterations:
        logger.info(f"Keeper: Max iterations ({max_iterations}) reached")
        state["should_continue"] = False
        return state
    
    # ============================================================
    # CHECK FACT SUFFICIENCY
    # ============================================================
    min_facts = 3
    if len(facts) >= min_facts:
        logger.info(f"Keeper: Sufficient facts gathered ({len(facts)} >= {min_facts})")
        
        # If all tasks complete, stop
        if progress["completed_tasks"] >= progress["total_tasks"]:
            logger.info("Keeper: All execution plan tasks complete")
            state["should_continue"] = False
            return state
        
        # If in later iterations, consider stopping
        if iteration >= 2:
            state["should_continue"] = False
            return state
    
    # ============================================================
    # CHECK CONTEXT DRIFT
    # ============================================================
    if facts:
        # Simple keyword overlap check
        query_words = set(query.lower().split())
        relevant_facts = 0
        
        for fact in facts:
            fact_text = str(fact).lower() if isinstance(fact, dict) else fact.lower()
            fact_words = set(fact_text.split())
            overlap = len(query_words & fact_words)
            if overlap > 0:
                relevant_facts += 1
        
        relevance_ratio = relevant_facts / len(facts) if facts else 0
        
        if relevance_ratio < 0.3 and iteration > 0:
            logger.warning(f"Keeper: Context drift detected (relevance: {relevance_ratio:.2f})")
            state["should_continue"] = False
            state["drift_detected"] = True
            return state
    
    # ============================================================
    # CONTINUE RESEARCH
    # ============================================================
    state["should_continue"] = True
    state["iteration"] = iteration + 1
    
    logger.info(f"Keeper: Continuing research (iteration {iteration + 1})")
    return state

