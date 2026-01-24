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
from services.vault.core.audit_trail import audited, AuditEventType

# Import real implementations
from services.orchestrator.nodes.planner import planner_node as real_planner_node
from services.orchestrator.nodes.keeper import keeper_node as real_keeper_node
from services.orchestrator.agents.generator import GeneratorAgent
from services.orchestrator.agents.critic import CriticAgent
from services.orchestrator.agents.judge import JudgeAgent
from services.orchestrator.core.router import IntentionRouter

# NEW: Context pool and code generator for dynamic data flow
from shared.context_pool import get_context_pool, reset_context_pool
from services.orchestrator.agents.code_generator import generate_fallback_code, generate_python_code



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
    """Route query to appropriate execution path with Memory & Intent."""
    query = state.get("query", "")
    job_id = state.get("job_id", "unknown_session")
    
    logger.info("\n" + "="*70)
    logger.info("📍 STEP 1: ROUTER NODE (Memory Aware)")
    logger.info("="*70)
    logger.info(f"Query: {query[:200]}...")
    
    # =========================================================================
    # Phase 2: Memory & Intent Integration
    # =========================================================================
    from services.orchestrator.core.conversation import get_conversation_manager, Intent
    
    mem_mgr = get_conversation_manager()
    
    # We use job_id as session_id for now for simplicity
    # In a real app, session_id would be distinct from job_id
    resp = await mem_mgr.process(session_id=job_id, message=query)
    
    logger.info(f"🧠 Intent Detected: {resp.intent.value.upper()}")
    
    context_str = ""
    if resp.intent == Intent.FOLLOW_UP:
        context_str = resp.context
        logger.info(f"📚 Retrieved Context ({len(context_str)} chars)")
        # Inject context into query for the Planner to see
        # We append it so the Planner knows what "it" refers to
        state["query"] = f"{query}\n\n[CONTEXT FROM MEMORY]:\n{context_str}"
        
    elif resp.intent == Intent.NEW_TOPIC:
        logger.info("✨ New Topic Detected - Clearing localized context")
        # No context injection
        
    # =========================================================================

    router = IntentionRouter()
    context = {
        "prior_research": state.get("prior_research"),
        "data_to_verify": state.get("data_to_verify"),
        "memory_context": context_str
    }
    
    path = await router.route(query, context)
    
    logger.info(f"✅ Selected Path: {path}")
    logger.info(f"   A = Memory Fork | B = Shadow Lab | C = Grand Synthesis | D = Deep Research")
    logger.info("="*70 + "\n")
    
    return {
        **state,
        "path": path,
        "status": "running",
    }


@audited(AuditEventType.QUERY_CLASSIFIED, "Planner Node decomposed query")
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

@audited(AuditEventType.TOOL_CALLED, "Researcher Node executed iteration")
async def researcher_node(state: GraphState) -> GraphState:
    """Execute research using execution plan with dynamic tool routing and PARALLEL execution."""
    iteration = state.get("iteration", 1)
    
    logger.info("\n" + "="*70)
    logger.info(f"📍 STEP 3: RESEARCHER NODE (Iteration {iteration}) - Parallel Tool Execution")
    logger.info("="*70)
    
    execution_plan = state.get("execution_plan", {})
    micro_tasks = execution_plan.get("micro_tasks", [])
    sub_queries = state.get("sub_queries", [])
    query = state.get("query", "")
    facts = state.get("facts", [])
    sources = state.get("sources", [])
    tool_invocations = state.get("tool_invocations", [])
    
    # Reset context pool for new research iteration
    if iteration == 1:
        reset_context_pool()
    
    # If no execution plan, fall back to sub-queries with web_search
    if not micro_tasks:
        logger.info("No execution plan, falling back to sub-query based web search")
        micro_tasks = [
            {"task_id": f"task_{i+1}", "description": sq, "tool": "web_search", 
             "inputs": {"query": sq}, "fallback_tools": ["news_search"], "persist": True}
            for i, sq in enumerate(sub_queries or [query])
        ]
    
    # =========================================================================
    # Phase 3: Fractal Spawning (High Complexity)
    # =========================================================================
    if len(micro_tasks) > 5:
        logger.info(f"🚀 High Complexity Detected ({len(micro_tasks)} tasks) -> Spawning Fractal Swarm")
        try:
            from services.orchestrator.core.agent_spawner import get_spawner
            # Use strict imports to avoid shadowing
            from services.orchestrator.core.organization import get_organization 
            # Domain is imported from agent_spawner below (which uses prompt_factory.Domain)
            
            # Simple prompt callback wrapper for spawner
            # Ideally this uses the real LLM, but for now we pass a dummy or use existing infrastructure
            # We will skip the complex 'plan_execution' and use 'execute_swarm' directly on our micro_tasks
            spawner = get_spawner()
            
            # Convert micro_tasks to Spawner SubTasks
            from services.orchestrator.core.agent_spawner import SubTask, SpawnPlan, TaskType, Domain
            import uuid
            
            subtasks = []
            for t in micro_tasks:
                subtasks.append(SubTask(
                    subtask_id=t.get("task_id"),
                    query=t.get("description"),
                    domain=Domain.RESEARCH, 
                    task_type=TaskType.RESEARCH,
                    preferred_tool=t.get("tool") # Pass context from Planner
                ))
                
            plan = SpawnPlan(
                task_id=state.get("job_id", "swarm"),
                subtasks=subtasks,
                max_parallel=len(micro_tasks) # Go wild
            )
            
            # Execute Swarm
            logger.info(f"💥 Executing Fractal Swarm for {len(subtasks)} subtasks...")
            swarm_result = await spawner.execute_swarm(plan)
            
            # Convert Swarm Result to Facts
            for res in swarm_result.agent_results:
                if res.status == "completed":
                    facts.append({
                        "text": str(res.result)[:1000],
                        "query": f"Swarm Agent {res.agent_id}: {res.prompt_used[:50]}...",
                        "source": "fractal_swarm",
                        "task_id": res.subtask_id,
                        "persist": True
                    })
                    # Mark as completed so we skip standard execution for these
                    pass # Logic handled by clearing micro_tasks below
                    # Wait, 'completed' set is defined below in the standard loop.
                    # We need to skip the standard loop entirely or mark specific tasks as done.
                    # Since we did ALL micro_tasks in the swarm, we can just return or clear micro_tasks.
            
            # Log success
            logger.info(f"✅ Swarm Complete: {swarm_result.successful} successful, {swarm_result.failed} failed")
            
            # If swarm succeeded significantly, we can skip standard execution
            if swarm_result.successful > 0:
                # Add dummy tool invocations for tracking
                for res in swarm_result.agent_results:
                     tool_invocations.append({
                        "task_id": res.subtask_id,
                        "tool": "swarm_agent",
                        "success": res.status == "completed",
                        "persist": True
                     })
                
                logger.info("⚡ Skipping standard execution loop (Swarm handled tasks)")
                # Clear micro_tasks to skip standard loop
                micro_tasks = [] 
            else:
                 logger.warning(f"⚠️ Swarm failed to produce results ({swarm_result.failed} failed). Falling back to Standard Executor.")
                 for res in swarm_result.agent_results:
                     if res.error:
                         logger.warning(f"   ❌ Agent {res.agent_id} error: {res.error}")
                     elif res.result and "Exception" in str(res.result):
                         logger.warning(f"   ❌ Agent {res.agent_id} exception: {str(res.result)[:200]}")            
        except ImportError:
            pass
            
    # =========================================================================

    # 1. Hardware-Aware Scaling
    from shared.hardware.detector import detect_hardware
    from services.mcp_host.core.parallel_executor import ParallelExecutor, ToolCall
    from services.mcp_host.core.session_registry import get_session_registry
    
    hw_profile = detect_hardware()
    max_workers = hw_profile.optimal_workers()
    logger.info(f"🚀 Hardware-Aware Dispatcher: Using {max_workers} parallel workers (RAM: {hw_profile.ram_available_gb:.1f}GB)")
    
    executor = ParallelExecutor(max_concurrent=max_workers)
    registry = get_session_registry()
    
    # Tool registry for dynamic routing
    # NOTE: We have removed direct imports to enforce "Pure MCP" architecture.
    # All tools are now discovered dynamically via SessionRegistry.
    
    def build_tool_inputs(tool_name: str, description: str, original_inputs: dict, collected_facts: list = None) -> dict:
        """Build proper inputs based on tool requirements."""
        ctx = get_context_pool()
        
        # PYTHON TOOLS
        if tool_name in ["run_python", "execute_code", "parse_document"]:
            if "code" in original_inputs: return original_inputs
            code = generate_fallback_code(description, collected_facts or [])
            return {"code": code}
        
        if tool_name in ["sql_query", "dataframe_ops", "analyze_data"]:
             # TRANSFORM: Smart Logic -> Python Code
             if "code" in original_inputs: return original_inputs
             
             # If we have unstructured query, generate code
             code = generate_fallback_code(description, collected_facts or [])
             return {"code": code}
        
        # SCRAPING & CRAWLING
        if tool_name in ["scrape_url", "fetch_url", "link_extractor", "sitemap_parser"]:
            if "url" in original_inputs: return original_inputs
            
            # ORCHESTRATION FIX: Auto-chain URLs from context pool
            # If no URL provided, pull one from the pool of discovered URLs
            next_url = ctx.get_url()
            if next_url:
                logger.info(f"   🔗 Chained URL from pool to {tool_name}: {next_url}")
                return {"url": next_url}
                
            return None
        
        if tool_name == "web_crawler":
            if "start_url" in original_inputs: return original_inputs
            crawl_url = ctx.get_url()
            if crawl_url: return {"start_url": crawl_url, "max_depth": 3, "max_pages": 50}
            return None

        # BROWSER TOOLS
        if tool_name in ["human_search", "human_like_search"]:
            if "query" in original_inputs: return {"query": original_inputs["query"], "max_sites": 10}
            return {"query": description, "max_sites": 10}
            
        if tool_name == "source_validator":
            if "url" in original_inputs: return original_inputs
            next_url = ctx.get_url()
            if next_url: return {"url": next_url}
            return None
            
        if tool_name == "multi_browse":
            if "urls" in original_inputs: return original_inputs
            return None

        # SEARCH TOOLS (default)
        if tool_name in ["web_search", "news_search", "fetch_data"]:
            if "query" in original_inputs: return original_inputs
            return {"query": description, "max_results": 20}
            
        return original_inputs


    # 2. Unified Tool Handler (INTELLIGENCE INJECTED)
    async def unified_tool_handler(name: str, args: dict) -> Any:
        # Resolve target server dynamically
        server_name = registry.get_server_for_tool(name)
        
        if not server_name:
            # Fallback Mapping (Legacy Support)
            legacy_map = {
                "run_python": "execute_code",
                "fetch_page": "fetch_url"
            }
            mapped = legacy_map.get(name)
            if mapped:
                server_name = registry.get_server_for_tool(mapped)
                if server_name:
                    logger.info(f"🔄 Mapped {name} -> {mapped} on {server_name}")
                    name = mapped # Switch to actual tool name
            
        if not server_name:
             # Try JIT Discovery
             await registry.list_all_tools()
             server_name = registry.get_server_for_tool(name)
        
        if not server_name:
             raise ValueError(f"Tool {name} not found in SessionRegistry.")
            
        # Execute
        try:
            session = await registry.get_session(server_name)
            result = await session.call_tool(name, args)
        except Exception as e:
            logger.error(f"Tool execution failed: {e}")
            raise ValueError(f"Tool {name} failed: {e}")

        # =========================================================================
        # AUTONOMIC MEMORY INTERCEPTOR (The Wiring Fix)
        # =========================================================================
        try:
            from services.orchestrator.core.interceptor import MemoryInterceptor
            job_id = state.get("job_id", "unknown_trace")
            
            # Fire-and-forget storage to Postgres
            await MemoryInterceptor.intercept(
                trace_id=job_id,
                source_node=name,
                result=result,
                inputs=args
            )
        except Exception as e:
            logger.warning(f"Interceptor failed (non-blocking): {e}")
        # =========================================================================

        return result

    # 3. Parallel Execution Loop
    completed = {inv["task_id"] for inv in tool_invocations if inv.get("success")}
    processed_this_run = set()
    
    while True:
        # Find ready tasks
        ready_tasks = []
        for task in micro_tasks:
            t_id = task.get("task_id")
            if t_id in completed or t_id in processed_this_run:
                continue
                
            # Check dependencies
            deps = task.get("depends_on", [])
            if all(d in completed for d in deps):
                ready_tasks.append(task)
        
        if not ready_tasks:
            break
            
        # Batch execute
        batch = ready_tasks[:max_workers * 2] # Allow slight over-subscription for IO wait
        processed_this_run.update(t.get("task_id") for t in batch)
        
        logger.info(f"\n⚡ Batching {len(batch)} tasks...")
        
        # Prepare calls
        calls = []
        task_map = {} # index -> task
        
        for idx, task in enumerate(batch):
            t_name = task.get("tool", "web_search")
            t_desc = task.get("description", "")
            t_inputs = task.get("inputs", {})
            t_id = task.get("task_id")
            
            final_inputs = build_tool_inputs(t_name, t_desc, t_inputs, facts)
            
            # Handle input build failure (fallback immediately or skip)
            if final_inputs is None:
                # Try fallback
                fallback_tools = task.get("fallback_tools") or ["web_search"]
                t_name = fallback_tools[0]
                
                # Attempt to build inputs for fallback tool
                final_inputs = build_tool_inputs(t_name, t_desc, t_inputs, facts)
                
                if final_inputs is None:
                    # Ultimate fallback to web_search
                    t_name = "web_search"
                    final_inputs = {"query": t_desc, "max_results": 10}
            
            calls.append(ToolCall(tool_name=t_name, arguments=final_inputs))
            task_map[idx] = task
            
        # EXECUTE BATCH
        results = await executor.execute_batch(calls, unified_tool_handler)
        
        # Process results
        for idx, res in enumerate(results):
            task = task_map[idx]
            t_id = task.get("task_id")
            t_persist = task.get("persist", True)
            
            success = res.success
            error_msg = None
            content_text = ""
            
            if success and res.result and hasattr(res.result, "content"):
                for c in res.result.content:
                    if hasattr(c, "text"):
                        content_text += c.text
                
                # Verify content isn't error text
                if "error" in content_text.lower() and len(content_text) < 200:
                     # Soft error check
                     pass

            if success:
                # Extract Facts
                fact = {
                    "text": content_text[:1000],
                    "query": task.get("description", "")[:200],
                    "source": calls[idx].tool_name,
                    "task_id": t_id,
                    "persist": t_persist
                }
                facts.append(fact)
                
                # Extract Sources
                ctx = get_context_pool()
                extracted_urls = ctx.extract_urls_from_text(content_text)
                for url in extracted_urls[:10]:
                    sources.append({
                        "url": url,
                        "title": task.get("description", "")[:80],
                        "tool": calls[idx].tool_name,
                        "task_id": t_id
                    })
                
                completed.add(t_id)
                logger.info(f"   ✅ Task {t_id} completed via {calls[idx].tool_name}")
            else:
                # Handle hard failure - extract clean error message
                tool_name = calls[idx].tool_name
                error_text = "Unknown error"
                
                # Extract error text from result
                if res.result and hasattr(res.result, "content"):
                    for c in res.result.content:
                        if hasattr(c, "text"):
                            error_text = c.text
                            break
                elif res.result:
                    error_text = str(res.result)
                
                # Clean up common error patterns for readability
                if "Tool execution error:" in error_text:
                    error_text = error_text.replace("Tool execution error:", "Missing parameter:")
                
                logger.warning(f"   ❌ Task {t_id} ({tool_name}) FAILED: {error_text}")
                
                # We do NOT add to completed, so it won't satisfy dependencies. 
                # Ideally we should try fallbacks here, but for now we mark failed to avoid infinite loop
                tool_invocations.append({
                    "task_id": t_id,
                    "tool": tool_name,
                    "success": False,
                    "error": error_text
                })
                # Prevent re-execution to avoid infinite loop
                completed.add(t_id) 

            # Log invocation
            tool_invocations.append({
                 "task_id": t_id,
                 "tool": calls[idx].tool_name,
                 "success": success,
                 "persist": t_persist
            })

    # Summary Logging
    logger.info(f"\n📊 Parallel Research Summary:")
    logger.info(f"   Facts collected: {len(facts)}")
    logger.info(f"   Sources found: {len(sources)}")
    
    # ============================================================
    # RERANK FACTS BY RELEVANCE (Neural Reranking)
    # ============================================================
    if facts and len(facts) > 1:
        try:
            from shared.embedding.model_manager import get_reranker_provider
            from shared.config import get_settings
            
            query = state.get("query", "")
            reranker = get_reranker_provider()
            config = get_settings()
            
            # Extract text from facts for reranking
            fact_texts = [f.get("text", "")[:2000] for f in facts]
            
            # Use top_k from config
            # (Previously was hardware aware, now config driven, which can be hardware aware if we tune defaults)
            top_k = min(len(facts), config.reranker.per_task_top_k)
            
            logger.info(f"   🔄 Reranking {len(facts)} facts by relevance...")
            results = await reranker.rerank(query, fact_texts, top_k=top_k)
            
            # Reorder facts by reranker score
            reranked_facts = []
            for r in results:
                fact = facts[r.index].copy()
                fact["rerank_score"] = r.score
                reranked_facts.append(fact)
            
            facts = reranked_facts
            logger.info(f"   ✅ Reranked to top {len(facts)} facts")
            
        except Exception as e:
            logger.warning(f"   ⚠️ Reranking failed, using original order: {e}")
    
    logger.info("="*70 + "\n")
    
    return {
        **state,
        "facts": facts,
        "sources": sources,
        "tool_invocations": tool_invocations,
    }


@audited(AuditEventType.SECURITY_CHECK, "Keeper Node verified progress")
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


@audited(AuditEventType.QUERY_COMPLETED, "Synthesizer Node generated final report")
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


async def smart_fetch_data(args: dict) -> Any:
    # JIT-Enabled Data Fetcher
    query = args.get("query", "")
    
    # 1. AUTONOMOUS SEARCH: Find the data source URL first
    # We define a search query to find a list of companies
    discovery_query = f"list of companies listed on {query} stock exchange wikipedia"
    logger.info(f"🔍 Web Search for Data Source: '{discovery_query}'")
    
    wiki_url = "https://en.wikipedia.org/wiki/LQ45" # Default fallback
    try:
        search_args = {"query": discovery_query, "max_results": 3}
        # Use MCP Client for search
        mcp_client = get_mcp_orchestrator()
        search_results = await mcp_client.call_tool("web_search", search_args)
        
        # Simple heuristic to find a Wikipedia URL
        search_text = str(search_results)
        import re
        match = re.search(r'(https://[a-z]+\.wikipedia\.org/wiki/[^\s\)\"]+)', search_text)
        if match:
            wiki_url = match.group(0)
            logger.info(f"✅ Discovered Data Source: {wiki_url}")
        else:
            logger.warning(f"⚠️ Could not extract Wiki URL from search. Defaulting manually to LQ45 one.")
    except Exception as e:
        logger.error(f"❌ Discovery Search Failed: {e}")

    # 2. Dynamic Script Generation with DISCOVERED URL
    # NOTE: We use raw imports because we are running in a JIT 'uv' environment
    code = f"""
import pandas as pd
import yfinance as yf
import requests

def get_tickers():
    source_url = "{wiki_url}"
    print(f"🔍 Scraping tickers from discovered source: {{source_url}}")
    tickers = []
    
    try:
        # Robust Scrape
        import html5lib 
        tables = pd.read_html(source_url)
        
        # Smart Column Detection
        for df in tables:
            # Normalize cols
            cols = [str(c).upper() for c in df.columns]
            
            target_col = None
            for c in df.columns:
                c_up = str(c).upper()
                if "CODE" in c_up or "SYMBOL" in c_up or "TICKER" in c_up:
                    target_col = c
                    break
            
            if target_col:
                # Valid table found
                raw_tickers = df[target_col].tolist()
                suffix = ".JK" if "Indonesia" in "{query}" or "IDX" in "{query}" or "LQ45" in source_url else ""
                
                tickers = [f"{{str(t).strip()}}{{suffix}}" for t in raw_tickers if isinstance(t, str)]
                print(f"   ✅ Found {{len(tickers)}} tickers in table columns: {{df.columns.tolist()}}")
                break
                
        if not tickers:
            print("   ⚠️ No ticker column found in any table.")
            try:
                print("   🔄 Falling back to GitHub raw CSV...")
                url = "https://raw.githubusercontent.com/goapi-io/idx-companies/main/companies.csv"
                df_gh = pd.read_csv(url)
                tickers = [f"{{t}}.JK" for t in df_gh.iloc[:, 0].tolist()[:50]]
                print(f"   ✅ Discovered {{len(tickers)}} tickers from GitHub Fallback")
            except:
                pass
            
    except Exception as e:
        print(f"Discovery error: {{e}}")
        tickers = []
        
    return tickers

# Main Execution
try:
    targets = get_tickers()
    if not targets:
        print("No tickers found from source.")
    else:
        print(f"📊 Fetching data for {{len(targets)}} companies...")
        
        results = []
        for t in targets[:20]: 
            try:
                stock = yf.Ticker(t)
                info = stock.info
                results.append({{
                    "Ticker": t,
                    "Market Cap (IDR T)": round((info.get("marketCap", 0) or 0) / 1_000_000_000_000, 2),
                    "PE Ratio": round(info.get("trailingPE", 999) or 999, 2),
                    "Revenue Growth (%)": round((info.get("revenueGrowth", 0) or 0) * 100, 2),
                    "Sector": info.get("sector", "Unknown"),
                    "Price": info.get("currentPrice", 0)
                }})
                print(f"   ✅ Fetched {{t}}")
            except Exception as e:
                print(f"   ❌ Failed {{t}}: {{e}}")
                
        df = pd.DataFrame(results)
        print("\\nDATA_START")
        print(df.to_markdown(index=False))
        print("DATA_END")
        
except Exception as e:
    print(f"Script Error: {{e}}")
"""

    # Call execute_code_tool with JIT dependencies via MCP Client
    mcp_client = get_mcp_orchestrator()
    if not mcp_client:
        raise ValueError("MCP/Orchestrator not initialized")
        
    return await mcp_client.call_tool("execute_code", {
        "code": code, 
        "dependencies": ["yfinance", "pandas", "requests", "html5lib", "lxml", "tabulate"]
    })
