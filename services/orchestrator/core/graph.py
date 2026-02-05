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

# Data pool for bucket pattern (massive data collection)
from shared.data_pool import get_data_pool

# Node Assembly Engine for n8n-style node wiring
from services.orchestrator.core.assembler import ArtifactStore, NodeAssembler, create_assembler



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
    
    # Revision loop control (for Judge -> Generator retry)
    revision_count: int
    max_revisions: int


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
    
    # Initialize Node Assembly Engine for artifact-based data flow
    ctx = get_context_pool()
    assembler = create_assembler(ctx)
    
    # If no execution plan, fall back to sub-queries with web_search
    if not micro_tasks:
        logger.info("No execution plan, falling back to sub-query based web search")
        micro_tasks = [
            {"task_id": f"task_{i+1}", "description": sq, "tool": "web_search", 
             "inputs": {"query": sq}, "fallback_tools": ["news_search"], "persist": True}
            for i, sq in enumerate(sub_queries or [query])
        ]
    
    # =========================================================================
    # DAG Executor: Dependency-Driven Parallel Execution with Microplanner
    # =========================================================================
    # Replaces the old phase-based loop. Tasks now fire as soon as their
    # specific dependencies are satisfied, not when their entire phase completes.
    # The microplanner inspects results after each node and can inject new tasks.
    # =========================================================================
    if len(micro_tasks) >= 1:
        try:
            from services.orchestrator.core.agent_spawner import get_spawner
            from services.orchestrator.core.agent_spawner import (
                SubTask, SpawnPlan, TaskType, Domain
            )
            from services.orchestrator.core.prompt_factory import (
                PromptFactory, PromptContext
            )
            from services.orchestrator.core.workflow_nodes import (
                WorkflowNode, NodeType, NodeStatus, NodeResult,
                parse_blueprint,
            )
            from services.orchestrator.core.dag_executor import DAGExecutor
            from services.orchestrator.core.microplanner import Microplanner

            spawner = get_spawner()
            prompt_factory = PromptFactory()

            # Get complexity-aware limits
            complexity_info = state.get("complexity", {})
            max_parallel = complexity_info.get("max_parallel", 6)

            # Convert micro_tasks (dicts) into WorkflowNodes
            workflow_nodes = parse_blueprint(micro_tasks)

            logger.info(
                f"🧩 DAG Executor: {len(workflow_nodes)} nodes, "
                f"max_parallel={max_parallel}"
            )

            # Create node executor that bridges WorkflowNode → AgentSpawner
            async def execute_workflow_node(
                node: WorkflowNode,
                args: dict,
            ) -> NodeResult:
                """Execute a single workflow node via the agent spawner."""
                subtask = SubTask(
                    subtask_id=node.id,
                    query=node.description or f"{node.tool}: {str(args)[:100]}",
                    domain=Domain.RESEARCH,
                    task_type=TaskType.RESEARCH,
                    preferred_tool=node.tool,
                    arguments=args,
                )

                # Generate prompt with global context
                try:
                    ctx_pool = get_context_pool()
                    global_facts = [f.get("text", "") for f in ctx_pool.fact_pool]
                except Exception:
                    global_facts = []

                prompt_ctx = PromptContext(
                    query=subtask.query,
                    domain=subtask.domain,
                    task_type=subtask.task_type,
                    previous_findings=global_facts,
                )
                prompt = prompt_factory.generate(prompt_ctx)

                plan = SpawnPlan(
                    task_id=f"{state.get('job_id', 'node')}_{node.id}",
                    subtasks=[subtask],
                    prompts=[prompt],
                    max_parallel=1,
                )

                swarm_result = await spawner.execute_swarm(plan)

                # Convert SwarmResult → NodeResult
                if swarm_result.successful > 0:
                    agent_res = next(
                        (r for r in swarm_result.agent_results
                         if r.status == "completed"),
                        None,
                    )
                    output = agent_res.result if agent_res else None

                    # Store in context pool for downstream nodes
                    try:
                        ctx_pool = get_context_pool()
                        ctx_pool.store_data(
                            key=f"task_output_{node.id}",
                            data=str(output),
                            description=f"Output from node {node.id}",
                        )
                        ctx_pool.add_fact(
                            text=str(output),
                            source=f"task_{node.id}",
                            task_id=node.id,
                        )
                    except Exception as e:
                        logger.warning(f"Context pool update failed: {e}")

                    return NodeResult(
                        node_id=node.id,
                        status=NodeStatus.COMPLETED,
                        output=output,
                        artifacts={node.output_artifact: str(output)} if node.output_artifact else {},
                        metadata={
                            "source": agent_res.source if agent_res else None,
                            "prompt": agent_res.prompt_used[:200] if agent_res else "",
                        },
                    )
                else:
                    error_msg = "; ".join(
                        r.error or "unknown"
                        for r in swarm_result.agent_results
                        if r.status != "completed"
                    )
                    return NodeResult(
                        node_id=node.id,
                        status=NodeStatus.FAILED,
                        error=error_msg or "All agents failed",
                    )

            # Initialize microplanner for reactive replanning
            microplanner = Microplanner(
                query=query,
                llm_callback=spawner.llm_callback,
                max_replans=complexity_info.get("max_research_iterations", 3),
            )

            # Create and run DAG executor
            dag_executor = DAGExecutor(
                store=assembler.store,
                node_executor=execute_workflow_node,
                max_parallel=max_parallel,
                microplanner=microplanner.checkpoint,
            )

            dag_result = await dag_executor.execute(workflow_nodes)

            # Harvest results into facts/sources/tool_invocations
            for node_id, node_result in dag_result.node_results.items():
                if node_result.status == NodeStatus.COMPLETED and node_result.output:
                    facts.append({
                        "text": str(node_result.output),
                        "query": f"DAG Node {node_id}",
                        "source": node_result.metadata.get("source", "dag_executor"),
                        "task_id": node_id,
                        "persist": True,
                    })

                tool_invocations.append({
                    "task_id": node_id,
                    "tool": "dag_executor",
                    "success": node_result.status == NodeStatus.COMPLETED,
                    "persist": True,
                })

            logger.info(
                f"✅ DAG complete: {dag_result.completed} ok, "
                f"{dag_result.failed} failed, {dag_result.skipped} skipped, "
                f"{dag_result.replans_triggered} replans"
            )
            micro_tasks = []  # Clear standard loop queue

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
    
    from services.orchestrator.core.utils import build_tool_inputs


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
            
            # SMART CODE GENERATION INTERCEPTOR
            if t_name in ["run_python", "execute_code", "parse_document"] and "code" not in t_inputs:
                try:
                    from services.orchestrator.agents.code_generator import generate_python_code
                    ctx = get_context_pool()
                    files = ctx.list_files()
                    
                    logger.info(f"   🤖 Generating Smart Code for '{t_desc}' (Context: {len(facts)} facts, {len(files)} files)")
                    generated_code = await generate_python_code(t_desc, facts, file_artifacts=files)
                    
                    if generated_code:
                        t_inputs["code"] = generated_code
                        # Skip standard build_tool_inputs since we handled it
                        final_inputs = t_inputs
                    else:
                        final_inputs = build_tool_inputs(t_name, t_desc, t_inputs, facts)
                except Exception as e:
                    logger.warning(f"Smart Code Generation failed: {e}, falling back")
                    final_inputs = build_tool_inputs(t_name, t_desc, t_inputs, facts)
            else:
                final_inputs = build_tool_inputs(t_name, t_desc, t_inputs, facts)
            
            # Handle input build failure (fallback immediately or skip)
            if final_inputs is None:
                # Try fallback
                fallback_tools = task.get("fallback_tools") or ["web_search"]
                t_name = fallback_tools[0]
                
                # Attempt to build inputs for fallback tool
                final_inputs = build_tool_inputs(t_name, t_desc, t_inputs, facts)
                
                if final_inputs is None:
                    # Ultimate fallback to web_search with hardware-aware limit
                    from shared.hardware.detector import detect_hardware
                    t_name = "web_search"
                    final_inputs = {"query": t_desc, "max_results": detect_hardware().optimal_search_limit()}
            
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
                
                # Strict Error Filtering (Prevent "Error is a Fact")
                if "tool not found" in content_text.lower() or "error:" in content_text.lower() or "exception" in content_text.lower():
                    success = False # Mark as failed logically even if technically successful execution
                    error_msg = content_text
                elif len(content_text) < 5:
                    success = False
                    error_msg = "Content too short"

            if success:
                # Extract Facts
                fact = {
                    "text": content_text,  # No truncation - store full content
                    "query": task.get("description", ""),  # No truncation
                    "source": calls[idx].tool_name,
                    "task_id": t_id,
                    "persist": t_persist
                }
                facts.append(fact)
                
                # Extract Sources
                ctx = get_context_pool()
                extracted_urls = ctx.extract_urls_from_text(content_text)
                
                # FALLBACK: If no URLs found in text, check input arguments!
                if not extracted_urls and "url" in calls[idx].arguments:
                    url_arg = calls[idx].arguments["url"]
                    if isinstance(url_arg, str) and url_arg.startswith("http"):
                        extracted_urls.append(url_arg)
                        
                for url in extracted_urls:  # No limit - extract all URLs
                    sources.append({
                        "url": url,
                        "title": task.get("description", ""),  # No truncation
                        "tool": calls[idx].tool_name,
                        "task_id": t_id
                    })
                
                # Store in DataPool for bucket pattern
                try:
                    data_pool = get_data_pool()
                    await data_pool.create_pool_item(
                        pool_id=state.get("job_id", "default"),
                        metadata={
                            "fact_text": content_text[:5000],  # Summary for metadata
                            "source": calls[idx].tool_name,
                            "task_id": t_id,
                            "query": task.get("description", ""),
                        },
                        status="raw"
                    )
                except Exception as e:
                    logger.debug(f"DataPool storage skipped: {e}")

                # ARTIFACT HARVESTING (NEW): Scan for file paths
                import re
                file_matches = re.findall(r'[\w\-\._\/]+\.(?:csv|parquet|xlsx|json)', content_text)
                for fpath in file_matches:
                    fpath = fpath.strip()
                    if len(fpath) > 4: 
                         ctx.store_file(t_id, fpath)
                         logger.info(f"   📂 Harvested artifact: {fpath}")
                
                completed.add(t_id)
                logger.info(f"   ✅ Task {t_id} completed via {calls[idx].tool_name}")
                
                # VERBOSE CODE OUTPUT
                if calls[idx].tool_name in ["execute_code", "run_python"]:
                     logger.info(f"   🐍 EXECUTION OUTPUT:\n{'-'*60}\n{content_text.strip()}\n{'-'*60}")
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
            
            # GPU MEMORY SAFETY (User Request)
            try:
                import torch
                import gc
                gc.collect()
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            except ImportError:
                pass
            
            # Extract text from facts for reranking
            fact_texts = [f.get("text", "")[:2000] for f in facts]
            
            # Use top_k from config
            # (Previously was hardware aware, now config driven, which can be hardware aware if we tune defaults)
            top_k = min(len(facts), config.reranker.per_task_top_k)
            
            logger.info(f"   🔄 Reranking {len(facts)} facts by relevance to query...")
            logger.debug(f"   🔍 Reranker Query: {query[:100]}...")
            logger.debug(f"   🔍 Reranker Sample Fact: {fact_texts[0][:100]}...")
            
            try:
                results = await reranker.rerank(query, fact_texts, top_k=top_k)
                if results:
                    logger.info(f"   ✅ Top Score: {results[0].score:.4f}, Bottom Score: {results[-1].score:.4f}")
                else:
                    logger.warning("   ⚠️ Reranker returned no results")
            except Exception as e:
                # OOM CHECK & RECOVERY
                is_oom = "out of memory" in str(e).lower()
                if is_oom:
                     import torch
                     import gc
                     from shared.embedding.model_manager import switch_reranker_device
                     
                     logger.warning(f"⚠️ CUDA OOM detected during reranking. Initiating failover...")
                     
                     # Clear cache immediately
                     gc.collect()
                     if torch.cuda.is_available():
                        torch.cuda.empty_cache()
                     
                     # Determine next device
                     new_device = "cpu"
                     if torch.cuda.is_available() and torch.cuda.device_count() > 1:
                         # Try next GPU
                         current_device = getattr(reranker, "device", "cuda:0")
                         if isinstance(current_device, str) and ":" in current_device:
                             try:
                                 curr_idx = int(current_device.split(":")[-1])
                                 new_idx = (curr_idx + 1) % torch.cuda.device_count()
                                 # Prevent cycling back to same OOM device immediately if count > 1
                                 if new_idx != curr_idx:
                                     new_device = f"cuda:{new_idx}"
                             except:
                                 pass
                     
                     logger.warning(f"   🔄 Switching reranker to {new_device} and retrying operation...")
                     
                     # Switch device
                     switch_reranker_device(new_device)
                     
                     # Retry execution
                     results = await reranker.rerank(query, fact_texts, top_k=top_k)
                     logger.info(f"   ✅ Retry successful on {new_device}")
                else:
                    raise e
            finally:
                # Cleanup after heavy operation
                try:
                    import torch
                    import gc
                    gc.collect()
                    if torch.cuda.is_available():
                        torch.cuda.empty_cache()
                except: 
                    pass
            
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
    from shared.config import get_settings
    config = get_settings()
    
    iteration = state.get("iteration", 0)
    # Use config for max depth
    max_iterations = state.get("max_iterations", config.research.max_depth)
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
    
    # Increment revision count if verdict is Revise
    revision_count = state.get("revision_count", 0)
    if verdict == "Revise":
        revision_count += 1
        logger.info(f"🔄 Revision requested. Count: {revision_count}")
    
    return {
        **state,
        "judge_verdict": verdict,
        "confidence": confidence,
        "revision_count": revision_count,
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


def should_revise_or_finalize(state: GraphState) -> Literal["generator", "synthesizer"]:
    """
    Decide whether to revise the answer or finalize.
    
    If Judge verdict is 'Revise' and we haven't exceeded max_revisions,
    loop back to Generator for another attempt.
    """
    verdict = state.get("judge_verdict", "Accept")
    revision_count = state.get("revision_count", 0)
    max_revisions = state.get("max_revisions", 2)  # Default: allow 2 retries
    
    if verdict == "Revise" and revision_count < max_revisions:
        logger.info(f"🔄 Judge requested revision. Attempt {revision_count + 1}/{max_revisions}")
        return "generator"
    
    return "synthesizer"


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
    
    # Conditional edge: Judge can request revision or finalize
    graph.add_conditional_edges(
        NodeName.JUDGE.value,
        should_revise_or_finalize,
        {
            "generator": NodeName.GENERATOR.value,  # Loop back for revision
            "synthesizer": NodeName.SYNTHESIZER.value,  # Proceed to final
        }
    )
    
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
        from shared.hardware.detector import detect_hardware
        search_args = {"query": discovery_query, "max_results": detect_hardware().optimal_search_limit()}
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


# ============================================================================
# Agentic Workflow Runner (Autonomous Human-Like Execution)
# ============================================================================

async def run_agentic_research(
    query: str,
    job_id: str | None = None,
    max_steps: int = 15
) -> dict[str, Any]:
    """
    Run autonomous research using the agentic workflow.
    
    This is an alternative to the standard LangGraph flow that uses
    a ReAct-style loop where the LLM reasons about each step,
    similar to how a human analyst would work.
    
    The agent will:
    1. Analyze the query
    2. Call appropriate tools to gather data
    3. Inspect results and decide next steps
    4. Synthesize findings when complete
    
    Args:
        query: User's research query
        job_id: Optional job ID for tracking
        max_steps: Maximum reasoning steps (default 15)
        
    Returns:
        Dict with final_answer, reasoning_steps, tool_executions, artifacts
        
    Example:
        result = await run_agentic_research("Analyze TSLA financials")
        print(result["final_answer"])
        print(f"Completed in {len(result['reasoning_steps'])} steps")
    """
    from services.orchestrator.core.agentic_workflow import AgenticWorkflow
    from services.mcp_host.core.session_registry import get_session_registry
    
    logger.info("=" * 70)
    logger.info("🤖 AGENTIC WORKFLOW MODE - Human-Like Autonomous Research")
    logger.info("=" * 70)
    logger.info(f"Query: {query[:200]}")
    logger.info("-" * 70)
    
    registry = get_session_registry()
    
    async def tool_executor(name: str, args: dict) -> Any:
        """Execute tools via MCP session registry."""
        # Handle full names like "yfinance_server.get_income_statement_quarterly"
        if "." in name:
            server_name, tool_name = name.rsplit(".", 1)
        else:
            tool_name = name
            server_name = registry.get_server_for_tool(name)
            if not server_name:
                raise ValueError(f"Tool {name} not found in registry")
        
        session = await registry.get_session(server_name)
        result = await session.call_tool(tool_name, args)
        
        # Extract text content from result
        if hasattr(result, "content"):
            text_parts = []
            for c in result.content:
                if hasattr(c, "text"):
                    text_parts.append(c.text)
            return "\n".join(text_parts)
        
        return str(result)
    
    # Discover available tools
    await registry.list_all_tools()
    all_tools = registry.get_all_tools_list()
    
    # Filter to relevant tools for financial analysis
    relevant_prefixes = ["yfinance", "python", "execute", "web_search", "news"]
    available_tools = [
        {"name": t.get("name", ""), "description": t.get("description", "")}
        for t in all_tools
        if any(p in t.get("name", "").lower() for p in relevant_prefixes)
    ][:50]  # Limit to 50 tools for context
    
    logger.info(f"📚 Discovered {len(available_tools)} relevant tools")
    
    # Run the agentic workflow
    workflow = AgenticWorkflow(
        tool_executor=tool_executor,
        max_steps=max_steps
    )
    
    state = await workflow.run(
        query=query,
        available_tools=available_tools
    )
    
    # Log summary
    logger.info("=" * 70)
    logger.info("✅ AGENTIC WORKFLOW COMPLETE")
    logger.info("=" * 70)
    logger.info(f"Status: {state.status}")
    logger.info(f"Steps: {state.current_step}")
    logger.info(f"Tools Called: {len(state.tool_executions)}")
    logger.info(f"Schemas Learned: {len(state.learned_schemas)}")
    
    return {
        "final_answer": state.final_answer,
        "status": state.status,
        "reasoning_steps": state.reasoning_steps,
        "tool_executions": state.tool_executions,
        "artifacts": state.artifacts,
        "learned_schemas": state.learned_schemas,
        "query": query,
        "job_id": job_id
    }

