"""
LangGraph Research State Machine.

Implements the cyclic research flow with checkpointing.
This is the PRODUCTION version that uses real LLM and MCP implementations.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any, Literal, TypedDict

from langgraph.graph import END, StateGraph

from kernel.agents.critic import CriticAgent
from kernel.agents.generator import GeneratorAgent
from kernel.agents.judge import JudgeAgent

# Node Assembly Engine for n8n-style node wiring
from kernel.core.assembler import create_assembler
from kernel.flow.router import IntentionRouter
from kernel.nodes.keeper import keeper_node as real_keeper_node

# Import real implementations
from kernel.nodes.planner import planner_node as real_planner_node
from shared.audit import AuditEventType, audited

# NEW: Context pool and code generator for dynamic data flow
from shared.context_pool import get_context_pool, reset_context_pool

# Data pool for bucket pattern (massive data collection)
from shared.data_pool import get_data_pool
from shared.logging import get_logger
from shared.prompts import get_agent_prompt, get_kernel_config, get_report_template
from shared.vocab import load_vocab as _load_vocab

# ---------------------------------------------------------------------------
# Module-level config constants (loaded once, cached via @cache in prompts.py)
# ---------------------------------------------------------------------------
_VOCAB = _load_vocab("classification")
_VOCAB_PLANNER = _load_vocab("planner")
_STANDARD_ERRORS: list[str] = _VOCAB.get("error_keywords", {}).get("standard", [])
_QUICK_ERRORS: list[str] = _VOCAB.get("error_keywords", {}).get("quick_filter", [])
_CODE_TOOLS: list[str] = _VOCAB.get("tool_categories", {}).get("code_execution", [])
_TOOL_ALIASES: dict = _VOCAB_PLANNER.get("aliases", {})
_AGENTIC_PREFIXES: list[str] = _VOCAB.get("agentic_tool_prefixes", [])

_MIN_LEN: int = get_kernel_config("execution.min_valid_output_length") or 5
_MAX_REVISIONS_DEFAULT: int = get_kernel_config("defaults.max_revisions") or 2
_FALLBACK_TOOL: str = get_kernel_config("defaults.fallback_tool") or "web_search"
_MAX_TOOLS: int = get_kernel_config("execution.max_agentic_tools") or 50
_REPORT_MAX_FACTS: int = get_kernel_config("execution.report_max_facts") or 10
_REPORT_MAX_INV: int = get_kernel_config("execution.report_max_invocations") or 25
_REPORT_MAX_SRC: int = get_kernel_config("execution.report_max_sources_fallback") or 10
_CITE_PREVIEW: int = get_kernel_config("execution.citation_preview_length") or 500

logger = get_logger(__name__)


# ============================================================================
# Node Names
# ============================================================================


class NodeName(StrEnum):
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

    # Error Feedback Loop (Self-Correction)
    # Stores errors from failed tool calls to inject into LLM for learning
    error_feedback: list[dict]  # [{"tool": str, "error": str, "args": dict, "suggestion": str}]

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
    stop_reason: str  # Reason for stopping (confidence_achieved, all_tools_failed, etc.)

    # Revision loop control (for Judge -> Generator retry)
    revision_count: int
    max_revisions: int

    # Replan loop control (for Keeper -> Planner retry when all tools fail)
    replan_count: int

    # Deduplication (skip repeated tool calls)
    completed_calls: set  # Set of call hashes: hash(tool_name + json(args))


# ============================================================================
# Node Implementations (VERBOSE MODE)
# ============================================================================


async def router_node(state: GraphState) -> GraphState:
    """Route query to appropriate execution path with Memory & Intent."""
    query = state.get("query", "")
    job_id = state.get("job_id", "unknown_session")

    logger.info("\n" + "=" * 70)
    logger.info("  STEP 1: ROUTER NODE (Memory Aware)")
    logger.info("=" * 70)
    logger.info(f"Query: {query[:200]}...")

    # =========================================================================
    # Phase 2: Memory & Intent Integration
    # =========================================================================
    from kernel.memory.conversation import Intent, get_conversation_manager

    mem_mgr = get_conversation_manager()

    # We use job_id as session_id for now for simplicity
    # In a real app, session_id would be distinct from job_id
    resp = await mem_mgr.process(session_id=job_id, message=query)

    logger.info(f"  Intent Detected: {resp.intent.value.upper()}")

    context_str = ""
    if resp.intent == Intent.FOLLOW_UP:
        context_str = resp.context
        logger.info(f"  Retrieved Context ({len(context_str)} chars)")
        # Inject context into query for the Planner to see
        # We append it so the Planner knows what "it" refers to
        state["query"] = f"{query}\n\n[CONTEXT FROM MEMORY]:\n{context_str}"

    elif resp.intent == Intent.NEW_TOPIC:
        logger.info("  New Topic Detected - Clearing localized context")
        # No context injection

    # =========================================================================

    router = IntentionRouter()
    context = {
        "prior_research": state.get("prior_research"),
        "data_to_verify": state.get("data_to_verify"),
        "memory_context": context_str,
    }

    path = await router.route(query, context)

    logger.info(f"  Selected Path: {path}")
    logger.info("   A = Memory Fork | B = Shadow Lab | C = Grand Synthesis | D = Deep Research")
    logger.info("=" * 70 + "\n")

    return {
        **state,
        "path": path,
        "status": "running",
    }


@audited(AuditEventType.QUERY_CLASSIFIED, "Planner Node decomposed query")
async def planner_node(state: GraphState) -> GraphState:
    """Decompose query into sub-queries, hypotheses, and execution plan using real LLM."""
    logger.info("\n" + "=" * 70)
    logger.info("  STEP 2: PLANNER NODE (LLM Call)")
    logger.info("=" * 70)
    logger.info(f"Query: {state.get('query', '')[:200]}...")
    logger.info("-" * 70)
    logger.info("Calling LLM to decompose query into sub-queries and execution plan...")

    # Call real planner that uses OpenRouter LLM
    updated_state = await real_planner_node(dict(state))

    sub_queries = updated_state.get("sub_queries", [])
    hypotheses = updated_state.get("hypotheses", [])
    execution_plan = updated_state.get("execution_plan", {})

    logger.info(f"\n  Sub-Queries Generated ({len(sub_queries)}):")
    for i, sq in enumerate(sub_queries, 1):
        logger.info(f"   {i}. {sq}")

    logger.info(f"\n  Hypotheses Generated ({len(hypotheses)}):")
    for i, h in enumerate(hypotheses, 1):
        logger.info(f"   {i}. {h}")

    # Log execution plan
    micro_tasks = execution_plan.get("micro_tasks", [])
    if micro_tasks:
        logger.info(f"\n  Execution Plan Generated ({len(micro_tasks)} micro-tasks):")
        for task in micro_tasks:
            logger.info(
                f"   [{task.get('task_id')}] {task.get('tool')}: {task.get('description', '')[:60]}..."
            )
        logger.info(f"   Phases: {execution_plan.get('phases', [])}")

    logger.info("=" * 70 + "\n")

    # Increment iteration
    updated_state["iteration"] = state.get("iteration", 0) + 1

    return {**state, **updated_state}


@audited(AuditEventType.TOOL_CALLED, "Researcher Node executed iteration")
async def _llm_correct_tool_parameters(
    query: str, task_description: str, tool_name: str, failed_arguments: dict, error_message: str
) -> dict | None:
    """
    Use LLM to intelligently correct tool parameters after failure.

    Args:
        query: Original user query
        task_description: Specific task description
        tool_name: Tool that failed
        failed_arguments: Arguments that caused failure
        error_message: Error message from failed execution

    Returns:
        Corrected arguments dict, or None if can't correct
    """
    try:
        import os

        if not os.getenv("OPENROUTER_API_KEY"):
            return None

        import json

        from shared.config import get_settings
        from shared.llm import LLMConfig, OpenRouterProvider
        from shared.llm.provider import LLMMessage, LLMRole

        provider = OpenRouterProvider()
        config = LLMConfig(
            model=get_settings().models.planner_model,
            temperature=0.3,
            max_tokens=32768,  # Max out for comprehensive parameter correction
        )

        # Get tool schema for intelligent correction
        tool_schema_info = ""
        try:
            from kernel.interfaces.tool_registry import get_tool_registry
            registry = get_tool_registry()
            all_tools = await registry.list_tools()

            # Find this tool's schema
            for tool in all_tools:
                if tool.get("name") == tool_name:
                    schema = tool.get("inputSchema", {})
                    if schema:
                        tool_schema_info = f"\n**Tool Schema:** {json.dumps(schema, indent=2)}"
                    break
        except Exception:
            pass

        messages = [
            LLMMessage(
                role=LLMRole.SYSTEM,
                content=get_agent_prompt("parameter_corrector"),
            ),
            LLMMessage(
                role=LLMRole.USER,
                content=f"""A tool execution failed. Analyze and suggest parameter corrections:

**User Query:** {query}
**Task Description:** {task_description}
**Tool Name:** {tool_name}
**Arguments That Failed:** {json.dumps(failed_arguments, indent=2)}
**Error Message:** {error_message}{tool_schema_info}

Based on the error, what are the CORRECT parameters?
Return JSON only, matching the parameter names from failed arguments.""",
            ),
        ]

        response = await provider.complete(messages, config)
        content = response.content.strip()

        # Extract JSON from response
        import re

        json_match = re.search(r"\{[^}]+\}", content)
        if json_match:
            corrected = json.loads(json_match.group(0))
            if corrected:  # Non-empty dict
                return corrected

        return None

    except Exception as e:
        logger.error(f"LLM parameter correction failed: {e}")
        return None


def _build_tool_citation(
    tool_name: str,
    server_name: str,
    arguments: dict,
    result_preview: str,
    duration_ms: float = 0.0,
    is_error: bool = False,
    invoked_at: datetime | None = None,
    source_url: str = "",
) -> dict:
    """
    Build a ToolCitation dict from a completed tool call.

    The call record IS the citation   no URL derivation from tool name.
    source_url is only populated when a URL is genuinely present in the tool output.
    Works uniformly for all 68+ MCP servers.
    """
    return {
        "tool_name": tool_name,
        "server_name": server_name,
        "arguments": arguments,
        "result_preview": result_preview[:500],
        "is_error": is_error,
        "duration_ms": round(duration_ms, 2),
        "invoked_at": (invoked_at or datetime.utcnow()).isoformat(),
        "source_url": source_url,
    }


async def researcher_node(state: GraphState) -> GraphState:
    """Execute research using execution plan with dynamic tool routing and PARALLEL execution."""
    iteration = state.get("iteration", 1)

    logger.info("\n" + "=" * 70)
    logger.info(f"  STEP 3: RESEARCHER NODE (Iteration {iteration}) - Parallel Tool Execution")
    logger.info("=" * 70)

    execution_plan = state.get("execution_plan", {})
    micro_tasks = execution_plan.get("micro_tasks", [])
    sub_queries = state.get("sub_queries", [])
    query = state.get("query", "")
    facts = state.get("facts", [])
    sources = state.get("sources", [])
    tool_invocations = state.get("tool_invocations", [])
    error_feedback = state.get("error_feedback", [])  # Error feedback for LLM self-correction
    completed_calls = state.get("completed_calls", set())  # Deduplication: skip repeated calls

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
            {
                "task_id": f"task_{i + 1}",
                "description": sq,
                "tool": "web_search",
                "inputs": {"query": sq},
                "fallback_tools": ["news_search"],
                "persist": True,
                "output_artifact": f"search_result_{i + 1}",
            }
            for i, sq in enumerate(sub_queries or [query])
        ]

    # =========================================================================
    # =========================================================================
    # DAG Executor: Dependency-Driven Parallel Execution via SwarmExecutor
    # =========================================================================
    # Logic extracted to kernel.cognition.swarm_executor for modularity.
    # =========================================================================
    if len(micro_tasks) >= 1:
        try:
            from kernel.cognition.swarm_executor import SwarmExecutor

            swarm_exec = SwarmExecutor(job_id=state.get("job_id", "unknown"))
            
            (
                dag_result, 
                new_facts, 
                new_sources, 
                new_invocations, 
                new_errors
            ) = await swarm_exec.execute(micro_tasks, state, assembler)

            # Merge results
            facts.extend(new_facts)
            for s in new_sources:
                if s["url"] not in [exist.get("url") for exist in sources]:
                    sources.append(s)
            tool_invocations.extend(new_invocations)
            error_feedback.extend(new_errors)

            logger.info(
                f"  DAG complete: {dag_result.completed} ok, "
                f"{dag_result.failed} failed, {dag_result.skipped} skipped, "
                f"{dag_result.replans_triggered} replans"
            )
            micro_tasks = []  # Clear so legacy loop is skipped

        except ImportError as e:
            logger.warning(
                f"  SwarmExecutor unavailable ({e}), falling back to legacy phase-based executor"
            )
        except Exception as e:
            logger.error(f"  SwarmExecutor failed ({e}), falling back to legacy executor")

    # =========================================================================
    # Legacy Phase-Based Executor (fallback when DAG executor is unavailable)
    # Only runs if micro_tasks is non-empty (DAG executor clears it on success)
    # =========================================================================
    if micro_tasks:
        # 1. Hardware-Aware Scaling
        from kernel.actions.parallel_executor import ParallelExecutor, ToolCall
        from kernel.interfaces.tool_registry import get_tool_registry
        from shared.hardware.detector import detect_hardware

        hw_profile = detect_hardware()
        max_workers = hw_profile.optimal_workers()
        logger.info(
            f"  Legacy Executor: Using {max_workers} parallel workers (RAM: {hw_profile.ram_available_gb:.1f}GB)"
        )

        executor = ParallelExecutor(max_concurrent=max_workers)
        registry = get_tool_registry()

        from kernel.utils import build_tool_inputs

        # 2. Unified Tool Handler with Intelligent Retry (INTELLIGENCE INJECTED)
        async def unified_tool_handler(name: str, args: dict) -> Any:
            """
            Execute tool with intelligent retry on parameter errors.
            Used by both DAG executor and legacy executor.
            """
            nonlocal completed_calls  # Access outer variable

            # ============================================================
            # DEDUPLICATION: Skip repeated tool calls with same args
            # ============================================================
            import hashlib
            import json as json_mod

            # Create deterministic hash of tool call
            args_str = json_mod.dumps(args, sort_keys=True, default=str)
            call_hash = hashlib.md5(f"{name}:{args_str}".encode()).hexdigest()

            if call_hash in completed_calls:
                logger.info(f"  DEDUP: Skipping duplicate call: {name}({list(args.keys())})")
                # Return cached result from context pool if available
                cached_key = f"cache_{name}_{call_hash[:8]}"
                cached_result = ctx.get_data(cached_key)
                if cached_result:
                    logger.info(f"     Using cached result from {cached_key}")
                    return cached_result
                # If no cache, still skip but return a marker
                return f"[Duplicate call skipped: {name}]"

            # Mark as in-progress (add to set)
            completed_calls.add(call_hash)

            # Resolve target server dynamically
            server_name = registry.get_server_for_tool(name)

            if not server_name:
                # Fallback Mapping (from configs/vocab/classification.yaml tool_aliases)
                mapped = _TOOL_ALIASES.get(name)
                if mapped:
                    server_name = registry.get_server_for_tool(mapped)
                    if server_name:
                        logger.info(f"  Mapped {name} -> {mapped} on {server_name}")
                        name = mapped  # Switch to actual tool name

            if not server_name:
                # Try JIT Discovery
                await registry.list_all_tools()
                server_name = registry.get_server_for_tool(name)

            if not server_name:
                raise ValueError(f"Tool {name} not found in SessionRegistry.")

            # Execute with intelligent retry loop
            result = None
            retry_count = 0

            # Hardware-aware retry limit (more retries for free APIs with high quotas)
            # Free tier: 1000/day = plenty of budget for retries
            # With 4+ cores, can handle 5-8 retries efficiently
            try:
                from shared.hardware.detector import detect_hardware

                hw = detect_hardware()
                # Scale retries with CPU cores: more cores = can handle more retries in parallel
                max_retries = min(8, max(3, hw.cpu_count // 2))  # 3-8 retries based on CPU
            except Exception:
                max_retries = 5  # Default to 5 retries (was 2)

            current_args = args.copy()

            while retry_count <= max_retries:
                try:
                    session = await registry.get_session(server_name)
                    result = await session.call_tool(name, current_args)

                    # Generic error detection (works for any tool/domain)
                    error_detected = False
                    if result and hasattr(result, "content"):
                        content_text = ""
                        for c in result.content:
                            if hasattr(c, "text"):
                                content_text += c.text

                        # Check if output looks like an error (keywords from classification.yaml)
                        lower_text = content_text.lower()
                        for error_term in _STANDARD_ERRORS:
                            if error_term in lower_text:
                                # Additional check: Is this a substantial error or just mention?
                                # Real errors are usually short and contain error term early
                                if (
                                    len(content_text.strip()) < 200
                                    or lower_text.find(error_term) < 100
                                ):
                                    error_detected = True
                                    break

                        # If error and we have retries left, attempt correction
                        if error_detected and retry_count < max_retries:
                            retry_count += 1
                            logger.warning(
                                f"  Tool {name} returned error. "
                                f"Attempting LLM correction (retry {retry_count}/{max_retries})"
                            )

                            # Use LLM to correct parameters
                            corrected_args = await _llm_correct_tool_parameters(
                                query=state.get("query", ""),
                                task_description=f"Execute {name}",
                                tool_name=name,
                                failed_arguments=current_args,
                                error_message=content_text[:500],
                            )

                            if corrected_args:
                                logger.info(f"  LLM corrected arguments: {corrected_args}")
                                current_args = corrected_args
                                # Loop will retry with corrected args
                            else:
                                logger.warning(
                                    "  LLM couldn't suggest correction, returning error result"
                                )
                                break  # No correction possible, return error result
                        else:
                            # No error or no retries left
                            break
                    else:
                        # No content to check, return as-is
                        break

                except Exception as e:
                    logger.error(f"Tool execution failed: {e}")
                    if retry_count < max_retries:
                        retry_count += 1
                        logger.warning(
                            f"  Retrying after exception (retry {retry_count}/{max_retries})"
                        )
                    else:
                        raise ValueError(f"Tool {name} failed after {max_retries} retries: {e}")

            # AUTONOMIC MEMORY INTERCEPTOR
            try:
                from kernel.flow.interceptor import MemoryInterceptor

                job_id = state.get("job_id", "unknown_trace")
                await MemoryInterceptor.intercept(
                    trace_id=job_id,
                    source_node=name,
                    result=result,
                    inputs=current_args,  # Use final args (may be corrected)
                )
            except Exception as e:
                logger.warning(f"Interceptor failed (non-blocking): {e}")

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
            batch = ready_tasks[: max_workers * 2]
            processed_this_run.update(t.get("task_id") for t in batch)

            logger.info(f"\n  Batching {len(batch)} tasks...")

            # Prepare calls
            calls = []
            task_map = {}  # index -> task

            for idx, task in enumerate(batch):
                t_name = task.get("tool", "web_search")
                t_desc = task.get("description", "")
                t_inputs = task.get("inputs", {})
                t_id = task.get("task_id")

                # SMART CODE GENERATION INTERCEPTOR
                if t_name in _CODE_TOOLS and "code" not in t_inputs:
                    try:
                        from kernel.agents.code_generator import generate_python_code

                        ctx = get_context_pool()
                        files = ctx.list_files()

                        logger.info(
                            f"     Generating Smart Code for '{t_desc}' (Context: {len(facts)} facts, {len(files)} files)"
                        )
                        generated_code = await generate_python_code(
                            t_desc, facts, file_artifacts=files
                        )

                        if generated_code:
                            t_inputs["code"] = generated_code
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
                    fallback_tools = task.get("fallback_tools") or ["web_search"]
                    t_name = fallback_tools[0]
                    final_inputs = build_tool_inputs(t_name, t_desc, t_inputs, facts)

                    if final_inputs is None:
                        from shared.hardware.detector import detect_hardware

                        t_name = _FALLBACK_TOOL
                        final_inputs = {
                            "query": t_desc,
                            "max_results": detect_hardware().optimal_search_limit(),
                        }

                calls.append(ToolCall(tool_name=t_name, arguments=final_inputs))
                task_map[idx] = task

            # COMPLIANCE GATE   filter out calls that fail before execution
            from kernel.logic.guardrails import check_tool_call as _check_tool

            _compliant_calls: list[ToolCall] = []
            _compliant_task_map: dict[int, dict] = {}
            for _ci, (_call, _task) in enumerate(
                zip(calls, [task_map[i] for i in range(len(calls))])
            ):
                _violations = await _check_tool(_call.tool_name, _call.arguments)
                if _violations:
                    _t_id = _task.get("task_id", "unknown")
                    logger.warning(
                        f"  GUARDRAIL: Blocked {_call.tool_name} for task {_t_id} "
                        f"  {_violations[0]['message']}"
                    )
                    error_feedback.append(
                        {
                            "tool": _call.tool_name,
                            "task_id": _t_id,
                            "error": f"Compliance violation: {_violations[0]['message']}",
                            "args": _call.arguments,
                            "description": _task.get("description", ""),
                        }
                    )
                    completed.add(_t_id)
                else:
                    _new_idx = len(_compliant_calls)
                    _compliant_calls.append(_call)
                    _compliant_task_map[_new_idx] = _task

            calls = _compliant_calls
            task_map = _compliant_task_map

            if not calls:
                logger.info("All batch calls blocked by compliance gate   skipping execution")
                continue

            # EXECUTE BATCH
            results = await executor.execute_batch(calls, unified_tool_handler)

            # Process results
            for idx, res in enumerate(results):
                task = task_map[idx]
                t_id = task.get("task_id")
                t_persist = task.get("persist", True)

                success = res.success
                content_text = ""

                if success and res.result and hasattr(res.result, "content"):
                    for c in res.result.content:
                        if hasattr(c, "text"):
                            content_text += c.text

                    # Strict Error Filtering (Prevent "Error is a Fact")
                    # Note: Retry logic is now in unified_tool_handler, not here
                    for keyword in _QUICK_ERRORS:
                        if keyword in content_text.lower():
                            success = False
                            break

                    if len(content_text) < _MIN_LEN:
                        success = False

                # Build citation unconditionally   covers both success and failure paths
                _legacy_citation = _build_tool_citation(
                    tool_name=calls[idx].tool_name or "unknown_tool",
                    server_name="mcp_host",
                    arguments=calls[idx].arguments or {},
                    result_preview=content_text,
                    duration_ms=res.duration_ms,
                    is_error=not success,
                )

                if success:
                    tool_name = calls[idx].tool_name or "unknown_tool"
                    arguments = calls[idx].arguments or {}

                    fact = {
                        "text": content_text,
                        "query": task.get("description", ""),
                        "source": tool_name,
                        "source_url": "",
                        "task_id": t_id,
                        "persist": t_persist,
                        "tool_citation": _legacy_citation,
                    }
                    facts.append(fact)

                    ctx = get_context_pool()
                    extracted_urls = ctx.extract_urls_from_text(content_text)

                    if not extracted_urls and "url" in calls[idx].arguments:
                        url_arg = calls[idx].arguments["url"]
                        if isinstance(url_arg, str) and url_arg.startswith("http"):
                            extracted_urls.append(url_arg)

                    # Backfill source_url from genuinely extracted URLs (no fabrication)
                    if extracted_urls:
                        _legacy_citation["source_url"] = extracted_urls[0]
                        fact["source_url"] = extracted_urls[0]

                    _cite_url = _legacy_citation.get("source_url", "")
                    if _cite_url and _cite_url.startswith("http"):
                        if _cite_url not in [s.get("url") for s in sources]:
                            sources.append(
                                {
                                    "url": _cite_url,
                                    "title": task.get("description", ""),
                                    "tool": calls[idx].tool_name,
                                    "task_id": t_id,
                                }
                            )

                    # Add any URLs extracted from content
                    for url in extracted_urls:
                        if url not in [s.get("url") for s in sources]:
                            sources.append(
                                {
                                    "url": url,
                                    "title": task.get("description", ""),
                                    "tool": calls[idx].tool_name,
                                    "task_id": t_id,
                                }
                            )

                    # Store in DataPool for bucket pattern
                    try:
                        data_pool = get_data_pool()
                        await data_pool.create_pool_item(
                            pool_id=state.get("job_id", "default"),
                            metadata={
                                "fact_text": content_text[:5000],
                                "source": calls[idx].tool_name,
                                "task_id": t_id,
                                "query": task.get("description", ""),
                            },
                            status="raw",
                        )
                    except Exception as e:
                        logger.debug(f"DataPool storage skipped: {e}")

                    # ARTIFACT HARVESTING: Scan for file paths
                    import re

                    file_matches = re.findall(
                        r"[\w\-\._\/]+\.(?:csv|parquet|xlsx|json)", content_text
                    )
                    for fpath in file_matches:
                        fpath = fpath.strip()
                        if len(fpath) > 4:
                            ctx.store_file(t_id, fpath)
                            logger.info(f"     Harvested artifact: {fpath}")

                    completed.add(t_id)
                    logger.info(f"     Task {t_id} completed via {calls[idx].tool_name}")

                    if calls[idx].tool_name in ["execute_code", "run_python"]:
                        logger.info(
                            f"     EXECUTION OUTPUT:\n{'-' * 60}\n{content_text.strip()}\n{'-' * 60}"
                        )
                else:
                    # Handle hard failure
                    tool_name = calls[idx].tool_name
                    error_text = "Unknown error"

                    if res.result and hasattr(res.result, "content"):
                        for c in res.result.content:
                            if hasattr(c, "text"):
                                error_text = c.text
                                break
                    elif res.result:
                        error_text = str(res.result)

                    if "Tool execution error:" in error_text:
                        error_text = error_text.replace(
                            "Tool execution error:", "Missing parameter:"
                        )

                    logger.warning(f"     Task {t_id} ({tool_name}) FAILED: {error_text}")

                    # ERROR FEEDBACK LOOP: Capture error for LLM self-correction
                    # This allows the planner to learn from mistakes on retry
                    error_feedback.append(
                        {
                            "tool": tool_name,
                            "task_id": t_id,
                            "error": error_text[:500],  # Truncate for context window
                            "args": calls[idx].arguments,
                            "description": task.get("description", ""),
                        }
                    )

                    # Prevent re-execution to avoid infinite loop
                    completed.add(t_id)

                # Log invocation (single entry per task, no duplicates)
                tool_invocations.append(
                    {
                        "task_id": t_id,
                        "tool": calls[idx].tool_name,
                        "success": success,
                        "persist": t_persist,
                        "tool_citation": _legacy_citation,
                    }
                )

    # Summary Logging
    logger.info("\n  Parallel Research Summary:")
    logger.info(f"   Facts collected: {len(facts)}")
    logger.info(f"   Sources found: {len(sources)}")

    # ============================================================
    # RERANK FACTS BY RELEVANCE (Neural Reranking)
    # ============================================================
    if facts and len(facts) > 1:
        try:
            from shared.config import get_settings
            from shared.embedding.model_manager import get_reranker_provider

            query = state.get("query", "")
            reranker = get_reranker_provider()
            config = get_settings()

            # GPU MEMORY SAFETY (User Request)
            try:
                import gc

                import torch

                gc.collect()
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            except ImportError:
                pass

            # Extract text from facts for reranking (increased limit for financial tables)
            fact_texts = [f.get("text", "")[:8000] for f in facts]

            # Use top_k from config
            # (Previously was hardware aware, now config driven, which can be hardware aware if we tune defaults)
            top_k = min(len(facts), config.reranker.per_task_top_k)

            logger.info(f"     Reranking {len(facts)} facts by relevance to query...")
            logger.debug(f"     Reranker Query: {query[:100]}...")
            logger.debug(f"     Reranker Sample Fact: {fact_texts[0][:100]}...")

            try:
                results = await reranker.rerank(query, fact_texts, top_k=top_k)
                if results:
                    logger.info(
                        f"     Top Score: {results[0].score:.4f}, Bottom Score: {results[-1].score:.4f}"
                    )
                else:
                    logger.warning("     Reranker returned no results")
            except Exception as e:
                # OOM CHECK & RECOVERY
                is_oom = "out of memory" in str(e).lower()
                if is_oom:
                    import gc

                    import torch

                    from shared.embedding.model_manager import switch_reranker_device

                    logger.warning("  CUDA OOM detected during reranking. Initiating failover...")

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
                            except Exception:
                                pass

                    logger.warning(
                        f"     Switching reranker to {new_device} and retrying operation..."
                    )

                    # Switch device
                    switch_reranker_device(new_device)

                    # Retry execution
                    results = await reranker.rerank(query, fact_texts, top_k=top_k)
                    logger.info(f"     Retry successful on {new_device}")
                else:
                    raise e
            finally:
                # Cleanup after heavy operation
                try:
                    import gc

                    import torch

                    gc.collect()
                    if torch.cuda.is_available():
                        torch.cuda.empty_cache()
                except Exception:
                    pass

            # Reorder facts by reranker score
            reranked_facts = []
            for r in results:
                fact = facts[r.index].copy()
                fact["rerank_score"] = r.score
                reranked_facts.append(fact)

            facts = reranked_facts
            logger.info(f"     Reranked to top {len(facts)} facts")

        except Exception as e:
            logger.warning(f"     Reranking failed, using original order: {e}")

    logger.info("=" * 70 + "\n")

    return {
        **state,
        "facts": facts,
        "sources": sources,
        "tool_invocations": tool_invocations,
        "error_feedback": error_feedback,  # Pass errors to LLM for self-correction on retry
        "completed_calls": completed_calls,  # Persist deduplication cache
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

    logger.info("\n" + "=" * 70)
    logger.info("  STEP 4: KEEPER NODE (Context Guard)")
    logger.info("=" * 70)
    logger.info(f"Iteration: {iteration}/{max_iterations}")
    logger.info(f"Facts collected: {len(facts)}")

    # Call real keeper that checks context drift
    updated_state = await real_keeper_node(dict(state))

    should_continue = updated_state.get("should_continue", False)
    drift_detected = updated_state.get("drift_detected", False)

    if drift_detected:
        logger.info("  Context drift detected!")

    if should_continue:
        logger.info("  Decision: CONTINUE research loop")
    else:
        logger.info("  Decision: STOP research, proceed to synthesis")

    logger.info("=" * 70 + "\n")

    return {**state, **updated_state}


async def generator_node(state: GraphState) -> GraphState:
    """Generate initial answer from facts using real LLM (Optimist role)."""
    logger.info("\n" + "=" * 70)
    logger.info("  STEP 5: GENERATOR NODE (LLM Call - The Optimist)")
    logger.info("=" * 70)

    facts = state.get("facts", [])
    sources = state.get("sources", [])
    query = state.get("query", "")
    critic_feedback = state.get("critic_feedback", None)  # For revisions
    revision_count = state.get("revision_count", 0)

    logger.info(f"Query: {query[:100]}...")
    logger.info(f"Facts available: {len(facts)}")
    if revision_count > 0:
        logger.info(f"  REVISION ATTEMPT #{revision_count}")
    logger.info("-" * 70)
    logger.info("Calling LLM to generate comprehensive answer...")

    generator = GeneratorAgent()
    output = await generator.generate(query, facts, sources, revision_feedback=critic_feedback)

    logger.info(f"\n  Generator Output ({len(output)} chars):")
    logger.info("-" * 70)
    # Print full output
    logger.info(output)
    logger.info("-" * 70)
    logger.info("=" * 70 + "\n")

    return {
        **state,
        "generator_output": output,
    }


async def critic_node(state: GraphState) -> GraphState:
    """Critique the generator's output using real LLM (Pessimist role)."""
    logger.info("\n" + "=" * 70)
    logger.info("  STEP 6: CRITIC NODE (LLM Call - The Pessimist)")
    logger.info("=" * 70)

    generator_output = state.get("generator_output", "")
    facts = state.get("facts", [])
    sources = state.get("sources", [])

    logger.info(f"Reviewing answer ({len(generator_output)} chars)")
    logger.info("-" * 70)
    logger.info("Calling LLM to critique and find weaknesses...")

    critic = CriticAgent()
    feedback = await critic.critique(generator_output, facts, sources)

    logger.info(f"\n  Critic Feedback ({len(feedback)} chars):")
    logger.info("-" * 70)
    # Print full feedback
    logger.info(feedback)
    logger.info("-" * 70)
    logger.info("=" * 70 + "\n")

    return {
        **state,
        "critic_feedback": feedback,
    }


async def judge_node(state: GraphState) -> GraphState:
    """Synthesize generator/critic into final verdict using real LLM."""
    logger.info("\n" + "=" * 70)
    logger.info("  STEP 7: JUDGE NODE (LLM Call - The Arbiter)")
    logger.info("=" * 70)

    query = state.get("query", "")
    generator_output = state.get("generator_output", "")
    critic_feedback = state.get("critic_feedback", "")
    facts = state.get("atomic_facts", [])  # Get facts for quality-based confidence

    logger.info(
        f"Evaluating: Generator ({len(generator_output)} chars) vs Critic ({len(critic_feedback)} chars)"
    )
    logger.info("-" * 70)
    logger.info("Calling LLM to make final judgment...")

    judge = JudgeAgent()
    result = await judge.judge(query, generator_output, critic_feedback, facts=facts)

    verdict = result.get("verdict", "Accept")
    confidence = result.get("confidence", 0.5)
    reasoning = result.get("reasoning", "")

    logger.info(f"\n  Judge Verdict: {verdict}")
    logger.info(f"  Confidence: {confidence:.0%}")
    logger.info("\n  Reasoning:")
    logger.info("-" * 70)
    logger.info(reasoning[:500] if len(reasoning) > 500 else reasoning)
    logger.info("-" * 70)
    logger.info("=" * 70 + "\n")

    # Increment revision count if verdict is Revise
    revision_count = state.get("revision_count", 0)
    if verdict == "Revise":
        revision_count += 1
        logger.info(f"  Revision requested. Count: {revision_count}")

    # IMPORTANT: Preserve reward confidence from Keeper, store judge's confidence separately
    # The reward score is calculated based on research quality metrics (facts, tools, errors)
    # The judge's confidence is a quality assessment of the generated answer
    reward_confidence = state.get("confidence", 0.0)
    if reward_confidence > 0:
        # Reward confidence was calculated by Keeper - preserve it
        final_confidence = reward_confidence
        logger.info(
            f"  Preserving reward confidence: {reward_confidence:.0%} (Judge suggested: {confidence:.0%})"
        )
    else:
        # No reward score yet, fallback to judge's assessment
        final_confidence = confidence

    return {
        **state,
        "judge_verdict": verdict,
        "judge_confidence": confidence,  # Judge's assessment (for logging/debug)
        "confidence": final_confidence,  # Actual confidence (Reward score or fallback)
        "revision_count": revision_count,
    }


@audited(AuditEventType.QUERY_COMPLETED, "Synthesizer Node generated final report")
async def synthesizer_node(state: GraphState) -> GraphState:
    """Create final report from all inputs."""
    logger.info("\n" + "=" * 70)
    logger.info("  STEP 8: SYNTHESIZER NODE (Final Report)")
    logger.info("=" * 70)

    query = state.get("query", "")
    facts = state.get("facts", [])
    sources = state.get("sources", [])
    tool_invocations = state.get("tool_invocations", [])
    generator_output = state.get("generator_output", "")
    confidence = state.get("confidence", 0.0)
    verdict = state.get("judge_verdict", "Unknown")

    logger.info(f"Query: {query[:100]}...")
    logger.info(f"Facts collected: {len(facts)}")
    logger.info(f"Sources: {len(sources)}")
    logger.info(f"Judge Verdict: {verdict}")
    logger.info(f"Confidence: {confidence:.0%}")
    logger.info("-" * 70)
    logger.info("Generating final report...")

    _tmpl = get_report_template()
    _sec = _tmpl.get("sections", {})
    _tbl = _tmpl.get("source_table", {})

    report = _sec.get("title", "# Research Report: {query}").format(query=query) + "\n\n"
    report += (
        _sec.get("metadata", "").format(
            confidence_pct=f"{confidence:.0%}",
            sources_count=len(sources),
            facts_count=len(facts),
            verdict=verdict,
        )
        + "\n\n"
    )
    report += _sec.get("divider", "---") + "\n\n"
    report += generator_output + "\n\n" + _sec.get("divider", "---") + "\n\n"
    report += _sec.get("facts_heading", "## Facts Collected") + "\n\n"

    _fact_row_fmt = _sec.get("fact_row", "{n}. {text}...\n")
    for i, fact in enumerate(facts[:_REPORT_MAX_FACTS], 1):
        if isinstance(fact, dict):
            _text = fact.get("text", str(fact))[:150]
        else:
            _text = str(fact)[:150]
        report += _fact_row_fmt.format(n=i, text=_text)

    report += "\n" + _sec.get("sources_heading", "## Sources") + "\n\n"
    report += _tbl.get("header", "") + "\n"
    report += _tbl.get("separator", "") + "\n"
    _seen_citations: set[str] = set()
    _citation_n = 1
    _row_fmt = _tbl.get(
        "row", "| {n} | `{tool}` | {args} | {server} | {dur_ms:.0f}ms | {url_cell} | {ts} |\n"
    )
    for _inv in tool_invocations[:_REPORT_MAX_INV]:
        _tc = _inv.get("tool_citation")
        if not _tc or not isinstance(_tc, dict):
            continue
        _dedup = f"{_tc.get('tool_name')}:{str(_tc.get('arguments', {}))[:80]}"
        if _dedup in _seen_citations:
            continue
        _seen_citations.add(_dedup)
        _tc_url = _tc.get("source_url", "")
        _tc_args = _tc.get("arguments", {})
        _tc_args_short = (
            "; ".join(f"{k}={str(v)[:30]}" for k, v in list(_tc_args.items())[:3]) or "-"
        )
        report += _row_fmt.format(
            n=_citation_n,
            tool=_tc.get("tool_name", "unknown"),
            args=_tc_args_short,
            server=_tc.get("server_name", "unknown"),
            dur_ms=_tc.get("duration_ms", 0.0),
            url_cell=f"[link]({_tc_url})" if _tc_url.startswith("http") else (_tc_url or "-"),
            ts=_tc.get("invoked_at", "")[:19],
        )
        _citation_n += 1
    if _citation_n == 1:
        _fb_fmt = _tbl.get("fallback_row", "- [{title}]({url})\n")
        for src in sources[:_REPORT_MAX_SRC]:
            report += _fb_fmt.format(title=src.get("title", "Unknown"), url=src.get("url", ""))

    logger.info(f"\n  Final Report Generated ({len(report)} chars)")
    logger.info("=" * 70)
    logger.info("\n" + " " * 35)
    logger.info("                    RESEARCH COMPLETE")
    logger.info(" " * 35 + "\n")

    return {
        **state,
        "report": report,
        "status": "completed",
    }


# ============================================================================
# Routing Functions
# ============================================================================


def should_continue_research(state: GraphState) -> Literal["researcher", "generator", "planner"]:
    """Decide whether to continue research, replan, or move to synthesis."""
    # REPLAN PATH: When all tools failed with errors, go back to planner
    # This allows the LLM to receive error_feedback and correct tool calls
    stop_reason = state.get("stop_reason", "")
    if stop_reason == "replan":
        logger.info("  Replanning: Routing back to planner with error feedback")
        return "planner"

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
    max_revisions = state.get("max_revisions", _MAX_REVISIONS_DEFAULT)

    if verdict == "Revise" and revision_count < max_revisions:
        logger.info(f"  Judge requested revision. Attempt {revision_count + 1}/{max_revisions}")
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

    # Conditional edge: continue research, replan, or synthesize
    graph.add_conditional_edges(
        NodeName.KEEPER.value,
        should_continue_research,
        {
            "researcher": NodeName.RESEARCHER.value,
            "planner": NodeName.PLANNER.value,  # Replan path for error correction
            "generator": NodeName.GENERATOR.value,
        },
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
        },
    )

    graph.add_edge(NodeName.SYNTHESIZER.value, END)

    return graph


def compile_research_graph():
    """Compile the research graph for execution."""
    graph = build_research_graph()
    return graph.compile()


# ============================================================================
# Agentic Workflow Runner (Autonomous Human-Like Execution)
# ============================================================================


async def run_agentic_research(
    query: str, job_id: str | None = None, max_steps: int = 15
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
    from kernel.interfaces.tool_registry import get_tool_registry
    from kernel.flow.agentic_workflow import AgenticWorkflow

    logger.info("=" * 70)
    logger.info("  AGENTIC WORKFLOW MODE - Human-Like Autonomous Research")
    logger.info("=" * 70)
    logger.info(f"Query: {query[:200]}")
    logger.info("-" * 70)

    registry = get_tool_registry()

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

    # Filter to relevant tool prefixes (from configs/vocab/classification.yaml)
    relevant_prefixes = _AGENTIC_PREFIXES
    available_tools = [
        {"name": t.get("name", ""), "description": t.get("description", "")}
        for t in all_tools
        if any(p in t.get("name", "").lower() for p in relevant_prefixes)
    ][:_MAX_TOOLS]

    logger.info(f"  Discovered {len(available_tools)} relevant tools")

    # Run the agentic workflow
    workflow = AgenticWorkflow(tool_executor=tool_executor, max_steps=max_steps)

    state = await workflow.run(query=query, available_tools=available_tools)

    # Log summary
    logger.info("=" * 70)
    logger.info("  AGENTIC WORKFLOW COMPLETE")
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
        "job_id": job_id,
    }
