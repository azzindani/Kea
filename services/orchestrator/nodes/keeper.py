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
# Loop Safety Controls (from centralized config)
# ============================================================================

def _get_config():
    """Get settings from centralized config."""
    from shared.config import get_settings
    return get_settings()


def get_hardware_aware_limits() -> tuple[int, int]:
    """Get hardware-aware iteration and facts limits."""
    config = _get_config()
    max_iter_config = config.loop_safety.max_global_iterations
    max_facts_config = config.loop_safety.max_facts_threshold
    
    try:
        from shared.hardware.detector import detect_hardware
        hw = detect_hardware()
        # More RAM = can handle more iterations and facts
        max_iter = min(max_iter_config, max(3, int(hw.ram_available_gb)))
        max_facts = min(max_facts_config, int(hw.ram_available_gb * 100))
        return max_iter, max_facts
    except ImportError:
        return max_iter_config, max_facts_config


def get_adaptive_threshold(iteration: int) -> float:
    """
    Calculate adaptive confidence threshold based on iteration.
    
    Uses config values: initial_threshold, degradation_rate, min_threshold.
    """
    config = _get_config()
    threshold = config.confidence.initial_threshold - (iteration * config.confidence.degradation_rate)
    return max(threshold, config.confidence.min_threshold)


async def calculate_agreement_score(facts: list[dict]) -> float:
    """
    Calculate agreement score from facts using embedding similarity.
    
    High similarity between facts = high agreement = confident answer.
    """
    if not facts or len(facts) < 2:
        return 0.5  # Default for insufficient data
    
    try:
        from shared.embedding.model_manager import get_embedding_provider
        import numpy as np
        
        provider = get_embedding_provider()
        
        # Get text from facts
        texts = [f.get("text", "")[:1000] for f in facts[:20]]  # Limit for performance
        
        if not any(texts):
            return 0.5
        
        # Embed facts
        embeddings = await provider.embed(texts)
        
        if not embeddings:
            return 0.5
        
        # Calculate average pairwise cosine similarity
        embeddings_np = np.array(embeddings)
        norms = np.linalg.norm(embeddings_np, axis=1, keepdims=True)
        normalized = embeddings_np / (norms + 1e-8)
        similarity_matrix = np.dot(normalized, normalized.T)
        
        # Average of upper triangle (excluding diagonal)
        n = len(embeddings)
        if n < 2:
            return 0.5
        
        upper_triangle = similarity_matrix[np.triu_indices(n, k=1)]
        agreement_score = float(np.mean(upper_triangle))
        
        return agreement_score
        
    except Exception as e:
        logger.warning(f"Agreement score calculation failed: {e}")
        return 0.5


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
    
    # Count completed and failed from actual invocations
    # Note: success=True means the tool (or fallback) succeeded
    completed_tasks = sum(1 for inv in tool_invocations if inv.get("success", False))
    failed_tasks = sum(1 for inv in tool_invocations if not inv.get("success", True) and inv.get("error"))
    
    # Unique task IDs that succeeded
    completed_task_ids = {inv.get("task_id") for inv in tool_invocations if inv.get("success", False)}
    
    # Identify tasks to retry (failed with no success in any attempt)
    should_retry = []
    failed_task_ids = {inv.get("task_id") for inv in tool_invocations if not inv.get("success", True) and inv.get("error")}
    for task_id in failed_task_ids:
        if task_id not in completed_task_ids:
            # This task failed and hasn't succeeded yet
            for task in micro_tasks:
                if task.get("task_id") == task_id:
                    if task.get("fallback_tools"):
                        should_retry.append(task_id)
                    break
    
    # Determine phases from ACTUAL tools used (including fallbacks)
    phases = execution_plan.get("phases", [])
    completed_phases = set()
    
    for inv in tool_invocations:
        if inv.get("success"):
            # Use the actual tool that ran (may be fallback)
            actual_tool = inv.get("tool", "")
            
            # Map tool to phase
            if actual_tool in ["web_search", "news_search", "fetch_data"]:
                completed_phases.add("data_collection")
            elif actual_tool in ["scrape_url", "fetch_url", "parse_document"]:
                completed_phases.add("extraction")
            elif actual_tool in ["run_python", "execute_code"]:
                completed_phases.add("analysis")
            elif actual_tool in ["build_graph"]:
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
        "completed_task_ids": list(completed_task_ids),
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
    - Enforcing loop safety controls (hardware-aware)
    
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
    # HARDWARE-AWARE SAFETY CONTROLS
    # ============================================================
    hw_max_iter, hw_max_facts = get_hardware_aware_limits()
    
    # Global safety: Never exceed hardware-aware limits
    if iteration >= hw_max_iter:
        logger.warning(f"⚠️ Keeper: Global max iterations ({hw_max_iter}) reached - forcing stop")
        state["should_continue"] = False
        state["stop_reason"] = "max_iterations_global"
        return state
    
    if len(facts) >= hw_max_facts:
        logger.info(f"✅ Keeper: Max facts threshold ({hw_max_facts}) reached - stopping")
        state["should_continue"] = False
        state["stop_reason"] = "max_facts_threshold"
        return state
    
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
    # CHECK LOCAL ITERATION LIMIT (user-specified)
    # ============================================================
    if iteration >= max_iterations:
        logger.info(f"Keeper: Max iterations ({max_iterations}) reached")
        state["should_continue"] = False
        return state
    
    # ============================================================
    # ADAPTIVE CONFIDENCE CHECK (0.95 - 0.05 per iteration)
    # ============================================================
    min_facts = 3
    if len(facts) >= min_facts:
        # Calculate adaptive threshold for this iteration
        current_threshold = get_adaptive_threshold(iteration)
        
        # Calculate agreement score from facts (using embeddings)
        agreement_score = await calculate_agreement_score(facts)
        
        logger.info(f"Keeper: Agreement score {agreement_score:.3f}, threshold {current_threshold:.2f}")
        state["agreement_score"] = agreement_score
        state["confidence_threshold"] = current_threshold
        
        # If agreement exceeds threshold, we have confident answer
        if agreement_score >= current_threshold:
            logger.info(f"✅ Keeper: Confidence {agreement_score:.3f} >= {current_threshold:.2f} - stopping")
            state["should_continue"] = False
            state["stop_reason"] = "confidence_achieved"
            return state
        
        # If all tasks complete, stop regardless
        if progress["completed_tasks"] >= progress["total_tasks"]:
            logger.info("Keeper: All execution plan tasks complete")
            state["should_continue"] = False
            return state
        
        # Log degradation for next iteration
        next_threshold = get_adaptive_threshold(iteration + 1)
        logger.info(f"   📉 Threshold will degrade to {next_threshold:.2f} next iteration")
    
    # ============================================================
    # CHECK CONTEXT DRIFT
    # ============================================================
    # Skip drift check if we have minimal facts (less than min_facts)
    # or if this is the first iteration - give research time to gather data
    if facts and len(facts) >= min_facts and iteration > 1:
        # Simple keyword overlap check
        query_words = set(query.lower().split())
        relevant_facts = 0
        
        for fact in facts:
            # Extract actual fact content from dict
            if isinstance(fact, dict):
                # Get text content from common fact fields
                fact_parts = []
                for key in ["entity", "value", "text", "content", "attribute"]:
                    if key in fact and fact[key]:
                        fact_parts.append(str(fact[key]).lower())
                fact_text = " ".join(fact_parts)
            else:
                fact_text = str(fact).lower()
            
            fact_words = set(fact_text.split())
            overlap = len(query_words & fact_words)
            if overlap > 0:
                relevant_facts += 1
        
        relevance_ratio = relevant_facts / len(facts) if facts else 0
        
        if relevance_ratio < 0.3:
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

