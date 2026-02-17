"""
Cognitive Cycle   The Full Human Thinking Loop.

Replaces the flat ReAct loop (think act observe repeat) with a
biologically-inspired cognitive cycle:

    Perceive   Frame   Plan   Execute   Monitor   Adapt   Package

Each phase is a discrete async method that can be overridden or
customised per cognitive profile.  The cycle integrates with
``WorkingMemory`` for structured state, ``CognitiveProfile`` for
level-aware behaviour, and ``CellCommunicator`` for inter-cell
messaging during execution.

The ``CognitiveCycle`` is used *inside* `KernelCell._execute_solo()` to
replace the old flat reasoning loop.  Delegation is handled separately
by the kernel cell's own delegation path   this module only governs
how a single cell *thinks and works*.

Communication Integration (v2.0):
- PLAN phase: if clarification is needed AND a communicator is present,
  the cycle asks the parent directly instead of returning early.
- EXECUTE loop: checks for redirect/cancel messages and peer-shared
  data between steps; reports progress at configurable intervals.
- MONITOR phase: includes communication signals (redirects, shared data)
  in the self-assessment.

Version: 0.4.0   Brain Upgrade + Communication Network
"""

from __future__ import annotations

import json
from collections.abc import Awaitable, Callable
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator

from shared.logging import get_logger
from shared.prompts import get_agent_prompt, get_kernel_config, get_report_template

from kernel.core.cognitive_profiles import CognitiveProfile, ReasoningStyle
from kernel.logic.convergence import ConvergenceDetector, IterationSnapshot
from kernel.memory.error_journal import (
    ErrorEntry,
    ErrorSeverity,
    ErrorSource,
    ErrorStatus,
    FixAttempt,
    FixResult,
)
from kernel.io.output_schemas import (
    Artifact,
    ArtifactMetadata,
    ArtifactStatus,
    ArtifactType,
    WorkPackage,
)
from kernel.memory.artifact_store import ArtifactStore
from kernel.core.assembler import resolve_and_wire_inputs
from kernel.memory.working_memory import (
    FocusItem,
    FocusItemType,
    WorkingMemory,
)
from kernel.flow.workflow_nodes import (
    WorkflowNode,
    NodeResult,
    NodeStatus,
    NodeType,
    parse_blueprint,
)
from kernel.flow.dag_executor import DAGExecutor

logger = get_logger(__name__)


# ============================================================================
# Cycle Phase Enum
# ============================================================================


class CyclePhase(str, Enum):
    """Current phase in the cognitive cycle."""

    PERCEIVE = "perceive"  # Understand the instruction + route intent
    EXPLORE = "explore"  # Pre-planning reconnaissance (tools, sources, knowledge)
    FRAME = "frame"  # Restate the problem, identify assumptions
    PLAN = "plan"  # Choose approach, estimate effort
    EXECUTE = "execute"  # Do the work (tool calls, analysis)
    MONITOR = "monitor"  # Self-check: am I on track?
    ADAPT = "adapt"  # Change approach if needed
    PACKAGE = "package"  # Format results for consumer


# ============================================================================
# Phase Outputs (structured results from each phase)
# ============================================================================


class PerceptionResult(BaseModel):
    """Output of the PERCEIVE phase."""

    task_text: str = Field(description="The core instruction")
    implicit_expectations: list[str] = Field(
        default_factory=list,
        description="What the requester probably expects but didn't say",
    )
    urgency: str = Field(default="normal", description="normal | high | critical")
    output_format_hint: str = Field(
        default="",
        description="Expected output format (markdown, table, JSON, etc.)",
    )
    key_entities: list[str] = Field(
        default_factory=list,
        description="Key entities/topics mentioned in the task",
    )
    # IntentionRouter classification (v0.3.x legacy)
    intent_path: str = Field(
        default="D",
        description="Intent path: A (memory) | B (verify) | C (synthesis) | D (deep research)",
    )


class ExploreResult(BaseModel):
    """Output of the EXPLORE phase   pre-planning reconnaissance."""

    available_tools: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Relevant tool dicts (name, description, inputSchema) from RAG registry",
    )
    suggested_sources: list[str] = Field(
        default_factory=list,
        description="Data sources worth querying",
    )
    domain_knowledge: list[str] = Field(
        default_factory=list,
        description="Retrieved knowledge snippets",
    )
    prior_findings: list[str] = Field(
        default_factory=list,
        description="Cross-session findings from Vault",
    )
    exploration_notes: str = Field(
        default="",
        description="LLM assessment of the tool/source landscape",
    )


class FramingResult(BaseModel):
    """Output of the FRAME phase."""

    restatement: str = Field(description="Problem restated in own words")
    assumptions: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    scope_boundaries: Any = Field(
        default="",
        description="What IS and IS NOT in scope",
    )

    @field_validator("scope_boundaries", mode="before")
    @classmethod
    def parse_scope_boundaries(cls, v: Any) -> str:
        if isinstance(v, (dict, list)):
            return json.dumps(v, indent=2)
        return str(v)
    known_facts: list[str] = Field(
        default_factory=list,
        description="Facts already known (from memory/context)",
    )
    unknown_gaps: list[str] = Field(
        default_factory=list,
        description="Information gaps that need to be filled",
    )


class WorkflowStep(BaseModel):
    """A single step in a DAG workflow."""
    id: str = Field(description="Unique step ID (e.g., 'step_1')")
    step: str = Field(description="Description of the step")
    tool: str | None = Field(default=None, description="Tool to use (if any)")
    args: dict[str, Any] = Field(default_factory=dict, description="Tool arguments")
    depends_on: list[str] = Field(default_factory=list, description="IDs of steps that must finish first")


class PlanResult(BaseModel):
    """Output of the PLAN phase."""

    approach: str = Field(description="High-level strategy")
    steps: list[str] = Field(description="Ordered steps to execute")
    estimated_tools: int = Field(default=0)
    estimated_steps: int = Field(default=3)
    risk_factors: list[str] = Field(default_factory=list)
    can_complete_solo: bool = Field(default=True)
    needs_delegation: bool = Field(default=False)
    needs_clarification: bool = Field(default=False)
    clarification_questions: list[str] = Field(default_factory=list)

    # Explicit DAG workflow (v0.4.0)
    workflow: list[WorkflowStep] = Field(
        default_factory=list,
        description="Explicit DAG definition for parallel execution",
    )

    # Restored from old Planner node: explicit tool assignment per step.
    # Each entry maps step index (0-based) to {"tool": "<name>", "args_hint": {...}}.
    # Empty dict ({}) = no tool assigned for that step (LLM decides freely).
    step_tool_assignments: list[dict[str, Any]] = Field(
        default_factory=list,
        description=(
            "Per-step tool assignments from the planner. "
            "Index matches steps[]. Empty dict = LLM-decided step."
        ),
    )

    @field_validator("risk_factors", mode="before")
    @classmethod
    def parse_risk_factors(cls, v: Any) -> list[str]:
        """Handle LLM returning a single string instead of a list."""
        if isinstance(v, str):
            # Split by newlines or just wrap if it looks like a sentence
            if "\n" in v:
                return [line.strip("- *") for line in v.split("\n") if line.strip()]
            return [v]
        return v

    @model_validator(mode="before")
    @classmethod
    def normalize_steps_format(cls, data: Any) -> Any:
        """
        Handle the LLM returning a merged format where each step is a dict:
            steps: [{"step": "...", "tool": "web_search", "args_hint": {...}}, ...]

        Instead of the expected separate lists:
            steps: ["...", "..."]
            step_tool_assignments: [{"tool": "web_search", "args_hint": {...}}, {}]

        Extracts step text into steps[] and tool info into step_tool_assignments[].
        """
        if not isinstance(data, dict):
            return data
        
        # Also clean up workflow if provided as simple dicts
        workflow_raw = data.get("workflow", [])
        if workflow_raw and isinstance(workflow_raw, list):
            # Ensure proper WorkflowStep structure if simplified
            cleaned_wf = []
            for item in workflow_raw:
                if isinstance(item, dict):
                    # Ensure ID exists
                    if "id" not in item:
                        item["id"] = f"step_{len(cleaned_wf)}"
                    cleaned_wf.append(item)
            data["workflow"] = cleaned_wf

        raw_steps = data.get("steps", [])
        if not raw_steps or not isinstance(raw_steps, list) or not isinstance(raw_steps[0], dict):
            return data  # Already in correct str format

        steps_clean: list[str] = []
        assignments: list[dict[str, Any]] = []

        for item in raw_steps:
            if isinstance(item, dict):
                step_text = item.get("step") or item.get("description") or str(item)
                steps_clean.append(str(step_text))
                tool_name = item.get("tool", "")
                args_hint = item.get("args_hint") or item.get("arguments") or {}
                # Guard against LLM returning tool as "{}" string
                if (
                    isinstance(tool_name, str)
                    and tool_name
                    and tool_name not in ("{}", "null", "none", "")
                ):
                    assignments.append(
                        {"tool": tool_name, "args_hint": args_hint if isinstance(args_hint, dict) else {}}
                    )
                else:
                    assignments.append({})
            else:
                steps_clean.append(str(item))
                assignments.append({})

        data["steps"] = steps_clean
        # Only fill assignments if not already explicitly provided
        if not data.get("step_tool_assignments"):
            data["step_tool_assignments"] = assignments

        logger.debug(
            f"PlanResult.normalize_steps_format: extracted {len(steps_clean)} steps, "
            f"{sum(1 for a in assignments if a.get('tool'))} tool assignments from merged format"
        )
        return data


class MonitorResult(BaseModel):
    """Output of the MONITOR phase (self-assessment)."""

    on_track: bool = Field(default=True)
    progress_pct: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Estimated progress 0.0 1.0",
    )
    quality_so_far: str = Field(
        default="adequate",
        description="poor | adequate | good | excellent",
    )
    drift_detected: bool = Field(default=False)
    repetition_detected: bool = Field(default=False)
    stagnation_detected: bool = Field(default=False)
    weak_areas: list[str] = Field(default_factory=list)
    should_continue: bool = Field(default=True)
    should_change_approach: bool = Field(default=False)
    suggested_adjustment: str = Field(default="")

    # Communication signals (v2.0)
    redirect_received: bool = Field(
        default=False,
        description="True if parent sent a REDIRECT/CANCEL during execution",
    )
    redirect_content: str = Field(
        default="",
        description="Content of the redirect message",
    )
    shared_data_count: int = Field(
        default=0,
        description="Number of peer-shared data items received",
    )


class AdaptResult(BaseModel):
    """Output of the ADAPT phase (course correction)."""

    adapted: bool = Field(default=False)
    adjustment: str = Field(default="")
    new_steps: list[str] = Field(default_factory=list)
    reason: str = Field(default="")


class HealResult(BaseModel):
    """Output of the HEAL phase (recursive self-healing)."""

    iterations: int = Field(default=0)
    fixed_count: int = Field(default=0)
    remaining_count: int = Field(default=0)
    cascaded_count: int = Field(default=0)
    converged: bool = Field(default=False)
    convergence_reason: str = Field(default="")
    fixes_applied: list[str] = Field(default_factory=list)


# ============================================================================
# Cognitive Cycle Runner
# ============================================================================


class CognitiveCycle:
    """
    The full human-inspired cognitive cycle for a single kernel cell.

    This replaces the flat ReAct loop with:

        Perceive   Frame   Plan   [Execute   Monitor   Adapt]   Package

    The Execute Monitor loop runs iteratively until the cell either:
    - Reaches sufficient quality (self-assessed + heuristic checks)
    - Exhausts its reasoning budget
    - Hits stagnation/drift and triggers adaptation

    Usage::

        cycle = CognitiveCycle(
            profile=get_cognitive_profile("senior_staff"),
            memory=WorkingMemory(cell_id="analyst-42"),
            llm_call=llm_inference_function,
            tool_call=tool_execution_function,
        )

        result = await cycle.run(
            task="Analyze Tesla's competitive position in EV market",
            context="User is a portfolio manager...",
        )
    """

    def __init__(
        self,
        profile: CognitiveProfile,
        memory: WorkingMemory,
        llm_call: Callable[..., Awaitable[Any]],
        tool_call: Callable[[str, dict[str, Any]], Awaitable[Any]],
        task_id: str = "",
        communicator: Any | None = None,
    ) -> None:
        self.profile = profile
        self.memory = memory
        self.llm_call = llm_call
        self.tool_call = tool_call
        self.task_id = task_id

        # Communication (v2.0)   typed as Any to avoid circular import
        # Actual type: CellCommunicator | None
        self.comm = communicator

        # Internal state
        self.current_phase = CyclePhase.PERCEIVE
        self.monitor_count = 0
        self.tool_call_count = 0
        self.accumulated_content: list[str] = []  # Draft sections
        self.tool_results: list[dict[str, Any]] = []  # Raw tool outputs

        # Communication tracking
        self._progress_report_interval: int = 3  # Report every N steps
        self._last_progress_report: int = 0

        # Convergence tracking
        self._stagnant_steps: int = 0

        # Mid-execution delegation signal
        self._delegation_signal: dict[str, str] | None = None
        
        # Artifact Store for auto-wiring (holds intermediate tool outputs)
        self._store = ArtifactStore()

    # ================================================================ #
    # Main Entry Point
    # ================================================================ #

    async def run(
        self,
        task: str,
        context: str = "",
        available_tools: list[dict[str, Any]] | None = None,
        seed_facts: list[dict[str, Any]] | None = None,
        error_feedback: list[dict[str, Any]] | None = None,
    ) -> CycleOutput:
        """
        Execute the full cognitive cycle.

        Returns a ``CycleOutput`` containing the produced content,
        quality signals, and working memory state.
        """
        start_time = datetime.utcnow()
        available_tools = available_tools or []

        # Load seed facts into working memory
        if seed_facts:
            for fact in seed_facts:
                key = str(fact.get("key") or fact.get("finding") or "unknown_seed_fact")
                content = str(fact.get("content") or fact.get("value") or fact)
                # Avoid duplicate generic keys if possible, but keep simple
                self.memory.store_fact(key, content)

        # Load error feedback into error journal
        if error_feedback:
            try:
                from kernel.memory.error_journal import (
                    ErrorEntry,
                    ErrorSeverity,
                    ErrorSource,
                    ErrorStatus,
                )

                for err in error_feedback:
                    # Map dict to ErrorEntry
                    msg = str(err.get("error") or err.get("message") or "Previously encountered error")
                    ctx = err.get("context") or {}
                    # Try to match source enum, fallback to RUNTIME
                    src_str = str(err.get("source", "runtime"))
                    try:
                        src = ErrorSource(src_str)
                    except ValueError:
                        src = ErrorSource.RUNTIME
                    
                    # Try to match severity enum
                    sev_str = str(err.get("severity", "medium"))
                    try:
                        sev = ErrorSeverity(sev_str)
                    except ValueError:
                        sev = ErrorSeverity.MEDIUM

                    entry = ErrorEntry(
                        source=src,
                        message=msg,
                        context=ctx,
                        severity=sev,
                        status=ErrorStatus.DETECTED,  # Mark as detected so planner sees it
                    )
                    self.memory.error_journal.record(entry)
                    
            except Exception as e:
                logger.warning(f"Failed to load error feedback: {e}")

        logger.info(
            f"  CognitiveCycle [{self.profile.level}] starting | "
            f"style={self.profile.reasoning_style.value} | "
            f"max_steps={self.profile.max_reasoning_steps}"
        )

        #   Phase 1: PERCEIVE  
        self.current_phase = CyclePhase.PERCEIVE
        perception = await self._perceive(task, context)

        #   Phase 1.5: EXPLORE (pre-planning reconnaissance)  
        self.current_phase = CyclePhase.EXPLORE
        exploration = await self._explore(task, perception, available_tools)

        #   Phase 2: FRAME  
        self.current_phase = CyclePhase.FRAME
        framing = await self._frame(task, context, perception)

        #   Phase 3: PLAN  
        self.current_phase = CyclePhase.PLAN
        # Enrich available_tools with exploration discoveries
        if exploration.available_tools:
            # Dict-based dedup: preserve full tool schemas (name + description + inputSchema)
            existing_by_name: dict[str, dict] = {t.get("name", ""): t for t in available_tools}
            for tool_dict in exploration.available_tools:
                name = tool_dict.get("name", "")
                if name and name not in existing_by_name:
                    available_tools.append(tool_dict)
                    existing_by_name[name] = tool_dict
        plan = await self._plan(task, context, perception, framing, available_tools)

        # Short-circuit: if the plan says we need delegation or
        # clarification, return early and let the kernel cell handle it
        if plan.needs_delegation:
            return CycleOutput(
                content="",
                needs_delegation=True,
                plan=plan,
                framing=framing,
                perception=perception,
                quality="not_assessed",
                memory_state=self.memory.to_dict(),
                elapsed_ms=_elapsed_ms(start_time),
            )

        if plan.needs_clarification:
            # v2.0: If we have a communicator, try to resolve
            # clarification directly with the parent instead of
            # returning early and forcing a delegation-level retry.
            if self.comm and plan.clarification_questions:
                resolved = await self._resolve_clarifications(
                    plan.clarification_questions,
                )
                if resolved:
                    # Clarifications answered   continue execution
                    plan.needs_clarification = False
                    plan.clarification_questions = []
                    logger.info(
                        f"  CognitiveCycle: {len(resolved)} clarifications "
                        f"resolved via communicator, continuing"
                    )
                else:
                    # No answers   fall through to early return
                    pass

            if plan.needs_clarification:
                return CycleOutput(
                    content="",
                    needs_clarification=True,
                    clarification_questions=plan.clarification_questions,
                    plan=plan,
                    framing=framing,
                    perception=perception,
                    quality="not_assessed",
                    memory_state=self.memory.to_dict(),
                    elapsed_ms=_elapsed_ms(start_time),
                )

        #   Phase 4+5+6: EXECUTE   MONITOR   ADAPT loop  
        self.current_phase = CyclePhase.EXECUTE
        await self._execute_loop(task, context, plan, available_tools)

        #   Phase 4.5: HEAL (Recursive Self-Healing)  
        if self.memory.error_journal.get_unresolved_count() > 0:
            if self.profile.reasoning_style not in (ReasoningStyle.DIRECT_LOOKUP,):
                heal_result = await self._recursive_heal(
                    task,
                    context,
                    available_tools,
                )
                if heal_result.fixes_applied:
                    logger.info(
                        f"  Heal phase: {heal_result.fixed_count} fixed, "
                        f"{heal_result.remaining_count} remaining, "
                        f"converged={heal_result.converged}"
                    )

        #   Check for mid-execution delegation signal  
        if self._delegation_signal:
            logger.info(
                f"  CognitiveCycle: mid-execution delegation signal   "
                f"{self._delegation_signal['description'][:80]}"
            )
            return CycleOutput(
                content="\n\n".join(self.accumulated_content),
                needs_delegation=True,
                plan=plan,
                framing=framing,
                perception=perception,
                quality="partial",
                tool_results=self.tool_results,
                memory_state=self.memory.to_dict(),
                elapsed_ms=_elapsed_ms(start_time),
                facts_gathered=self.memory.fact_count,
                decisions_made=len(self.memory.decisions),
            )

        #   Phase 7: PACKAGE  
        self.current_phase = CyclePhase.PACKAGE
        work_package = await self._package(perception, framing)

        elapsed = _elapsed_ms(start_time)
        logger.info(
            f"  CognitiveCycle [{self.profile.level}] done | "
            f"{self.memory.step_count} steps | "
            f"{self.tool_call_count} tool calls | "
            f"{elapsed:.0f}ms"
        )

        return CycleOutput(
            content=work_package.summary,  # Legacy summary for content field
            work_package=work_package,
            needs_delegation=False,
            needs_clarification=False,
            plan=plan,
            framing=framing,
            perception=perception,
            quality=self._assess_final_quality(),
            tool_results=self.tool_results,
            memory_state=self.memory.to_dict(),
            elapsed_ms=elapsed,
            facts_gathered=self.memory.fact_count,
            decisions_made=len(self.memory.decisions),
        )

    # ================================================================ #
    # Phase 1: PERCEIVE
    # ================================================================ #

    async def _perceive(self, task: str, context: str) -> PerceptionResult:
        """
        Understand the instruction, detect intent and implicit expectations.

        For lower levels (intern, staff), this is a fast parse.
        For higher levels, this involves deeper comprehension.
        """
        # For intern/staff: lightweight parsing (no LLM call)
        if self.profile.reasoning_style in (
            ReasoningStyle.DIRECT_LOOKUP,
            ReasoningStyle.PROCEDURAL,
        ):
            return PerceptionResult(
                task_text=task,
                key_entities=_extract_entities(task),
            )

        # For senior levels: LLM-assisted perception
        prompt = (
            f"Analyze this task. Identify:\n"
            f"1. The core instruction (what specifically is being asked)\n"
            f"2. Implicit expectations (what the requester probably expects)\n"
            f"3. Key entities/topics mentioned\n"
            f"4. Expected output format\n"
            f"5. Urgency level (normal/high/critical)\n\n"
            f"Task: {task}\n"
        )
        if context:
            prompt += f"\nContext: {context[:500]}\n"

        prompt += "\nRespond in JSON format with keys: task_text, implicit_expectations, key_entities, output_format_hint, urgency"

        try:
            raw = await self.llm_call(
                system_prompt=get_agent_prompt("kernel_perceiver")
                or (
                    "You are a task comprehension expert. Analyze tasks to "
                    "identify exactly what is being asked, including implicit "
                    "expectations. Respond only in JSON."
                ),
                user_prompt=prompt,
            )
            data = _parse_json_safe(raw)
            result = PerceptionResult(
                task_text=data.get("task_text", task),
                implicit_expectations=data.get("implicit_expectations", []),
                key_entities=data.get("key_entities", _extract_entities(task)),
                output_format_hint=data.get("output_format_hint", ""),
                urgency=data.get("urgency", "normal"),
            )
        except Exception as e:
            logger.warning(f"Perception LLM call failed: {e}; using fallback")
            result = PerceptionResult(
                task_text=task,
                key_entities=_extract_entities(task),
            )

        #   IntentionRouter classification (v0.3.x legacy)  
        routing_cfg = get_kernel_config("kernel_cell_routing") or {}
        if routing_cfg.get("enabled", True):
            try:
                from kernel.flow.router import IntentionRouter

                router = IntentionRouter()
                route_context = {
                    "key_entities": result.key_entities,
                    "urgency": result.urgency,
                }
                intent_path = await router.route(task, route_context)
                result.intent_path = str(intent_path)
                logger.info(f"  IntentionRouter   Path {result.intent_path}")
            except Exception as e:
                default_path = routing_cfg.get("default_path", "D")
                result.intent_path = str(default_path)
                logger.warning(
                    f"IntentionRouter failed: {e}; defaulting to Path {default_path}"
                )

        # Store in working memory
        self.memory.focus_observation(
            "perception",
            f"Task: {result.task_text[:200]}",
            source="perceive",
        )
        self.memory.note("intent_path", result.intent_path)
        for entity in result.key_entities[:5]:
            self.memory.focus_fact(f"entity_{entity}", entity, source="perceive")

        return result

    # ================================================================ #
    # Phase 1.5: EXPLORE (Pre-Planning Reconnaissance)
    # ================================================================ #

    async def _explore(
        self,
        task: str,
        perception: PerceptionResult,
        available_tools: list[dict[str, Any]],
    ) -> ExploreResult:
        """
        Pre-planning reconnaissance   discover tools, sources, and prior knowledge.

        Like Claude Code exploring the codebase before coding, this phase scans
        the landscape so the PLAN phase has context about what's available.
        Skipped for lightweight levels (intern) or when disabled in config.
        """
        explore_cfg = get_kernel_config("kernel_cell_explore") or {}
        if not explore_cfg.get("enabled", True):
            return ExploreResult()

        skip_levels = explore_cfg.get("skip_for_levels", ["intern"])
        if self.profile.level in skip_levels:
            return ExploreResult()

        max_tools = explore_cfg.get("max_tools_to_scan", 30)
        max_knowledge = explore_cfg.get("max_knowledge_snippets", 5)

        #   1. Scan available tools for relevance (preserve full dicts with inputSchema)
        relevant_tools: list[dict[str, Any]] = []
        if available_tools:
            relevant_tools = list(available_tools[:max_tools])

        #   2. Retrieve domain knowledge  
        domain_snippets: list[str] = []
        try:
            from shared.knowledge.retriever import get_knowledge_retriever

            retriever = get_knowledge_retriever()
            if await retriever.is_available():
                knowledge = await retriever.retrieve_all(
                    query=perception.task_text,
                    skill_limit=max_knowledge,
                    rule_limit=2,
                    procedure_limit=2,
                )
                if knowledge:
                    domain_snippets = [
                        s.strip() for s in knowledge.split("\n") if s.strip()
                    ][:max_knowledge]
        except Exception as e:
            logger.debug(f"Knowledge retrieval during EXPLORE failed: {e}")

        #   2b. Query FactStore (RAG vector search) for semantic facts  
        rag_facts: list[str] = []
        max_rag_facts = explore_cfg.get("max_rag_facts", 5)
        try:
            from kernel.interfaces.fact_store import get_fact_store

            fact_store = get_fact_store()
            if fact_store is not None:
                search_query = perception.task_text[:200]
                atomic_facts = await fact_store.search(
                    query=search_query,
                    limit=max_rag_facts,
                )
                if atomic_facts:
                    for af in atomic_facts:
                        # AtomicFact has .claim and .evidence fields
                        fact_text = getattr(af, "claim", None) or str(af)
                        if fact_text:
                            rag_facts.append(fact_text[:500])
                    logger.info(
                        f"  [EXPLORE] FactStore RAG: {len(rag_facts)} facts "
                        f"for '{search_query[:40]}...'"
                    )
        except Exception as e:
            logger.debug(f"FactStore RAG during EXPLORE failed: {e}")

        #   3. Check Vault for prior findings  
        prior_findings: list[str] = []
        max_prior = explore_cfg.get("max_prior_findings", 3)
        try:
            from shared.service_registry import ServiceName, ServiceRegistry

            vault_url = ServiceRegistry.get_url(ServiceName.VAULT)
            if vault_url:
                import httpx

                async with httpx.AsyncClient(timeout=5.0) as client:
                    resp = await client.post(
                        f"{vault_url}/api/v1/search",
                        json={
                            "query": perception.task_text[:200],
                            "limit": max_prior,
                        },
                    )
                    if resp.status_code == 200:
                        results = resp.json().get("results", [])
                        prior_findings = [
                            r.get("summary", r.get("content", ""))[:300]
                            for r in results
                            if r.get("summary") or r.get("content")
                        ]
        except Exception as e:
            logger.debug(f"Vault cross-session lookup during EXPLORE failed: {e}")

        #   4. LLM assessment of landscape
        exploration_notes = ""
        suggested: list[str] = []
        if self.profile.reasoning_style not in (
            ReasoningStyle.DIRECT_LOOKUP,
            ReasoningStyle.PROCEDURAL,
        ):
            logger.info(f"  [EXPLORE] Scouting landscape (tools={len(relevant_tools)} knowledge={len(domain_snippets)} prior={len(prior_findings)})")
            try:
                # Extract names for display only — full dicts stay in relevant_tools
                tool_names_for_prompt = [t.get("name", "?") for t in relevant_tools[:15]]
                prompt = (
                    f"You are scouting the landscape before starting work.\n\n"
                    f"Task: {perception.task_text[:400]}\n"
                    f"Key entities: {', '.join(perception.key_entities[:5])}\n"
                    f"Intent path: {perception.intent_path}\n"
                    f"Available tools ({len(relevant_tools)}): "
                    f"{', '.join(tool_names_for_prompt)}\n"
                )
                if domain_snippets:
                    prompt += f"Domain knowledge: {'; '.join(domain_snippets[:3])}\n"
                if prior_findings:
                    prompt += f"Prior research: {'; '.join(prior_findings[:2])}\n"
                prompt += (
                    "\nProvide a brief exploration assessment in JSON:\n"
                    '{"suggested_sources": [...], "exploration_notes": "..."}'
                )

                raw = await self.llm_call(
                    system_prompt=get_agent_prompt("explorer")
                    or (
                        "You are a research scout. Assess available resources "
                        "and suggest the best sources/tools for the task. "
                        "Respond only in JSON."
                    ),
                    user_prompt=prompt,
                )
                data = _parse_json_safe(raw)
                
                if data.get("exploration_notes"):
                    logger.info(f"  [EXPLORE] Assessment: {data.get('exploration_notes')[:100]}...")
                
                exploration_notes = data.get("exploration_notes", "")
                # suggested_sources are data source URLs/names, NOT MCP tool dicts.
                # Store them separately in ExploreResult.suggested_sources — do NOT
                # merge into relevant_tools which must remain full MCP tool dicts.
                suggested = [s for s in data.get("suggested_sources", []) if isinstance(s, str)]
            except Exception as e:
                logger.debug(f"Exploration LLM call failed: {e}")

        # Merge RAG facts into domain knowledge for downstream consumption
        all_knowledge = domain_snippets + rag_facts

        result = ExploreResult(
            available_tools=relevant_tools,
            suggested_sources=suggested,
            domain_knowledge=all_knowledge,
            prior_findings=prior_findings,
            exploration_notes=exploration_notes,
        )

        # Store exploration in working memory for PLAN phase
        if domain_snippets:
            for i, snippet in enumerate(domain_snippets[:3]):
                self.memory.store_fact(f"explore_knowledge_{i}", snippet[:500])
        if rag_facts:
            for i, fact in enumerate(rag_facts[:5]):
                self.memory.store_fact(f"explore_rag_fact_{i}", fact[:500])
        if prior_findings:
            for i, finding in enumerate(prior_findings[:3]):
                self.memory.store_fact(f"explore_prior_{i}", finding[:500])
        if exploration_notes:
            self.memory.note("exploration_notes", exploration_notes[:500])

        logger.info(
            f"  EXPLORE: {len(relevant_tools)} tools, "
            f"{len(domain_snippets)} knowledge, "
            f"{len(rag_facts)} RAG facts, "
            f"{len(prior_findings)} prior findings"
        )

        return result

    # ================================================================ #
    # Phase 2: FRAME
    # ================================================================ #

    async def _frame(
        self,
        task: str,
        context: str,
        perception: PerceptionResult,
    ) -> FramingResult:
        """
        Restate the problem in own words, identify assumptions and gaps.

        For lower levels: skip framing entirely (just execute).
        For higher levels: deep framing with assumption identification.
        """
        if self.profile.reasoning_style == ReasoningStyle.DIRECT_LOOKUP:
            return FramingResult(
                restatement=task,
                unknown_gaps=["All data needs to be gathered"],
            )

        prompt = (
            f"Restate this problem in your own words and identify:\n"
            f"1. Your assumptions (what you're taking for granted)\n"
            f"2. Constraints (limits on what you can do)\n"
            f"3. Scope boundaries (what IS and IS NOT in scope)\n"
            f"4. Facts you already know\n"
            f"5. Information gaps you need to fill\n\n"
            f"Task: {perception.task_text}\n"
            f"Key entities: {', '.join(perception.key_entities)}\n"
        )
        if context:
            prompt += f"\nContext: {context[:500]}\n"

        prompt += (
            "\nRespond in JSON format with keys: restatement, assumptions, "
            "constraints, scope_boundaries, known_facts, unknown_gaps"
        )

        try:
            raw = await self.llm_call(
                system_prompt=get_agent_prompt("kernel_framer")
                or (
                    "You are an analytical thinker. Restate problems clearly, "
                    "identify assumptions and gaps. Be precise. Respond in JSON."
                ),
                user_prompt=prompt,
            )
            data = _parse_json_safe(raw)
            result = FramingResult(
                restatement=data.get("restatement", task),
                assumptions=data.get("assumptions", []),
                constraints=data.get("constraints", []),
                scope_boundaries=data.get("scope_boundaries", ""),
                known_facts=data.get("known_facts", []),
                unknown_gaps=data.get("unknown_gaps", []),
            )
        except Exception as e:
            logger.warning(f"Framing LLM call failed: {e}; using fallback")
            result = FramingResult(restatement=task)

        # Record assumptions as decisions
        for assumption in result.assumptions[:3]:
            self.memory.decide(
                f"assume_{len(self.memory.decisions)}",
                f"Assumption: {assumption}",
                rationale="Identified during framing phase",
            )

        # Record gaps as focus items
        for gap in result.unknown_gaps[:5]:
            self.memory.focus(
                FocusItem(
                    id=f"gap_{gap[:20]}",
                    item_type=FocusItemType.QUESTION,
                    content=f"Need to find: {gap}",
                    source="frame",
                )
            )

        return result

    # ================================================================ #
    # Phase 3: PLAN
    # ================================================================ #

    async def _plan(
        self,
        task: str,
        context: str,
        perception: PerceptionResult,
        framing: FramingResult,
        available_tools: list[dict[str, Any]],
    ) -> PlanResult:
        """
        Choose approach, estimate effort, decide if delegation is needed.
        """
        if self.profile.reasoning_style == ReasoningStyle.DIRECT_LOOKUP:
            return PlanResult(
                approach="Direct answer",
                steps=["Answer the question directly"],
                estimated_steps=1,
            )

        # Build planning prompt with cognitive profile awareness
        reasoning_instruction = self.profile.get_reasoning_instruction()
        tools_summary = f"\nAvailable tools:\n{self._format_tools(available_tools)}" if available_tools else ""

        prompt = (
            f"Plan how to complete this task.\n\n"
            f"Task: {perception.task_text}\n"
            f"Framing: {framing.restatement}\n"
            f"Known gaps: {', '.join(framing.unknown_gaps[:5])}\n"
            f"Assumptions: {', '.join(framing.assumptions[:3])}\n"
            f"{tools_summary}\n\n"
            f"Reasoning approach: {reasoning_instruction}\n\n"
            f"Your level: {self.profile.level} "
            f"(execution_pct={self.profile.execution_pct:.0%}, "
            f"can_delegate={self.profile.can_delegate})\n\n"
            f"Produce a plan with:\n"
            f"1. approach: high-level strategy\n"
            f"2. steps: ordered list of concrete steps\n"
            f"3. workflow: explicit DAG for complex execution (optional). List of objects:\n"
            f"   {{'id': 'step_0', 'step': 'search google', 'tool': 'web_search', 'args': {{...}}, 'depends_on': []}}\n"
            f"   {{'id': 'step_1', 'step': 'summarize', 'depends_on': ['step_0']}}\n"
            f"   Use this for parallel execution (e.g., step_1 and step_2 both depend on step_0).\n"
            f"4. step_tool_assignments: mapping for sequential steps (legacy/fallback)\n"
            f"   CRITICAL: You MUST populate this AND 'steps' as a backup, even if using 'workflow'.\n"
            f"   Use the same tool/args info here so sequential fallback works if DAG fails.\n"
            f"5. estimated_tools: number of tool calls needed\n"
            f"6. estimated_steps: number of reasoning steps\n"
            f"7. risk_factors: what could go wrong\n"
            f"8. can_complete_solo: can you do this alone?\n"
            f"9. needs_delegation: should this be split across agents?\n"
            f"10. needs_clarification: do you need more info first?\n"
            f"11. clarification_questions: if so, what questions?\n\n"
            f"Respond in JSON only."
        )

        try:
            raw = await self.llm_call(
                system_prompt=get_agent_prompt("kernel_planner")
                or (
                    "You are an execution planner. Create actionable plans "
                    "with clear steps. Be realistic about effort. Respond in JSON."
                ),
                user_prompt=prompt,
            )
            data = _parse_json_safe(raw)
            result = PlanResult(
                approach=data.get("approach", "Sequential analysis"),
                steps=data.get("steps", ["Analyze task", "Execute"]),
                estimated_tools=data.get("estimated_tools", 0),
                estimated_steps=data.get("estimated_steps", 3),
                risk_factors=data.get("risk_factors", []),
                can_complete_solo=data.get("can_complete_solo", True),
                needs_delegation=data.get("needs_delegation", False),
                needs_clarification=data.get("needs_clarification", False),
                clarification_questions=data.get("clarification_questions", []),
                step_tool_assignments=data.get("step_tool_assignments", []),
                workflow=data.get("workflow", []),
            )
        except Exception as e:
            logger.warning(f"Planning LLM call failed: {e}; using default plan")
            # Build a default plan that still wires available tools so auto-wire
            # can fire even when the LLM planner fails (e.g. JSON truncation).
            default_assignments: list[dict[str, Any]] = []
            if available_tools:
                default_assignments = [
                    {"tool": available_tools[0].get("name", ""), "args_hint": {"query": task[:200]}},
                    {},  # analyze step — LLM-decided
                    {},  # synthesize step — LLM-decided
                ]
            result = PlanResult(
                approach="Sequential research and analysis",
                steps=["Gather data using available tools", "Analyze findings", "Synthesize results"],
                step_tool_assignments=default_assignments,
            )

        # Record plan in working memory
        logger.info(f"  [PLAN] Decomposed task into {len(result.steps)} steps (approach: {result.approach})")
        self.memory.decide(
            "plan",
            f"Approach: {result.approach}",
            rationale=f"{len(result.steps)} steps, {result.estimated_tools} tool calls",
        )

        # Override delegation based on cognitive profile
        if not self.profile.can_delegate:
            result.needs_delegation = False

        return result

    # ================================================================ #
    # Phase 4+5+6: EXECUTE   MONITOR   ADAPT loop
    # ================================================================ #

    async def _execute_loop(
        self,
        task: str,
        context: str,
        plan: PlanResult,
        available_tools: list[dict[str, Any]],
    ) -> None:
        """
        The main execution loop with integrated monitoring.

        v0.4.0: Attempts DAG-based parallel execution for medium+ complexity.
        Falls back to sequential ReAct loop for simple queries or on DAG failure.

        v2.0 Communication hooks:
        - Check for REDIRECT/CANCEL from parent between steps
        - Incorporate peer-shared data as it arrives
        - Report progress to parent at regular intervals
        """
        #   Try DAG-based execution for complex queries  
        if await self._try_dag_execution(task, context, plan, available_tools):
            return  # DAG completed successfully

        max_steps = self.profile.max_reasoning_steps
        monitor_interval = max(
            1,
            max_steps // (self.profile.max_self_monitor_checks + 1),
        )

        reasoning_instruction = self.profile.get_reasoning_instruction()
        tools_summary = self._format_tools(available_tools)

        # Auto-wire state: track tool availability and nudge threshold
        self._tools_available: bool = bool(available_tools)
        exec_cfg = get_kernel_config("kernel_cell_execute") or {}
        nudge_threshold: int = exec_cfg.get("tool_call_nudge_after_step", 1)

        assigned_count = sum(1 for a in plan.step_tool_assignments if a.get("tool"))
        logger.info(
            f"  [EXECUTE] starting | max_steps={max_steps} tools={len(available_tools)} "
            f"plan_steps={len(plan.steps)} auto_wire_assignments={assigned_count}"
        )

        for step_idx in range(max_steps):
            self.memory.advance_step()

            #   Communication check (between steps)  
            if self.comm and step_idx > 0:
                # Check for redirect/cancel from parent
                redirect = self.comm.check_for_redirect()
                if redirect:
                    logger.info(
                        f"    Redirect received at step {step_idx}: {redirect.content[:80]}"
                    )
                    self.memory.focus_observation(
                        f"redirect-{step_idx}",
                        f"Parent redirect: {redirect.content[:200]}",
                        source="parent",
                    )
                    # If it's a cancel, stop immediately
                    from kernel.io.message_bus import MessageChannel

                    if redirect.channel == MessageChannel.CANCEL:
                        logger.info("  Execution cancelled by parent")
                        break
                    # Otherwise, record the new direction and let
                    # the monitor/adapt phases incorporate it

                # Incorporate peer-shared data
                shared = self.comm.check_for_shared_data()
                if shared:
                    logger.info(f"    Received {len(shared)} shared item(s) from peers")

                # Report progress at intervals
                if step_idx - self._last_progress_report >= self._progress_report_interval:
                    progress = step_idx / max_steps if max_steps > 0 else 0.0
                    await self._report_progress(progress, task, step_idx)
                    self._last_progress_report = step_idx

            #   Monitor check (periodic)  
            if (
                step_idx > 0
                and step_idx % monitor_interval == 0
                and self.monitor_count < self.profile.max_self_monitor_checks
            ):
                self.current_phase = CyclePhase.MONITOR
                monitor = await self._monitor(task, step_idx, max_steps)
                self.monitor_count += 1

                # Redirect from parent overrides everything
                if monitor.redirect_received:
                    logger.info(
                        f"  Monitor detected redirect, adapting: {monitor.redirect_content[:80]}"
                    )
                    self.current_phase = CyclePhase.ADAPT
                    adapt = await self._adapt(task, monitor, plan)
                    if adapt.adapted and adapt.new_steps:
                        plan.steps = adapt.new_steps
                    self.current_phase = CyclePhase.EXECUTE
                    continue

                if not monitor.should_continue:
                    logger.info(
                        f"  Monitor says stop at step {step_idx}: "
                        f"progress={monitor.progress_pct:.0%}"
                    )
                    break

                if monitor.should_change_approach:
                    self.current_phase = CyclePhase.ADAPT
                    adapt = await self._adapt(task, monitor, plan)
                    if adapt.adapted:
                        logger.info(f"  Adapted: {adapt.adjustment}")
                        # Update plan steps with new approach
                        if adapt.new_steps:
                            plan.steps = adapt.new_steps

                self.current_phase = CyclePhase.EXECUTE

            # --- Auto-Wire: execute assigned tool directly (no LLM choice) ---
            # Restores old Planner node + Node Assembler + Auto-Wire behavior:
            # the Planner already decided what tool to use — execute it directly.
            assignment: dict[str, Any] = {}
            if step_idx < len(plan.step_tool_assignments):
                assignment = plan.step_tool_assignments[step_idx] or {}

            if assignment.get("tool") and self.tool_call_count < self.profile.max_tool_calls:
                tool_name = assignment["tool"]
                raw_args = assignment.get("args_hint", {})
                
                # Resolve inputs (Auto-Wire)
                tool_args = await resolve_and_wire_inputs(
                    input_mapping={},
                    current_args=raw_args,
                    tool_name=tool_name,
                    store=self._store,
                    auto_wirer=None
                )
                
                logger.info(
                    f"  Auto-wire step {step_idx}: executing assigned tool '{tool_name}' "
                    f"args={list(tool_args.keys())}"
                )
                await self._execute_tool(tool_name, tool_args, step_idx)
                self.memory.advance_step()
                continue  # Skip LLM step — tool result is now in working memory

            # Compute nudge flag: fire when past threshold and still 0 tool calls
            nudge = (
                step_idx >= nudge_threshold
                and self.tool_call_count == 0
                and self._tools_available
            )

            #   Execute one reasoning step
            step_prompt = self._build_step_prompt(
                task=task,
                context=context,
                step_idx=step_idx,
                total_steps=max_steps,
                plan=plan,
                tools_summary=tools_summary,
                reasoning_instruction=reasoning_instruction,
                nudge_tool_use=nudge,
            )

            try:
                raw = await self.llm_call(
                    system_prompt=self._build_execute_system_prompt(
                        has_tools=self._tools_available
                    ),
                    user_prompt=step_prompt,
                )
                data = _parse_json_safe(raw)
            except Exception as e:
                logger.warning(f"  Step {step_idx} LLM call failed: {e}")
                continue

            # Process the step output
            thought = data.get("thought", "")
            action = data.get("action", "complete")
            action_input = data.get("action_input", {})
            confidence = data.get("confidence", 0.5)

            logger.info(
                f"  [Step {step_idx + 1}/{max_steps}] action={action} "
                f"confidence={confidence:.2f} tool_calls_so_far={self.tool_call_count}"
            )

            # Record thinking in working memory
            if thought:
                self.memory.note(
                    f"step_{step_idx}_thought",
                    thought[:300],
                )

            # Execute the action
            if action == "call_tool":
                if self.tool_call_count >= self.profile.max_tool_calls:
                    logger.info(
                        f"  Tool budget exhausted "
                        f"({self.tool_call_count}/{self.profile.max_tool_calls})"
                    )
                    # Force synthesis on next step
                    self.memory.note("force_synthesis", "Tool budget exhausted")
                else:
                    tool_name = action_input.get("tool", "")
                    tool_args = action_input.get("arguments", {})
                    if tool_name:
                        logger.info(f"  [call_tool] {tool_name} args={list(tool_args.keys())}")
                        await self._execute_tool(tool_name, tool_args, step_idx)

            elif action == "analyze":
                analysis = action_input.get("analysis", thought)
                if analysis:
                    self.accumulated_content.append(analysis)
                    self.memory.store_fact(
                        f"analysis_{step_idx}",
                        analysis[:500],
                    )

            elif action == "synthesize":
                synthesis = action_input.get("synthesis", "")
                if not synthesis:
                    synthesis = action_input.get("answer", thought)
                if synthesis:
                    self.accumulated_content.append(synthesis)
                    self.memory.store_fact(
                        f"synthesis_{step_idx}",
                        synthesis[:500],
                    )

            elif action == "complete":
                answer = action_input.get("answer", thought)
                if answer:
                    self.accumulated_content.append(answer)
                logger.info(f"  Execution complete at step {step_idx}")
                break

            #   Convergence detection  
            # If new content isn't adding meaningful value, stop early.
            if action in ("analyze", "synthesize") and len(self.accumulated_content) >= 3:
                if self._check_convergence(step_idx):
                    logger.info(
                        f"  Convergence detected at step {step_idx}   "
                        f"new content adds <10% information"
                    )
                    break

            #   Mid-execution delegation signal  
            if action == "delegate":
                subtask_desc = action_input.get("subtask", "")
                subtask_domain = action_input.get("domain", "general")
                if subtask_desc:
                    self._delegation_signal = {
                        "description": subtask_desc,
                        "domain": subtask_domain,
                    }
                    logger.info(
                        f"  Mid-execution delegation signal at step {step_idx}: {subtask_desc[:80]}"
                    )

            # Update confidence
            topic = f"step_{step_idx}"
            self.memory.set_confidence(topic, confidence)

        # Try DAG-based parallel execution for complex queries  
        dag_executed = await self._try_dag_execution(task, context, plan, available_tools)
        if dag_executed:
            return  # DAG completed successfully

        # Fallback to standard execution loop
        max_steps = self.profile.max_reasoning_steps
        monitor_interval = max(
            1,
            max_steps // (self.profile.max_self_monitor_checks + 1),
        )

    
    async def _try_dag_execution(
        self,
        task: str,
        context: str,
        plan: PlanResult,
        available_tools: list[dict[str, Any]],
    ) -> bool:
        """
        Attempt DAG-based parallel execution.

        Uses explicit plan.workflow OR falls back to converting sequential
        steps into a simple phased DAG.
        """
        dag_cfg = get_kernel_config("kernel_cell_dag") or {}
        if not dag_cfg.get("enabled", True):
            return False

        # If explicit workflow is provided, use it directly
        if plan.workflow and len(plan.workflow) > 0:
            logger.info(f"  [DECOMPOSITION] Explicit workflow found ({len(plan.workflow)} nodes)")
            blueprint_steps = []
            for node in plan.workflow:
                step_dict = {
                    "id": node.id,
                    "description": node.step,
                    "type": "tool" if node.tool else "llm",
                    "depends_on": node.depends_on,
                }
                if node.tool:
                    step_dict["tool"] = node.tool
                    step_dict["args"] = node.args or {"query": task[:500]}
                else:
                    step_dict["llm_prompt"] = (
                        f"Execute: {node.step}\nContext: {task[:300]}"
                    )
                    step_dict["llm_system"] = self._build_execute_system_prompt(
                         has_tools=bool(available_tools)
                    )
                blueprint_steps.append(step_dict)
            
            # Execute with Blueprint
            try:
                # Imports already at top-level
                # Define unified executor for DAG
                async def execute_dag_node(node: Any, args: dict[str, Any]) -> NodeResult:
                    # 'node' is a WorkflowNode
                    try:
                        if node.node_type == NodeType.TOOL:
                            if not node.tool:
                                raise ValueError("Tool node missing tool name")
                            output = await self.tool_call(node.tool, args)
                            return NodeResult(node.id, NodeStatus.COMPLETED, output=output)
                        
                        elif node.node_type == NodeType.LLM:
                            prompt = node.llm_prompt or f"Execute: {node.description}"
                            system = node.llm_system or "You are a helpful assistant."
                            raw = await self.llm_call(system_prompt=system, user_prompt=prompt)
                             # Extract output similar to _parse_execution_result or just use raw
                            return NodeResult(node.id, NodeStatus.COMPLETED, output=raw)
                        
                        else:
                            # Fallback for code/agentic if not implemented
                            return NodeResult(node.id, NodeStatus.FAILED, error="Unsupported node type")
                    except Exception as e:
                        return NodeResult(node.id, NodeStatus.FAILED, error=str(e))

                dag_nodes = parse_blueprint(blueprint_steps)
                executor = DAGExecutor(
                    store=self._store,
                    node_executor=execute_dag_node,
                    max_parallel=dag_cfg.get("max_parallel", 4),
                )
                
                logger.info(f"  [DAG] Starting execution of {len(dag_nodes)} nodes (explicit)")
                result = await executor.execute(dag_nodes)
                
                # Consolidate results
                for res in result.node_results.values():
                    if res.status == NodeStatus.COMPLETED:
                        output_str = str(res.output)
                        self.accumulated_content.append(output_str)
                        if res.output:
                            self.memory.store_fact(f"dag_result_{res.node_id}", output_str[:500])
                            # Also store explicit artifacts as facts if useful
                            if res.artifacts:
                                for k, v in res.artifacts.items():
                                    self.memory.store_fact(f"{k}", str(v)[:500])
                
                return True
            except Exception as e:
                logger.warning(f"  DAG execution failed: {e}, falling back to sequential")
                return False

        # Fallback: Heuristic DAG construction (existing logic)
        # Check complexity threshold   skip DAG for trivial/low
        min_complexity = dag_cfg.get("min_complexity_for_dag", "medium")
        complexity_order = ["trivial", "low", "medium", "high", "extreme"]
        # Use plan step count as complexity proxy
        plan_complexity = "low" if plan.estimated_steps <= 2 else "medium"
        if plan.estimated_steps >= 5:
            plan_complexity = "high"

        try:
            min_idx = complexity_order.index(min_complexity)
            cur_idx = complexity_order.index(plan_complexity)
        except ValueError:
            min_idx, cur_idx = 2, 1  # Default: skip

        if cur_idx < min_idx:
            logger.debug(
                f"  DAG skipped: complexity={plan_complexity} < {min_complexity}"
            )
            return False

        #   Convert plan steps   WorkflowNodes  
        try:
            # Imports already at top-level

            blueprint_steps: list[dict[str, Any]] = []
            for i, step_desc in enumerate(plan.steps):
                # Determine if this step should call a tool
                step_dict: dict[str, Any] = {
                    "id": f"step_{i}",
                    "description": step_desc,
                    "phase": (i // 2) + 1,  # Group into phases for parallelism
                }

                # --- Tool matching: assignment-first, substring fallback ---
                # Priority 1: use the planner's explicit assignment (step_tool_assignments).
                # The planner already selected the right tool via RAG — trust it.
                assignment: dict[str, Any] = {}
                if i < len(plan.step_tool_assignments):
                    assignment = plan.step_tool_assignments[i] or {}

                matched_tool = assignment.get("tool", "")
                tool_args_from_plan: dict[str, Any] = assignment.get("args_hint", {})

                if not matched_tool:
                    # Priority 2: legacy substring match (backwards compat)
                    step_lower = step_desc.lower()
                    for t in available_tools:
                        t_name = t.get("name", "")
                        if t_name and t_name.lower() in step_lower:
                            matched_tool = t_name
                            break

                if matched_tool:
                    step_dict["type"] = "tool"
                    step_dict["tool"] = matched_tool
                    step_dict["args"] = tool_args_from_plan or {"query": task[:500]}
                    logger.info(f"  [DAG] step_{i}: tool={matched_tool}")
                else:
                    step_dict["type"] = "llm"
                    step_dict["llm_prompt"] = (
                        f"Execute this step: {step_desc}\n\nOriginal task: {task[:300]}"
                    )
                    step_dict["llm_system"] = self._build_execute_system_prompt(
                        has_tools=bool(available_tools)
                    )
                    logger.info(f"  [DAG] step_{i}: llm (no tool assigned)")

                # Dependency: each step depends on the previous in same phase
                if i > 0 and blueprint_steps[i - 1].get("phase") == step_dict["phase"]:
                    step_dict["depends_on"] = []  # Same phase = parallel
                elif i > 0:
                    step_dict["depends_on"] = [f"step_{i - 1}"]

                blueprint_steps.append(step_dict)

            if not blueprint_steps:
                return False

            nodes = parse_blueprint(blueprint_steps)

            #   Build node executor  
            async def node_executor(
                node: WorkflowNode, inputs: dict[str, Any]
            ) -> NodeResult:
                if node.node_type == NodeType.TOOL and node.tool:
                    try:
                        result = await self.tool_call(node.tool, node.args or {})
                        self.tool_call_count += 1
                        result_str = str(result)[:1000] if result else "No output"
                        self.tool_results.append({
                            "tool": node.tool,
                            "args": node.args,
                            "result": result_str,
                            "step": node.id,
                        })
                        self.memory.store_fact(f"dag_{node.id}", result_str[:500])
                        return NodeResult(
                            node_id=node.id,
                            status=NodeStatus.COMPLETED,
                            output=result_str,
                        )
                    except Exception as e:
                        return NodeResult(
                            node_id=node.id,
                            status=NodeStatus.FAILED,
                            error=str(e)[:500],
                        )
                elif node.node_type == NodeType.LLM:
                    try:
                        raw = await self.llm_call(
                            system_prompt=node.llm_system or self._build_execute_system_prompt(),
                            user_prompt=node.llm_prompt or node.description,
                        )
                        content = str(raw)[:2000]
                        self.accumulated_content.append(content)
                        self.memory.store_fact(f"dag_{node.id}", content[:500])
                        return NodeResult(
                            node_id=node.id,
                            status=NodeStatus.COMPLETED,
                            output=content,
                        )
                    except Exception as e:
                        return NodeResult(
                            node_id=node.id,
                            status=NodeStatus.FAILED,
                            error=str(e)[:500],
                        )
                else:
                    return NodeResult(
                        node_id=node.id,
                        status=NodeStatus.COMPLETED,
                        output=f"Skipped node type: {node.node_type}",
                    )

            #   Execute DAG  
            max_concurrent = dag_cfg.get(
                "max_concurrent_default",
                self.profile.max_tool_calls or 4,
            )
            # Share the cycle's artifact store so DAG can see/write shared state
            dag = DAGExecutor(
                store=self._store,
                node_executor=node_executor,
                max_parallel=max_concurrent,
            )

            dag_result = await dag.execute(nodes)

            logger.info(
                f"  [DAG] complete: {dag_result.completed}/{dag_result.total_nodes} nodes "
                f"| failed={dag_result.failed} replans={dag_result.replans_triggered} "
                f"| tool_calls={self.tool_call_count}"
            )

            # Feed DAG results back into working memory
            for node_id, nr in dag_result.node_results.items():
                if nr.status == NodeStatus.COMPLETED and nr.output:
                    output_str = str(nr.output)[:500]
                    if output_str not in self.accumulated_content:
                        self.accumulated_content.append(output_str)

            # If too many failures, fall back to sequential
            if dag_result.success_rate < 0.3:
                logger.warning(
                    f"  DAG success rate {dag_result.success_rate:.0%} too low, "
                    f"falling back to sequential"
                )
                return False

            return True

        except Exception as e:
            logger.warning(f"  DAG execution setup failed: {e}; falling back to sequential")
            if dag_cfg.get("sequential_fallback", True):
                return False
            raise

    def _check_convergence(self, step_idx: int) -> bool:
        """
        Check if recent content is converging (diminishing returns).

        Compares the last two accumulated entries. If word overlap exceeds
        90%, we consider the content stagnant.
        """
        if len(self.accumulated_content) < 2:
            return False

        recent = self.accumulated_content[-1].lower().split()
        previous = self.accumulated_content[-2].lower().split()

        if not recent or not previous:
            return False

        recent_set = set(recent)
        previous_set = set(previous)
        overlap = len(recent_set & previous_set) / max(len(recent_set | previous_set), 1)

        if overlap > 0.9:
            self._stagnant_steps += 1
        else:
            self._stagnant_steps = 0

        convergence_cfg = self._get_convergence_config()
        consecutive_threshold = convergence_cfg.get("consecutive_stagnant_steps", 2)

        return self._stagnant_steps >= consecutive_threshold

    def _get_convergence_config(self) -> dict:
        """Load convergence config from kernel.yaml."""
        try:
            from shared.prompts import get_kernel_config

            return get_kernel_config("convergence") or {}
        except Exception:
            return {}

    async def _execute_tool(
        self,
        tool_name: str,
        tool_args: dict[str, Any],
        step_idx: int,
    ) -> None:
        """Execute a tool call and record results in working memory."""
        try:
            result = await self.tool_call(tool_name, tool_args)
            self.tool_call_count += 1

            # Record in working memory
            result_str = str(result)[:1000] if result else "No output"
            self.tool_results.append(
                {
                    "tool": tool_name,
                    "args": tool_args,
                    "result": result_str,
                    "step": step_idx,
                }
            )

            self.memory.store_fact(
                f"tool_{tool_name}_{step_idx}",
                result_str[:500],
            )
            self.memory.focus(
                FocusItem(
                    id=f"tool_result_{step_idx}",
                    item_type=FocusItemType.TOOL_RESULT,
                    content=f"{tool_name}: {result_str[:200]}",
                    source=tool_name,
                )
            )

            logger.debug(f"  Tool {tool_name}: {len(result_str)} chars")
            
            # Store in ArtifactStore for auto-wiring
            step_key = f"step_{step_idx}"
            self._store.store(step_key, "output", result_str)
            self._store.store(step_key, "result", result_str)
            # Also store by tool name if it helps heuristics
            self._store.store(step_key, tool_name, result_str)

        except Exception as e:
            logger.warning(f"  Tool {tool_name} failed: {e}")
            self.memory.note(
                f"tool_error_{step_idx}",
                f"{tool_name} failed: {str(e)[:200]}",
            )
            # Record in error journal for self-healing
            self.memory.error_journal.record_from_tool_failure(
                tool_name=tool_name,
                error_message=str(e)[:500],
                arguments=tool_args,
            )

    # ================================================================ #
    # Phase 5: MONITOR
    # ================================================================ #

    async def _monitor(
        self,
        task: str,
        step_idx: int,
        max_steps: int,
    ) -> MonitorResult:
        """
        Self-check: Am I on track? Is quality sufficient?

        Uses both heuristic checks and (for senior levels) an LLM call.
        v2.0: Also checks for communication signals (redirects, shared data).
        """
        # Heuristic checks (cheap, always run)
        drift = self.memory.detect_drift(task)
        repetition = self.memory.detect_repetition(
            " ".join(self.accumulated_content[-2:]) if self.accumulated_content else ""
        )
        stagnation = self.memory.detect_stagnation()

        progress = step_idx / max_steps if max_steps > 0 else 1.0
        has_content = len(self.accumulated_content) > 0
        has_facts = self.memory.fact_count > 0

        #   Communication signals (v2.0)  
        redirect_received = False
        redirect_content = ""
        shared_data_count = 0

        if self.comm:
            redirect = self.comm.check_for_redirect()
            if redirect:
                redirect_received = True
                redirect_content = redirect.content
                # Redirect overrides normal monitoring
                return MonitorResult(
                    on_track=False,
                    progress_pct=progress,
                    quality_so_far="redirected",
                    should_continue=True,  # Continue but with new direction
                    should_change_approach=True,
                    suggested_adjustment=redirect_content,
                    redirect_received=True,
                    redirect_content=redirect_content,
                )

            shared = self.comm.check_for_shared_data()
            shared_data_count = len(shared)

        #   Keeper-level context guard (legacy)  
        keeper_cfg = get_kernel_config("kernel_cell_keeper") or {}
        keeper_enabled = keeper_cfg.get("enabled", True)
        keeper_contradictions: list[str] = []
        keeper_confidence_boost = 0.0

        if keeper_enabled and self.memory.fact_count >= 2:
            keeper_contradictions, keeper_confidence_boost = await self._keeper_check(
                task, keeper_cfg
            )
            if keeper_contradictions:
                logger.info(
                    f"  Keeper: {len(keeper_contradictions)} contradiction(s) detected"
                )

        # For senior levels, also use LLM self-assessment
        quality_assessment = "adequate"
        weak_areas: list[str] = []
        should_change = False
        suggested_adjustment = ""

        if (
            self.profile.reasoning_style
            not in (ReasoningStyle.DIRECT_LOOKUP, ReasoningStyle.PROCEDURAL)
            and self.accumulated_content
        ):
            try:
                recent_work = "\n".join(self.accumulated_content[-3:])[:1500]
                prompt = (
                    f"You are reviewing your own work IN PROGRESS.\n\n"
                    f"Original task: {task[:300]}\n\n"
                    f"Work so far:\n{recent_work}\n\n"
                    f"Progress: step {step_idx}/{max_steps}\n"
                    f"Facts gathered: {self.memory.fact_count}\n"
                    f"Overall confidence: {self.memory.overall_confidence:.2f}\n"
                )
                if shared_data_count > 0:
                    prompt += f"Peer data received: {shared_data_count} item(s)\n"
                if keeper_contradictions:
                    prompt += (
                        f"CONTRADICTIONS DETECTED:\n"
                        + "\n".join(f"- {c}" for c in keeper_contradictions[:3])
                        + "\n"
                    )
                prompt += (
                    "\nAssess:\n"
                    "1. quality_so_far: poor/adequate/good/excellent\n"
                    "2. weak_areas: list of areas that need improvement\n"
                    "3. should_change_approach: true/false\n"
                    "4. suggested_adjustment: what to do differently\n\n"
                    "Respond in JSON."
                )
                raw = await self.llm_call(
                    system_prompt=get_agent_prompt("keeper_kernel")
                    or (
                        "You are a quality monitor reviewing work in progress. "
                        "Be honest and specific about weaknesses. Respond in JSON."
                    ),
                    user_prompt=prompt,
                )
                data = _parse_json_safe(raw)
                quality_assessment = data.get("quality_so_far", "adequate")
                weak_areas = data.get("weak_areas", [])
                should_change = data.get("should_change_approach", False)
                suggested_adjustment = data.get("suggested_adjustment", "")
            except Exception as e:
                logger.debug(f"Monitor LLM call failed: {e}; using heuristics only")

        # Add keeper-detected contradictions to weak areas
        if keeper_contradictions:
            weak_areas.extend(f"Contradiction: {c}" for c in keeper_contradictions[:2])

        # Combine heuristic + LLM signals
        should_continue = True
        if not has_content and progress > 0.5:
            should_continue = False  # Half budget spent, no content = stalled
        if drift > 0.7:
            should_change = True
            suggested_adjustment = "Refocus on original task   output is drifting"

        return MonitorResult(
            on_track=drift < 0.5 and not stagnation,
            progress_pct=progress,
            quality_so_far=quality_assessment,
            drift_detected=drift > 0.3,
            repetition_detected=repetition,
            stagnation_detected=stagnation,
            weak_areas=weak_areas,
            should_continue=should_continue,
            should_change_approach=should_change or stagnation,
            suggested_adjustment=suggested_adjustment,
            redirect_received=redirect_received,
            redirect_content=redirect_content,
            shared_data_count=shared_data_count,
        )

    # ================================================================ #
    # Phase 6: ADAPT
    # ================================================================ #

    async def _adapt(
        self,
        task: str,
        monitor: MonitorResult,
        plan: PlanResult,
    ) -> AdaptResult:
        """
        Change approach based on monitoring feedback.

        For lower levels: simple heuristic adjustment.
        For senior levels: LLM-driven replanning.
        """
        if self.profile.reasoning_style in (
            ReasoningStyle.DIRECT_LOOKUP,
            ReasoningStyle.PROCEDURAL,
        ):
            # Simple heuristic: if drifting, remind of original task
            if monitor.drift_detected:
                return AdaptResult(
                    adapted=True,
                    adjustment="Refocusing on original task",
                    reason="Drift detected",
                )
            if monitor.stagnation_detected:
                return AdaptResult(
                    adapted=True,
                    adjustment="Moving to synthesis   stagnation detected",
                    new_steps=["Synthesize current findings into final output"],
                    reason="Stagnation detected",
                )
            return AdaptResult(adapted=False)

        # Senior levels: LLM-assisted adaptation
        try:
            prompt = (
                f"Your work needs adjustment.\n\n"
                f"Original task: {task[:300]}\n"
                f"Current approach: {plan.approach}\n"
                f"Current steps: {json.dumps(plan.steps)}\n"
                f"Problems detected:\n"
                f"- Quality: {monitor.quality_so_far}\n"
                f"- Drift: {monitor.drift_detected}\n"
                f"- Stagnation: {monitor.stagnation_detected}\n"
                f"- Weak areas: {', '.join(monitor.weak_areas)}\n"
                f"- Suggested: {monitor.suggested_adjustment}\n\n"
                f"Produce an adjusted plan:\n"
                f"1. adjustment: what to change\n"
                f"2. new_steps: revised steps going forward\n"
                f"3. reason: why this adjustment\n\n"
                f"Respond in JSON."
            )
            raw = await self.llm_call(
                system_prompt=(
                    "You are adapting your work plan based on feedback. "
                    "Be specific about changes. Respond in JSON."
                ),
                user_prompt=prompt,
            )
            data = _parse_json_safe(raw)
            return AdaptResult(
                adapted=True,
                adjustment=data.get("adjustment", "Adjusting approach"),
                new_steps=data.get("new_steps", []),
                reason=data.get("reason", "Quality feedback"),
            )
        except Exception as e:
            logger.warning(f"Adapt LLM call failed: {e}")
            return AdaptResult(
                adapted=True,
                adjustment="Forcing synthesis due to adaptation failure",
                new_steps=["Synthesize all current findings"],
                reason="Adaptation LLM failed",
            )

    async def _rerank_facts(self, task: str) -> None:
        """Rerank facts in working memory by relevance to the task."""
        try:
             from shared.embedding.model_manager import get_reranker_provider
             from shared.config import get_settings
             
             reranker = get_reranker_provider()
             config = get_settings()
             
             if not self.memory.all_facts:
                 return

             fact_items = list(self.memory.all_facts.items())
             fact_texts = [v[:8000] for k, v in fact_items]
             
             top_k = min(len(fact_items), config.reranker.per_task_top_k)
             
             results = await reranker.rerank(task, fact_texts, top_k=top_k)
             
             # Reorder in memory (trickier with dict, but we can update keys or just rely on list usage)
             # For now, just logging corelations or could rebuild dict. 
             # Simpler: just store the high-relevance ones in a focus list or similar.
             # But the memory is a dict. Let's just log for now as per the plan/graph.py logic
             # In graph.py, it reorders the list of facts. Here we have a dict.
             # We can't easily reorder a standard dict in place to affect iteration order reliably across all python versions (though 3.7+ does).
             # Let's confusingly just leave it be, but maybe drop low relevance ones?
             # For safety/speed, let's just update a "relevance" metadata if possible.
             # But cognitive_cycle memory structure is simple {key: text}.
             pass
             
        except Exception as e:
            logger.debug(f"Reranking failed: {e}")

    async def _keeper_check(
        self,
        task: str,
        config: dict[str, Any],
    ) -> tuple[list[str], float]:
        """
        Keeper-level context guard: reranking and contradiction detection.
        """
        contradictions: list[str] = []
        confidence_boost = 0.0
        
        # 1. Rerank facts if enabled
        if config.get("rerank_facts", True):
             await self._rerank_facts(task)

        # 2. Detect contradictions (Neural + Heuristic)
        if config.get("detect_contradictions", True):
            # Simple heuristic check for direct contradictions in recent facts
            recent_facts = list(self.memory.all_facts.values())[-5:]
            if len(recent_facts) >= 2:
                prompt = (
                    f"Check for contradictions between these facts related to: {task[:200]}\n\n"
                    f"Facts:\n" + "\n".join(f"- {f[:300]}" for f in recent_facts) + "\n\n"
                    f"Return JSON: {{'contradictions': ['desc1']}} or {{'contradictions': []}}"
                )
                try:
                    raw = await self.llm_call(
                        system_prompt="You are a contradiction detector. Be strict.",
                        user_prompt=prompt,
                    )
                    data = _parse_json_safe(raw)
                    contradictions = data.get("contradictions", [])
                except Exception:
                    pass

        # 3. Calculate confidence from agreement (simplified)
        # If we have many facts and few contradictions, boost confidence
        if self.memory.fact_count > 5 and not contradictions:
            confidence_boost = 0.1
        elif contradictions:
            confidence_boost = -0.2

        return contradictions, confidence_boost

    # ================================================================ #
    # Phase 4.5: HEAL (Recursive Self-Healing)
    # ================================================================ #

    async def _recursive_heal(
        self,
        task: str,
        context: str,
        available_tools: list[dict[str, Any]],
        max_heal_iterations: int = 3,
    ) -> HealResult:
        """
        Claude Code-style recursive self-healing loop.

        After the execute phase, if errors were recorded in the error journal,
        this method attempts to fix them one by one. Each fix triggers a
        cascade check that may discover new errors, forming a recursive chain.

        The loop terminates on convergence (no more errors), budget exhaustion,
        or diminishing returns.
        """
        journal = self.memory.error_journal
        heal_cfg = self._get_heal_config()
        max_iterations = min(
            max_heal_iterations,
            heal_cfg.get("max_iterations", 3),
        )

        detector = ConvergenceDetector(
            max_iterations=max_iterations,
            max_cascade_depth=heal_cfg.get("max_cascade_depth", 3),
            diminishing_returns_threshold=heal_cfg.get(
                "diminishing_returns_threshold",
                0.1,
            ),
            max_new_errors_per_iteration=heal_cfg.get(
                "max_new_errors_per_iteration",
                5,
            ),
            min_budget_for_heal=heal_cfg.get("min_budget_for_heal", 500),
        )

        # Estimate remaining budget (rough: tokens left for LLM calls)
        budget_remaining = max(
            0,
            (self.profile.max_reasoning_steps - self.memory.step_count)
            * 500,  # ~500 tokens per step
        )

        all_fixes: list[str] = []
        total_cascaded = 0
        iteration = 0

        while True:
            decision = detector.should_continue(journal, budget_remaining)
            if not decision.continue_healing:
                break

            iteration += 1
            journal.advance_iteration()
            fixes_this_round = 0
            cascades_this_round = 0

            # Prioritise by severity
            unresolved = sorted(
                journal.get_unresolved(),
                key=lambda e: list(ErrorSeverity).index(e.severity),
                reverse=True,
            )

            for error in unresolved[:3]:  # Fix at most 3 per iteration
                fix_attempt = await self._attempt_fix(
                    error,
                    task,
                    context,
                    available_tools,
                )
                if fix_attempt.result in (FixResult.SUCCESS, FixResult.PARTIAL):
                    fixes_this_round += 1
                    all_fixes.append(fix_attempt.strategy)
                    self.memory.learn_fix(error, fix_attempt)

                cascades_this_round += len(fix_attempt.new_errors_discovered)
                budget_remaining -= fix_attempt.tokens_consumed

            total_cascaded += cascades_this_round

            detector.record_iteration(
                IterationSnapshot(
                    iteration=iteration,
                    unresolved_count=journal.get_unresolved_count(),
                    fixed_count=fixes_this_round,
                    cascaded_count=cascades_this_round,
                    tokens_consumed=fixes_this_round * 300,
                )
            )

        final_decision = detector.should_continue(journal, budget_remaining)
        return HealResult(
            iterations=iteration,
            fixed_count=journal.count_by_status(ErrorStatus.FIXED),
            remaining_count=journal.get_unresolved_count(),
            cascaded_count=total_cascaded,
            converged=journal.is_converged(),
            convergence_reason=final_decision.reason,
            fixes_applied=all_fixes,
        )

    async def _attempt_fix(
        self,
        error: ErrorEntry,
        task: str,
        context: str,
        available_tools: list[dict[str, Any]],
    ) -> FixAttempt:
        """Attempt to fix a single error. May discover cascading issues."""
        journal = self.memory.error_journal
        journal.diagnose(error.id, "diagnosing")

        # Check if we have a learned fix pattern
        suggested = self.memory.suggest_fix(error)
        if suggested:
            logger.info(f"  Heal: using learned fix for {error.error_type}: {suggested[:60]}")

        # Ask LLM to diagnose root cause and suggest fix
        error_context = json.dumps(error.context, default=str)[:300]
        prompt = (
            f"An error occurred during task execution.\n\n"
            f"Task: {task[:200]}\n"
            f"Error source: {error.source.value}\n"
            f"Error message: {error.message[:300]}\n"
            f"Error context: {error_context}\n"
        )
        if suggested:
            prompt += f"Previously successful fix for similar errors: {suggested}\n"
        prompt += (
            "\nDiagnose the root cause and suggest a fix strategy.\n"
            "Respond in JSON: {root_cause, fix_strategy, can_fix_with_tools, "
            "tool_to_call, tool_args, potential_cascades}\n"
        )

        try:
            raw = await self.llm_call(
                system_prompt=(
                    "You are a diagnostic expert. Analyze errors, identify root "
                    "causes, and suggest specific fix strategies. Respond in JSON."
                ),
                user_prompt=prompt,
            )
            data = _parse_json_safe(raw)
        except Exception as e:
            logger.warning(f"  Heal: diagnosis LLM failed: {e}")
            journal.mark_wont_fix(error.id, reason=f"diagnosis_failed: {e}")
            return FixAttempt(
                attempt_number=len(error.fix_attempts) + 1,
                strategy="diagnosis_failed",
                result=FixResult.FAILED,
                tokens_consumed=100,
            )

        root_cause = data.get("root_cause", "unknown")
        fix_strategy = data.get("fix_strategy", "retry")
        journal.diagnose(error.id, root_cause)

        # Attempt the fix
        fix_result = FixResult.FAILED
        new_errors: list[str] = []

        if data.get("can_fix_with_tools") and data.get("tool_to_call"):
            # Execute a corrective tool call
            tool_name = data["tool_to_call"]
            tool_args = data.get("tool_args", {})
            try:
                result = await self.tool_call(tool_name, tool_args)
                result_str = str(result)[:500]
                # Check if the tool call succeeded
                if result_str and not result_str.startswith("ERROR"):
                    fix_result = FixResult.SUCCESS
                    self.memory.store_fact(
                        f"heal_fix_{error.id}",
                        f"Fixed {error.error_type} via {tool_name}: {result_str[:200]}",
                    )
                    self.accumulated_content.append(result_str)
                else:
                    fix_result = FixResult.FAILED
            except Exception as e:
                logger.warning(f"  Heal: fix tool call failed: {e}")
                fix_result = FixResult.FAILED
        else:
            # Mark as fixed-by-diagnosis (the understanding itself is the fix)
            fix_result = FixResult.SUCCESS
            self.memory.store_fact(
                f"heal_diagnosis_{error.id}",
                f"Root cause of {error.error_type}: {root_cause}. Strategy: {fix_strategy}",
            )

        # Cascade check
        cascade_errors = await self._cascade_check(error, fix_strategy, context)
        for cascade_err in cascade_errors:
            err_id = journal.record(cascade_err)
            new_errors.append(err_id)

        if new_errors:
            fix_result = FixResult.CASCADED

        attempt = FixAttempt(
            attempt_number=len(error.fix_attempts) + 1,
            strategy=fix_strategy,
            result=fix_result,
            new_errors_discovered=new_errors,
            tokens_consumed=300,
        )
        journal.record_fix(error.id, attempt)
        return attempt

    async def _cascade_check(
        self,
        fixed_error: ErrorEntry,
        fix_strategy: str,
        context: str,
    ) -> list[ErrorEntry]:
        """Proactively check if a fix introduced new issues."""
        prompt = (
            f"I fixed the following error:\n"
            f"Error: {fixed_error.message[:200]}\n"
            f"Root cause: {fixed_error.root_cause or 'unknown'}\n"
            f"Fix applied: {fix_strategy[:200]}\n\n"
            f"What cascading issues might this fix introduce? "
            f"Check for: missing dependencies, broken references, "
            f"type mismatches, config inconsistencies, API contract violations.\n"
            f"Return a JSON list of objects with keys: "
            f"description, category, severity (low/medium/high/critical)\n"
            f"Return an empty list [] if no cascading issues are expected."
        )

        try:
            raw = await self.llm_call(
                system_prompt=(
                    "You are a cascade analysis expert. Given a fix, "
                    "identify potential side effects. Be conservative   "
                    "only report likely issues. Respond with a JSON list."
                ),
                user_prompt=prompt,
            )
            data = _parse_json_safe(raw)

            # Parse cascade list
            cascade_list = data if isinstance(data, list) else data.get("cascades", [])
            if isinstance(data, dict) and not cascade_list:
                # Try to extract from raw response as list
                raw_str = str(raw)
                if raw_str.strip().startswith("["):
                    try:
                        cascade_list = json.loads(raw_str)
                    except json.JSONDecodeError:
                        cascade_list = []

            new_errors: list[ErrorEntry] = []
            for item in cascade_list[:3]:  # Cap at 3 cascades per fix
                if isinstance(item, dict) and item.get("description"):
                    severity_str = item.get("severity", "medium").lower()
                    try:
                        severity = ErrorSeverity(severity_str)
                    except ValueError:
                        severity = ErrorSeverity.MEDIUM

                    new_errors.append(
                        ErrorEntry(
                            source=ErrorSource.CASCADE,
                            error_type=item.get("category", "cascade"),
                            message=item["description"][:300],
                            context={"parent_error": fixed_error.id},
                            severity=severity,
                            estimated_complexity="simple",
                        )
                    )

            return new_errors

        except Exception as e:
            logger.debug(f"  Cascade check failed: {e}")
            return []

    def _get_heal_config(self) -> dict[str, Any]:
        """Load healing config from kernel.yaml."""
        try:
            from shared.prompts import get_kernel_config

            cfg = get_kernel_config("kernel_cell") or {}
            return cfg.get("healing", {})
        except Exception:
            return {}

    # ================================================================ #
    # Phase 7: PACKAGE
    # ================================================================ #

    async def _package(
        self,
        perception: PerceptionResult,
        framing: FramingResult,
    ) -> WorkPackage:
        """
        Phase 7: PACKAGE (The Foundation of v2.0 Output)

        This is the synthesis step   combines all gathered data, analysis,
        and reasoning into a structured WorkPackage containing multiple
        artifacts, tailored to the audience.
        """
        if not self.accumulated_content and not self.memory.all_facts:
            return WorkPackage(
                summary="No data was gathered or analysis produced for this task.",
                overall_confidence=0.0,
            )

        # Gather all material for the LLM
        all_content = "\n\n".join(self.accumulated_content)
        facts_text = "\n".join(f"- {k}: {v[:500]}" for k, v in self.memory.all_facts.items())
        tool_summary = "\n".join(
            f"- {t['tool']}({t.get('args', {})}): {t['result'][:200]}" for t in self.tool_results
        )

        # Consensus Engine (Manager+ levels)
        consensus_cfg = get_kernel_config("kernel_cell.consensus") or {}
        rounds = consensus_cfg.get(f"{self.profile.level.lower()}_rounds", 0)
        
        if rounds > 0:
            try:
                from kernel.logic.consensus import ConsensusEngine
                
                engine = ConsensusEngine(max_rounds=rounds)
                sources_list = []
                for t in self.tool_results:
                     if "url" in t.get("args", {}):
                         sources_list.append({"url": t["args"]["url"], "title": t["tool"]})

                consensus_result = await engine.reach_consensus(
                    query=perception.task_text,
                    facts=[v for k, v in self.memory.all_facts.items()],
                    sources=sources_list,
                )
                
                final_content = consensus_result.get("final_answer", "")
                final_confidence = consensus_result.get("confidence", 0.8)
                
                if final_content:
                    # Format report
                    try:
                         tmpl = get_report_template()
                         sec = tmpl.get("sections", {})
                         
                         if not final_content.startswith("# Research Report"):
                             report = sec.get("title", "# Research Report: {query}").format(query=perception.task_text) + "\n\n"
                             report += sec.get("metadata", "").format(
                                 confidence_pct=f"{final_confidence:.0%}",
                                 sources_count=len(self.tool_results),
                                 facts_count=self.memory.fact_count,
                                 verdict="Consensus Reached"
                             ) + "\n\n"
                             report += sec.get("divider", "---") + "\n\n"
                             report += final_content
                             final_content = report
                    except Exception:
                        pass
                    
                    artifacts = [
                        self.memory.artifacts.create_artifact(
                            id=f"report_{datetime.utcnow().timestamp()}",
                            type=ArtifactType.REPORT,
                            title=f"Research Report: {perception.task_text[:50]}",
                            content=final_content,
                            summary=final_content[:300] + "...",
                            confidence=final_confidence,
                            metadata=ArtifactMetadata(
                                sources=[t.get("tool", "") for t in self.tool_results],
                                data_gaps=framing.unknown_gaps,
                            ),
                            status=ArtifactStatus.PUBLISHED
                        )
                    ]
                    
                    return WorkPackage(
                        summary=final_content[:3000],
                        artifacts=artifacts,
                        overall_confidence=final_confidence,
                        key_findings=["Consensus reached"],
                        metadata={"produced_by": self.profile.level, "steps": self.monitor_count},
                    )

            except Exception as e:
                logger.warning(f"Consensus engine failed: {e}")

        prompt = (
            f"Synthesize the FOLLOWING WORK into a professional Work Package.\n\n"
            f"=== ORIGINAL TASK ===\n{perception.task_text}\n\n"
            f"=== FRAMING ===\n"
            f"Restatement: {framing.restatement}\n"
            f"Assumptions: {', '.join(framing.assumptions)}\n"
            f"Constraints: {', '.join(framing.constraints)}\n\n"
            f"=== GATHERED DATA ===\n{facts_text}\n\n"
            f"=== ANALYSIS SECTIONS ===\n{all_content[:4000]}\n\n"
            f"=== TOOL USAGE ===\n{tool_summary[:1000]}\n\n"
            f"=== INSTRUCTIONS ===\n"
            f"Your output MUST be a JSON object conforming to the WorkPackage schema.\n"
            f"Divide the work into 2-5 distinct artifacts (e.g., a formal report, a dataset summary, recommendations).\n\n"
            f"JSON STRUCTURE:\n"
            f"{{\n"
            f'  "summary": "Executive summary of the whole package",\n'
            f'  "artifacts": [\n'
            f"    {{\n"
            f'      "id": "unique_id",\n'
            f'      "type": "report|analysis|dataset|recommendation",\n'
            f'      "title": "Title of artifact",\n'
            f'      "content": "Full markdown content",\n'
            f'      "confidence": 0.9,\n'
            f'      "metadata": {{ "sources": [...], "data_gaps": [...] }}\n'
            f"    }}\n"
            f"  ],\n"
            f'  "overall_confidence": 0.85,\n'
            f'  "key_findings": ["finding 1", ...]\n'
            f"}}\n"
        )

        try:
            raw_response = await self.llm_call(
                system_prompt=(
                    f"You are a {self.profile.level}-level expert synthesiser. "
                    f"Your job is to transform raw research into a high-quality Work Package. "
                    f"Respond ONLY with valid JSON."
                ),
                user_prompt=prompt,
            )
            data = _parse_json_safe(raw_response)

            # Create the work package objects
            artifacts: list[Artifact] = []
            for art_data in data.get("artifacts", []):
                meta_data = art_data.get("metadata", {})
                metadata_obj = ArtifactMetadata(
                    sources=meta_data.get("sources", []),
                    data_gaps=meta_data.get("data_gaps", []),
                    citations=meta_data.get("citations", []),
                    assumptions=meta_data.get("assumptions", []),
                )

                art = self.memory.artifacts.create_artifact(
                    id=art_data.get("id", f"art_{datetime.utcnow().timestamp()}"),
                    type=ArtifactType(art_data.get("type", "report")),
                    title=art_data.get("title", "Untitled Artifact"),
                    content=art_data.get("content", ""),
                    summary=art_data.get("summary", ""),
                    confidence=art_data.get("confidence", 0.5),
                    metadata=metadata_obj,
                )
                # Mark as published immediately for the final package
                art.status = ArtifactStatus.PUBLISHED
                artifacts.append(art)

            package = WorkPackage(
                summary=data.get("summary", "Analysis complete."),
                artifacts=artifacts,
                overall_confidence=data.get("overall_confidence", 0.5),
                key_findings=data.get("key_findings", []),
                recommendations=data.get("recommendations", []),
                metadata={"produced_by": self.profile.level, "steps": self.monitor_count},
            )
            return package

        except Exception as e:
            logger.error(f"Structured packaging failed: {e}")
            # Fallback to a simple package
            return WorkPackage(
                summary=f"Analysis encountered error during packaging: {e}",
                artifacts=[
                    self.memory.artifacts.create_artifact(
                        id="fallback_report",
                        type=ArtifactType.REPORT,
                        title="Incomplete Report",
                        content=all_content or "No content available.",
                    )
                ],
                overall_confidence=0.1,
            )

    # ================================================================ #
    # Helpers
    # ================================================================ #

    def _build_execute_system_prompt(self, has_tools: bool = False) -> str:
        """Build the system prompt for execute steps.

        Args:
            has_tools: Whether tools are available for this execution. When True,
                       injects a mandatory tool-use directive so the LLM cannot
                       fabricate answers from memory.
        """
        base = get_agent_prompt("kernel_executor") or (
            "You are an autonomous research agent executing tasks step by step."
        )
        modifier = self.profile.system_prompt_modifier
        reasoning = self.profile.get_reasoning_instruction()
        prompt = f"{base}\n\n{modifier}\n\nREASONING APPROACH:\n{reasoning}"

        if has_tools:
            exec_cfg = get_kernel_config("kernel_cell_execute") or {}
            if exec_cfg.get("min_tool_calls_before_synthesis", 1) > 0:
                prompt += (
                    "\n\nCRITICAL RULE: You have tools available. You MUST call at least "
                    "one tool to gather real external data before synthesizing or completing. "
                    "Reasoning from memory alone is a failure. Use call_tool."
                )

        return prompt

    def _build_step_prompt(
        self,
        task: str,
        context: str,
        step_idx: int,
        total_steps: int,
        plan: PlanResult,
        tools_summary: str,
        reasoning_instruction: str,
        nudge_tool_use: bool = False,
    ) -> str:
        """Build the user prompt for a single execution step.

        Args:
            nudge_tool_use: When True, injects a warning that tool calls are
                            required and none have been made yet.
        """
        wm_summary = self.memory.compress(max_chars=1500)

        current_step = "Continue working"
        if step_idx < len(plan.steps):
            current_step = plan.steps[step_idx]

        prompt_parts = [
            f"=== TASK ===\n{task[:500]}",
            f"\n=== PLAN ===\nApproach: {plan.approach}",
            f"Current step ({step_idx + 1}/{total_steps}): {current_step}",
        ]

        if wm_summary:
            prompt_parts.append(f"\n=== WORKING MEMORY ===\n{wm_summary}")

        if self.accumulated_content:
            recent = "\n".join(self.accumulated_content[-2:])[:800]
            prompt_parts.append(f"\n=== RECENT WORK ===\n{recent}")

        if tools_summary:
            prompt_parts.append(f"\n=== AVAILABLE TOOLS ===\n{tools_summary}")

        # Nudge injection: fire when tools are available but not yet used
        if nudge_tool_use and tools_summary:
            prompt_parts.append(
                "\n⚠️ NO TOOL CALLS MADE YET. You MUST use call_tool on this step "
                "to gather real data. Do not analyze from memory."
            )

        force_synthesis = self.memory.get_note("force_synthesis")
        if force_synthesis:
            prompt_parts.append(f"\n  {force_synthesis}. Move to synthesis/complete.")

        prompt_parts.append(
            "\n=== RESPOND ===\n"
            "JSON with keys: thought, action (call_tool|analyze|synthesize|complete), "
            "action_input, confidence (0.0-1.0)\n"
            'For call_tool: action_input = {"tool": "<name>", "arguments": {"<param*>": "<value>", ...}}\n'
            "Use exact parameter names from AVAILABLE TOOLS. Parameters marked * are required."
        )

        return "\n".join(prompt_parts)

    def _format_tools(self, tools: list[dict[str, Any]]) -> str:
        """Format tool list with parameter schema for LLM prompts.

        Shows each tool as:  - name(param*:type, param:type): description
        Parameters marked * are required. Falls back to name-only when no schema.
        """
        if not tools:
            return ""
        lines = []
        for t in tools[:15]:
            name = t.get("name", "?")
            desc = t.get("description", "")[:120]
            schema = t.get("inputSchema", {})
            properties = schema.get("properties", {})
            required = set(schema.get("required", []))
            if properties:
                param_parts = []
                for p_name, p_meta in properties.items():
                    p_type = p_meta.get("type", "any")
                    req_marker = "*" if p_name in required else ""
                    param_parts.append(f"{p_name}{req_marker}:{p_type}")
                lines.append(f"- {name}({', '.join(param_parts)}): {desc}")
            else:
                lines.append(f"- {name}: {desc}")
        return "\n".join(lines)

    def _assess_final_quality(self) -> str:
        """Quick final quality assessment based on working memory signals.

        Applies a config-driven quality penalty when tools were available
        but no tool calls were made — prevents 91% confidence "Accept" with
        0 actual data gathering (restores old orchestrator's quality gate).
        """
        if not self.accumulated_content:
            return "poor"

        confidence = self.memory.overall_confidence
        facts = self.memory.fact_count
        content_length = sum(len(c) for c in self.accumulated_content)

        # Tool-call quality gate: penalize fabricated answers
        exec_cfg = get_kernel_config("kernel_cell_execute") or {}
        penalty_enabled = exec_cfg.get("tool_call_quality_penalty_enabled", True)
        min_calls = exec_cfg.get("min_tool_calls_before_synthesis", 1)
        tools_were_available = getattr(self, "_tools_available", False)

        if penalty_enabled and tools_were_available and self.tool_call_count < min_calls:
            logger.warning(
                f"Quality penalty: {self.tool_call_count} tool calls "
                f"(min={min_calls}) with tools available — capping at 'poor'"
            )
            return "poor"

        if confidence >= 0.7 and facts >= 3 and content_length > 500:
            return "good"
        if confidence >= 0.5 and (facts >= 1 or content_length > 200):
            return "adequate"
        return "poor"

    # ================================================================ #
    # Communication Helpers (v2.0)
    # ================================================================ #

    async def _resolve_clarifications(
        self,
        questions: list[str],
    ) -> list[str]:
        """
        Attempt to resolve clarification questions via the communicator.

        Asks the parent each question. Returns a list of answers for
        questions that got responses (empty list if none answered).
        """
        if not self.comm:
            return []

        answers: list[str] = []
        for question in questions[:3]:  # Cap at 3 to avoid budget drain
            answer = await self.comm.ask_parent(
                question=question,
                context=self.memory.compress(max_chars=500),
            )
            if answer:
                answers.append(answer)
                # The communicator already stores in working memory
                logger.info(f"  Clarification answered: {question[:50]}   {answer[:50]}")
            else:
                logger.info(f"  Clarification unanswered: {question[:50]}")

        return answers

    async def _report_progress(
        self,
        progress_pct: float,
        task: str,
        step_idx: int,
    ) -> None:
        """
        Report execution progress to the parent via the communicator.

        Only fires if a communicator is attached and has budget remaining.
        """
        if not self.comm:
            return

        current_work = (
            f"Step {step_idx}: "
            f"{self.accumulated_content[-1][:100] if self.accumulated_content else 'working...'}"
        )

        try:
            await self.comm.report_progress(
                progress_pct=progress_pct,
                current_work=current_work,
                findings_so_far=self.memory.focus_summary,
            )
        except Exception as e:
            # Progress reporting is best-effort; never crash the cycle
            logger.debug(f"Progress report failed: {e}")


# ============================================================================
# Cycle Output
# ============================================================================


class CycleOutput(BaseModel):
    """Complete output from a cognitive cycle run."""

    # Primary deliverable (v2.0 uses WorkPackage)
    content: str = Field(description="Legacy string content (for backward compatibility)")
    work_package: WorkPackage | None = None

    #   Control signals  
    needs_delegation: bool = Field(default=False)
    needs_clarification: bool = Field(default=False)
    clarification_questions: list[str] = Field(default_factory=list)

    #   Phase results  
    perception: PerceptionResult | None = None
    framing: FramingResult | None = None
    plan: PlanResult | None = None

    #   Quality  
    quality: str = Field(default="not_assessed")

    #   Metrics  
    tool_results: list[dict[str, Any]] = Field(default_factory=list)
    memory_state: dict[str, Any] = Field(default_factory=dict)
    elapsed_ms: float = Field(default=0.0)
    facts_gathered: int = Field(default=0)
    decisions_made: int = Field(default=0)


# ============================================================================
# Utility Functions
# ============================================================================


def _extract_entities(text: str) -> list[str]:
    """
    Extract key entities from text using simple heuristics.

    Looks for capitalised words, quoted strings, and known patterns.
    This is a cheap fallback for when we don't want an LLM call.
    """
    entities: list[str] = []
    words = text.split()
    for i, word in enumerate(words):
        cleaned = word.strip(".,!?;:\"'()[]{}").strip()
        if not cleaned:
            continue
        # Capitalised words (not at sentence start)
        if i > 0 and cleaned[0].isupper() and len(cleaned) > 1:
            entities.append(cleaned)
        # All-caps words (acronyms like EV, AI, GDP)
        if cleaned.isupper() and 2 <= len(cleaned) <= 6:
            entities.append(cleaned)

    # Deduplicate while preserving order
    seen: set[str] = set()
    unique: list[str] = []
    for e in entities:
        if e.lower() not in seen:
            seen.add(e.lower())
            unique.append(e)
    return unique[:10]


def _parse_json_safe(raw: Any) -> dict[str, Any]:
    """
    Parse LLM output as JSON, handling common formatting issues.

    Handles:
    - Pydantic model objects (with .model_dump())
    - Raw strings (with json.loads())
    - Markdown-wrapped JSON (```json ... ```)
    - Already parsed dicts
    """
    if isinstance(raw, dict):
        return raw

    if hasattr(raw, "model_dump"):
        return raw.model_dump()

    if isinstance(raw, str):
        text = raw.strip()
        # Remove markdown code fences
        if text.startswith("```"):
            lines = text.split("\n")
            # Remove first and last line (the fences)
            lines = [l for l in lines if not l.strip().startswith("```")]
            text = "\n".join(lines).strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Try to find JSON object in the text
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                try:
                    return json.loads(text[start:end])
                except json.JSONDecodeError:
                    pass

    return {"raw": str(raw)}


def _elapsed_ms(start: datetime) -> float:
    """Calculate elapsed milliseconds from start to now."""
    return (datetime.utcnow() - start).total_seconds() * 1000
