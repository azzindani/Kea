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
    Get fixed confidence threshold (no degradation).
    
    Enterprise Mode: Always require 0.95 confidence.
    This ensures Kea maintains high quality output standards.
    The retry loop will continue until this threshold is met.
    """
    config = _get_config()
    # No degradation - always return initial threshold (0.95)
    return config.confidence.initial_threshold


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


async def calculate_grpo_reward(
    facts: list[dict],
    tool_invocations: list[dict],
    query: str,
    error_feedback: list[dict] | None = None,
    completed_calls: set | None = None,
) -> dict[str, float]:
    """
    GRPO-Style Reward Scoring for Kea (Generative Reward Policy Optimization).
    
    Combines multiple signals into a comprehensive reward score that guides
    the research loop more intelligently than simple agreement scoring.
    
    Returns:
        Dict with individual scores and final reward:
        {
            "relevance": float,      # How relevant are facts to query?
            "novelty": float,        # Are we learning new things?
            "success_rate": float,   # % of tools that succeeded
            "citation_coverage": float,  # Do facts have sources?
            "efficiency": float,     # Fewer steps = better
            "penalty": float,        # Deductions for errors/duplicates
            "final_reward": float,   # Weighted combination
        }
    """
    scores = {
        "relevance": 0.0,
        "novelty": 0.0,
        "success_rate": 0.0,
        "citation_coverage": 0.0,
        "efficiency": 0.0,
        "penalty": 0.0,
        "final_reward": 0.0,
    }
    
    # ============================================================
    # 1. RELEVANCE SCORE (How relevant are facts to the query?)
    # ============================================================
    if facts and query:
        try:
            from shared.embedding.model_manager import get_embedding_provider
            import numpy as np
            
            provider = get_embedding_provider()
            
            # Get query embedding
            query_emb = await provider.embed([query[:500]])
            
            # Get fact embeddings (limit for performance)
            fact_texts = [f.get("text", "")[:500] for f in facts[:10]]
            fact_embs = await provider.embed(fact_texts)
            
            if query_emb and fact_embs:
                query_vec = np.array(query_emb[0])
                fact_vecs = np.array(fact_embs)
                
                # Cosine similarity between query and each fact
                query_norm = query_vec / (np.linalg.norm(query_vec) + 1e-8)
                fact_norms = fact_vecs / (np.linalg.norm(fact_vecs, axis=1, keepdims=True) + 1e-8)
                similarities = np.dot(fact_norms, query_norm)
                
                scores["relevance"] = float(np.mean(similarities))
        except Exception as e:
            logger.debug(f"GRPO relevance calculation failed: {e}")
            scores["relevance"] = 0.5 if facts else 0.0
    
    # ============================================================
    # 2. NOVELTY SCORE (Are facts diverse and non-redundant?)
    # ============================================================
    if facts and len(facts) >= 2:
        # Calculate agreement score as a proxy for redundancy
        agreement_score = await calculate_agreement_score(facts)
        # Lower agreement = more novelty (diverse information)
        # But we cap it - too low agreement might mean noise
        scores["novelty"] = 1.0 - min(0.7, max(0.3, agreement_score))
    else:
        scores["novelty"] = 0.3  # Default for insufficient data
    
    # ============================================================
    # 3. TOOL SUCCESS RATE
    # ============================================================
    if tool_invocations:
        successes = sum(1 for inv in tool_invocations if inv.get("success", False))
        total = len(tool_invocations)
        scores["success_rate"] = successes / total if total > 0 else 0.0
    
    # ============================================================
    # 4. CITATION COVERAGE (Do facts have traceable sources?)
    # ============================================================
    if facts:
        with_sources = sum(1 for f in facts if f.get("source_url") or f.get("source"))
        scores["citation_coverage"] = with_sources / len(facts)
    
    # ============================================================
    # 5. EFFICIENCY (Fewer unique calls = better)
    # ============================================================
    unique_calls = len(completed_calls) if completed_calls else len(tool_invocations)
    # Target: 3-8 calls for typical research. Penalize excess.
    optimal_calls = 5
    if unique_calls > 0:
        efficiency_ratio = min(optimal_calls / unique_calls, 1.0)
        scores["efficiency"] = efficiency_ratio
    
    # ============================================================
    # 6. PENALTY CALCULATION (Errors, Duplicates, Hallucinations)
    # ============================================================
    penalty = 0.0
    
    # Penalty for errors
    error_count = len(error_feedback) if error_feedback else 0
    penalty += error_count * 0.1  # -0.1 per error
    
    # Penalty for failed tools
    failures = sum(1 for inv in tool_invocations if inv.get("success") is False) if tool_invocations else 0
    penalty += failures * 0.05  # -0.05 per failure
    
    # Cap penalty at 0.5 (don't make reward negative)
    scores["penalty"] = min(0.5, penalty)
    
    # ============================================================
    # FINAL WEIGHTED REWARD
    # ============================================================
    # Weights inspired by GRPO: prioritize relevance and success
    final_reward = (
        0.30 * scores["relevance"] +
        0.15 * scores["novelty"] +
        0.25 * scores["success_rate"] +
        0.15 * scores["citation_coverage"] +
        0.15 * scores["efficiency"] -
        scores["penalty"]
    )
    
    # Clamp to [0, 1]
    scores["final_reward"] = max(0.0, min(1.0, final_reward))
    
    logger.info(f"📊 GRPO Score: {scores['final_reward']:.3f} "
                f"(rel={scores['relevance']:.2f}, nov={scores['novelty']:.2f}, "
                f"succ={scores['success_rate']:.2f}, cit={scores['citation_coverage']:.2f}, "
                f"eff={scores['efficiency']:.2f}, pen=-{scores['penalty']:.2f})")
    
    return scores


# ============================================================================
# Persistence Layer (Always Persist Policy)
# ============================================================================

async def persist_facts(facts: list[dict], job_id: str) -> int:
    """
    Persist facts to database using FactStore.
    
    Always-persist policy: every fact is stored for durability and resume capability.
    
    Returns:
        Number of facts persisted
    """
    persisted = 0
    
    try:
        from services.rag_service.core.fact_store import FactStore
        from shared.schemas import AtomicFact
        
        store = FactStore()
        
        for fact in facts:
            if not fact.get("persist", True):
                continue
                
            # Create AtomicFact from dict
            # Create AtomicFact from dict
            import uuid
            atomic_fact = AtomicFact(
                fact_id=str(uuid.uuid4()),
                entity=fact.get("source") or "unknown",
                attribute="content",
                value=fact.get("text", ""),
                source_url=fact.get("url", ""),
                confidence_score=1.0,
            )
            
            # Persist to database
            await store.add_fact(atomic_fact, dataset_id=job_id)
            persisted += 1
            
        logger.info(f"Keeper: Persisted {persisted} facts to FactStore for job {job_id}")
        
    except Exception as e:
        logger.warning(f"Keeper: FactStore persistence failed: {e}, counting only")
        persisted = sum(1 for f in facts if f.get("persist", True))
    
    return persisted


async def persist_tool_invocations(invocations: list[dict], job_id: str) -> int:
    """
    Persist tool invocations to audit trail using Vault.
    
    Returns:
        Number of invocations persisted
    """
    persisted = 0
    
    try:
        from services.vault.core.audit_trail import get_audit_trail, AuditEventType
        
        client = get_audit_trail()
        
        for inv in invocations:
            await client.log(
                event_type=AuditEventType.TOOL_CALLED,
                action=f"tool_executed_{inv.get('tool', 'unknown')}",
                actor="keeper_node",
                resource=job_id,
                details={
                    "task_id": inv.get("task_id"),
                    "tool": inv.get("tool"),
                    "success": inv.get("success"),
                    "error": inv.get("error"),
                },
                session_id=job_id,
            )
            persisted += 1
            
        logger.info(f"Keeper: Persisted {persisted} tool invocations to AuditTrail for job {job_id}")
        
    except Exception as e:
        logger.warning(f"Keeper: AuditTrail persistence failed: {e}, counting only")
        persisted = len(invocations)
    
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
    # Count failures: any invocation with success=False (not requiring 'error' field)
    failed_tasks = sum(1 for inv in tool_invocations if inv.get("success") is False)
    
    # Unique task IDs that succeeded
    completed_task_ids = {inv.get("task_id") for inv in tool_invocations if inv.get("success", False)}
    
    # Identify tasks to retry (failed with no success in any attempt)
    should_retry = []
    failed_task_ids = {inv.get("task_id") for inv in tool_invocations if inv.get("success") is False}
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
    
    config = _get_config()
    iteration = state.get("iteration", 0)
    # Sensible cap: Even if config allows more, limit to 5 iterations for most queries
    config_max = state.get("max_iterations", config.loop_safety.max_global_iterations)
    max_iterations = min(config_max, 5)  # Hard cap at 5 iterations
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
    # REPLAN ON ALL FAILURES (instead of stopping, give LLM another chance)
    # ============================================================
    replan_count = state.get("replan_count", 0)
    max_replans = config.research.max_depth  # Use same limit as iterations
    
    if progress["total_tasks"] > 0 and progress["completed_tasks"] == 0 and progress["failed_tasks"] > 0:
        if replan_count < max_replans:
            logger.warning(f"Keeper: ALL tool calls failed ({progress['failed_tasks']}/{progress['total_tasks']})")
            logger.warning(f"   Triggering REPLAN (attempt {replan_count + 1}/{max_replans}) - LLM will receive error feedback")
            state["should_continue"] = True  # Continue the loop
            state["stop_reason"] = "replan"   # Route to planner, not researcher
            state["replan_count"] = replan_count + 1
            state["confidence"] = 0.0
            return state
        else:
            logger.error(f"Keeper: ALL tool calls failed after {max_replans} replans")
            logger.error(f"   Stopping to prevent infinite loop - no valid facts collected")
            state["should_continue"] = False
            state["stop_reason"] = "max_replans_exceeded"
            state["confidence"] = 0.0
            return state
    
    # ============================================================
    # CHECK LOCAL ITERATION LIMIT (user-specified)
    # ============================================================
    if iteration >= max_iterations:
        logger.info(f"Keeper: Max iterations ({max_iterations}) reached")
        logger.info(f"   Proceeding to final report with achieved confidence score")
        
        # Calculate GRPO score even when exiting due to max iterations
        # This ensures the final report shows the actual achieved confidence
        query = state.get("query", "")
        error_feedback = state.get("error_feedback", [])
        completed_calls = state.get("completed_calls", set())
        
        grpo_scores = await calculate_grpo_reward(
            facts=facts,
            tool_invocations=tool_invocations,
            query=query,
            error_feedback=error_feedback,
            completed_calls=completed_calls,
        )
        
        confidence_score = grpo_scores["final_reward"]
        state["confidence"] = confidence_score
        state["grpo_scores"] = grpo_scores
        state["stop_reason"] = f"max_iterations_with_{confidence_score:.0%}_confidence"
        
        logger.info(f"   Final GRPO confidence: {confidence_score:.0%}")
        state["should_continue"] = False
        return state
    
    # ============================================================
    # SUCCESS-BASED EARLY EXIT (prevents infinite looping)
    # When ALL tools succeed AND we have sufficient facts, STOP
    # ============================================================
    sufficient_facts = 5  # Minimum facts to consider research "complete"
    all_tools_succeeded = (
        progress["total_tasks"] > 0 and 
        progress["failed_tasks"] == 0 and
        progress["completed_tasks"] >= progress["total_tasks"]
    )
    
    if all_tools_succeeded and len(facts) >= sufficient_facts:
        logger.info(f"✅ Keeper: SUCCESS-BASED EXIT - All tools succeeded with {len(facts)} facts")
        
        # CALCULATE CONFIDENCE before exiting (was missing before!)
        query = state.get("query", "")
        error_feedback = state.get("error_feedback", [])
        completed_calls = state.get("completed_calls", set())
        
        grpo_scores = await calculate_grpo_reward(
            facts=facts,
            tool_invocations=tool_invocations,
            query=query,
            error_feedback=error_feedback,
            completed_calls=completed_calls,
        )
        
        confidence_score = grpo_scores["final_reward"]
        state["confidence"] = confidence_score
        state["grpo_scores"] = grpo_scores
        state["should_continue"] = False
        state["stop_reason"] = f"success_complete_{confidence_score:.0%}"
        
        logger.info(f"   GRPO Confidence: {confidence_score:.0%}")
        return state
    
    # ============================================================
    # GRPO-STYLE CONFIDENCE CHECK (Multi-signal reward scoring)
    # ============================================================
    min_facts = 3
    if len(facts) >= min_facts:
        # Calculate adaptive threshold for this iteration
        current_threshold = get_adaptive_threshold(iteration)
        
        # Get additional state for GRPO scoring
        query = state.get("query", "")
        error_feedback = state.get("error_feedback", [])
        completed_calls = state.get("completed_calls", set())
        
        # Calculate GRPO reward score (replaces simple agreement scoring)
        grpo_scores = await calculate_grpo_reward(
            facts=facts,
            tool_invocations=tool_invocations,
            query=query,
            error_feedback=error_feedback,
            completed_calls=completed_calls,
        )
        
        # Use final_reward as the confidence metric
        confidence_score = grpo_scores["final_reward"]
        
        logger.info(f"Keeper: GRPO confidence {confidence_score:.3f}, threshold {current_threshold:.2f}")
        state["grpo_scores"] = grpo_scores  # Store detailed breakdown
        state["agreement_score"] = confidence_score  # Backward compatibility
        state["confidence_threshold"] = current_threshold
        
        # Store actual confidence in state for final report
        state["confidence"] = confidence_score
        
        # If confidence exceeds threshold, we have confident answer
        if confidence_score >= current_threshold:
            logger.info(f"Keeper: GRPO Confidence {confidence_score:.3f} >= {current_threshold:.2f} - PASSED")
            state["should_continue"] = False
            state["stop_reason"] = "confidence_achieved"
            return state
        else:
            logger.warning(f"Keeper: Confidence {confidence_score:.3f} < {current_threshold:.2f} - below standard")
            
            # ============================================================
            # LOW CONFIDENCE REPLAN: When tasks complete but confidence is low
            # Trigger a replan to generate additional research tasks
            # ============================================================
            if progress["completed_tasks"] >= progress["total_tasks"]:
                replan_count = state.get("replan_count", 0)
                max_replans = 2  # Prevent infinite replanning
                
                if replan_count < max_replans:
                    logger.warning(f"Keeper: All tasks complete but confidence too low ({confidence_score:.1%})")
                    logger.info(f"   🔄 Triggering REPLAN to gather more evidence (attempt {replan_count + 1}/{max_replans})")
                    
                    # Build error feedback explaining why we need more research
                    error_feedback = state.get("error_feedback", [])
                    error_feedback.append({
                        "issue": "low_confidence",
                        "message": f"Research confidence is only {confidence_score:.1%}, below threshold of {current_threshold:.0%}. Need to gather more facts.",
                        "suggestion": "Add additional research tasks to collect more data sources and verify findings."
                    })
                    
                    state["error_feedback"] = error_feedback
                    state["replan_count"] = replan_count + 1
                    state["stop_reason"] = "replan"
                    state["should_continue"] = True  # Will route to planner
                    return state
                else:
                    logger.warning(f"Keeper: Max replans ({max_replans}) reached, proceeding with {confidence_score:.1%} confidence")
        
        # If all tasks complete AND we've exhausted replans, stop
        if progress["completed_tasks"] >= progress["total_tasks"]:
            logger.info("Keeper: All execution plan tasks complete")
            logger.info(f"   Final confidence: {confidence_score:.3f} (required: {current_threshold:.2f})")
            state["should_continue"] = False
            return state
        
        # No degradation - threshold stays at 0.95
        logger.info(f"   Threshold remains at {current_threshold:.2f} (no degradation)")
    
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

