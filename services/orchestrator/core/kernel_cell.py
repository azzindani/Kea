"""
The Kernel Cell — Universal Recursive Processing Unit.

Every level of the corporate hierarchy — from Board to Intern — runs this
exact same code. Only the configuration differs: identity, tools, knowledge,
budget, quality bar, and now **cognitive profile**.

This is the CORE module of Kea's kernel. It wires together:
- KnowledgeEnhancedInference → for context engineering per inference
- KnowledgeRetriever → for skill/rule/procedure retrieval
- ConsensusEngine → for per-level quality assurance
- Organization → for role resolution during delegation
- WorkBoard → for kanban-style task tracking
- ScoreCard → for multi-dimensional quality scoring
- StdioEnvelope → for structured I/O contracts
- Output Schemas → for validated LLM output parsing
- CognitiveCycle → for the full perceive→frame→plan→execute↔monitor→package loop
- WorkingMemory → for structured, human-inspired state tracking
- CognitiveProfile → for level-aware reasoning styles
- CellCommunicator → for multi-directional inter-cell messaging
- MessageBus → for async message routing between cells
- DelegationProtocol → for iterative, review-driven delegation

Features (v2.0.1 — Brain + Communication + Iterative Delegation):
- Full cognitive cycle replaces flat ReAct loop
- Structured working memory per cell (focus, hypotheses, decisions)
- Level-aware cognitive profiles (intern → board)
- Continuous self-monitoring during execution (not just post-hoc)
- Recursive delegation: spawn_child() creates child cells
- Budget-controlled execution: TokenBudget prevents infinite recursion
- Quality gates: per-level thresholds with configurable failure actions
- Contribution tracking: who produced what in the final output
- Multi-directional communication: clarification, progress, sharing, escalation
- Peer-to-peer data exchange between sibling cells
- Communication budget: token-controlled messaging (15% of task budget)
- Iterative delegation: multi-round review→feedback→revision loop
- Conflict detection: contradictions between sibling outputs found and resolved
- Synthesis notes: reviewer instructions carried into final synthesis
"""

from __future__ import annotations

import asyncio
import json
import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from services.orchestrator.core.cell_communicator import CellCommunicator
from services.orchestrator.core.cognitive_cycle import CognitiveCycle, CycleOutput
from services.orchestrator.core.cognitive_profiles import (
    CognitiveProfile,
    child_level_for,
    get_cognitive_profile,
)
from services.orchestrator.core.complexity import classify_complexity
from services.orchestrator.core.degradation import get_degrader
from services.orchestrator.core.delegation_protocol import (
    DelegationProtocol,
    DelegationState,
)
from services.orchestrator.core.error_journal import (
    ErrorStatus,
    FixAttempt,
    FixResult,
)
from services.orchestrator.core.inference_context import (
    AgentIdentity,
    InferenceContext,
    KnowledgeEnhancedInference,
    get_inference_engine,
)
from services.orchestrator.core.message_bus import (
    MessageChannel,
    get_message_bus,
    reset_message_bus,
)
from services.orchestrator.core.output_schemas import (
    Artifact,
    ArtifactMetadata,
    ArtifactStatus,
    ComplexityAssessment,
    PlannerOutput,
    ProcessingMode,
    SubTask,
    WorkPackage,
)
from services.orchestrator.core.resource_governor import (
    EscalationSeverity,
    ExecutionGuard,
    ResourceGovernor,
)
from services.orchestrator.core.score_card import (
    ContributionLedger,
    ScoreCard,
    get_quality_gate,
)
from services.orchestrator.core.stdio_envelope import (
    Constraints,
    EnvelopeMetadata,
    Failure,
    Instruction,
    MessageType,
    StderrEnvelope,
    StdinEnvelope,
    StdioEnvelope,
    StdoutEnvelope,
    TaskContext,
    Warning,
    WarningSeverity,
)
from services.orchestrator.core.work_unit import (
    WorkType,
    WorkUnit,
    get_work_board,
)
from services.orchestrator.core.working_memory import WorkingMemory
from shared.config import get_settings
from shared.knowledge.retriever import KnowledgeRetriever, get_knowledge_retriever
from shared.llm import LLMConfig
from shared.llm.provider import LLMMessage, LLMRole
from shared.logging import get_logger
from shared.prompts import get_agent_prompt, get_kernel_config
from shared.service_registry import ServiceName, ServiceRegistry

logger = get_logger(__name__)


# ============================================================================
# Token Budget — Recursion Control
# ============================================================================


@dataclass
class TokenBudget:
    """
    Budget-based recursion control.

    Prevents infinite delegation by tracking token consumption
    and enforcing depth limits. Parent allocates fractions to children.

    Defaults are loaded from ``kernel.yaml`` when sentinel values (0) are used.
    When explicit non-zero values are provided (e.g. by ``run_kernel()`` or
    ``allocate_fraction()``), those values take precedence.
    """

    max_tokens: int = 0
    remaining: int = 0
    depth: int = 0
    max_depth: int = 0

    def __post_init__(self) -> None:
        """Load defaults from kernel.yaml for any fields left at sentinel value."""
        if self.max_tokens == 0:
            cfg = get_kernel_config("kernel_cell.budget.default_max_tokens")
            self.max_tokens = int(cfg) if cfg else 30_000
        if self.remaining == 0:
            self.remaining = self.max_tokens
        if self.max_depth == 0:
            cfg = get_kernel_config("kernel_cell.recursion.max_depth")
            self.max_depth = int(cfg) if cfg else 5

    def allocate_fraction(
        self,
        fraction: float,
        min_tokens: int = 500,
    ) -> TokenBudget:
        """Allocate a fraction of remaining budget to a child cell."""
        allocated = max(int(self.remaining * fraction), min_tokens)
        allocated = min(allocated, self.remaining)  # Can't exceed remaining
        self.remaining -= allocated

        child_budget = TokenBudget(
            max_tokens=allocated,
            remaining=allocated,
            depth=self.depth + 1,
            max_depth=self.max_depth,
        )
        return child_budget

    def consume(self, tokens: int) -> None:
        """Record token consumption."""
        self.remaining = max(0, self.remaining - tokens)

    @property
    def can_delegate(self) -> bool:
        """Can this cell still spawn children?"""
        return self.depth < self.max_depth and self.remaining > 2000

    @property
    def has_remaining(self) -> bool:
        """Is there enough budget for another iteration?"""
        return self.remaining > 500

    @property
    def utilization(self) -> float:
        """Budget utilization (0.0 = unused, 1.0 = exhausted)."""
        if self.max_tokens == 0:
            return 1.0
        return 1.0 - (self.remaining / self.max_tokens)


# ============================================================================
# Kernel Cell State
# ============================================================================


class CellState(BaseModel):
    """Internal state of a kernel cell during processing."""

    # Reasoning chain
    reasoning_steps: list[dict[str, Any]] = Field(default_factory=list)
    current_step: int = Field(default=0)
    max_steps: int = Field(default=15)

    # Tool execution history
    tool_executions: list[dict[str, Any]] = Field(default_factory=list)

    # Accumulated artifacts
    artifacts: dict[str, Any] = Field(default_factory=dict)

    # Status
    status: str = Field(default="thinking")  # thinking | executing | delegating | complete | failed

    # Child results
    child_results: list[StdioEnvelope] = Field(default_factory=list)


# ============================================================================
# The Kernel Cell
# ============================================================================


class KernelCell:
    """
    The Universal Employee — recursive kernel processing unit (v2.0).

    Every level of the hierarchy runs this exact same code. The
    **cognitive profile** modulates HOW the cell thinks:
    - Interns do direct lookups with minimal reasoning
    - Staff follow procedures with self-checks
    - Senior Staff do deep analysis with hypothesis tracking
    - Managers plan, delegate, and review
    - Directors/VPs orchestrate multi-team work
    - C-Suite synthesizes across domains

    Phases (v2.0 Cognitive Cycle):
        1. INTAKE — Parse instruction, load context and knowledge
        2. ASSESS — Heuristic-first complexity → solo vs. delegation
        3. EXECUTE — Full cognitive cycle (perceive→frame→plan→execute↔monitor→package)
                     or spawn children (delegation)
        4. QUALITY — Continuous monitoring + post-hoc quality gate
        5. OUTPUT — Package result as StdioEnvelope with working memory metadata

    Usage:
        cell = KernelCell(
            identity=AgentIdentity(role="financial_analyst", level="staff"),
            tool_executor=my_tool_executor,
        )

        input_envelope = StdioEnvelope(
            stdin=StdinEnvelope(
                instruction=Instruction(text="Analyze AAPL quarterly earnings")
            )
        )

        output_envelope = await cell.process(input_envelope)
    """

    def __init__(
        self,
        identity: AgentIdentity,
        tool_executor: Callable[[str, dict], Awaitable[Any]],
        knowledge_retriever: KnowledgeRetriever | None = None,
        inference_engine: KnowledgeEnhancedInference | None = None,
        parent: KernelCell | None = None,
        budget: TokenBudget | None = None,
        model: str | None = None,
    ) -> None:
        self.cell_id = str(uuid.uuid4())[:8]
        self.identity = identity
        self.tool_executor = tool_executor
        self.knowledge = knowledge_retriever or get_knowledge_retriever()
        self.engine = inference_engine or get_inference_engine()
        self.parent = parent
        self.budget = budget or TokenBudget()

        # LLM setup
        settings = get_settings()
        self.model = model or settings.models.planner_model

        # ── Brain Upgrade (v2.0) ──────────────────────────────────────
        # Cognitive profile: HOW this cell thinks (level-aware)
        self.cognitive_profile: CognitiveProfile = get_cognitive_profile(
            identity.level,
        )

        # Working memory: structured state instead of flat strings
        self.working_memory = WorkingMemory(
            cell_id=self.cell_id,
            max_focus=self.cognitive_profile.max_reasoning_steps,
        )

        # ── Communication Network (v2.0) ──────────────────────────────
        # Communicator: multi-directional messaging to parent/peers/children
        self.comm = CellCommunicator(
            cell_id=self.cell_id,
            memory=self.working_memory,
            total_budget=budget.max_tokens if budget else 30_000,
            parent_id=parent.cell_id if parent else "",
            peer_group="",  # Set by parent during _spawn_child
        )

        self.last_work_package: WorkPackage | None = None

        # State (legacy, kept for backward compatibility)
        self.state = CellState()
        self.score_card = ScoreCard(
            cell_id=self.cell_id,
            level=identity.level,
            role=identity.role,
            domain=identity.domain,
        )
        self.children: list[KernelCell] = []
        self.contribution = ContributionLedger(output_id=self.cell_id)

        # Work tracking (wires existing WorkBoard)
        self.board = get_work_board()
        self._work_unit: WorkUnit | None = None

        # Timing
        self._start_time: datetime | None = None

        # Config cache (avoid repeated YAML loads)
        self._complexity_modes: dict[str, str] | None = None

        # ── Resource Governance (Phase 4) ─────────────────────────────
        # Governor: manages budgets and escalations for children
        async def _governor_llm_call(system_prompt: str, user_prompt: str) -> str:
            messages = [
                LLMMessage(role=LLMRole.SYSTEM, content=system_prompt),
                LLMMessage(role=LLMRole.USER, content=user_prompt),
            ]
            response = await self.engine.complete(
                messages,
                LLMConfig(model=self.model, temperature=0.3, max_tokens=1000),
            )
            return response.content

        self.governor = ResourceGovernor(
            parent_cell_id=self.cell_id,
            total_budget=self.budget.remaining,
            llm_call=_governor_llm_call,
            bus=get_message_bus(),
        )

    # ================================================================== #
    # Phase 0: Main Entry Point
    # ================================================================== #

    async def process(self, envelope: StdioEnvelope) -> StdioEnvelope:
        """
        The Universal Processing Loop.

        Every employee — CEO to intern — runs this exact loop.

        v2.0.1 (Phase 4): Wrapped with ExecutionGuard for pre-flight
        validation, execution tracking, and post-execution audit.
        """
        self._start_time = datetime.utcnow()

        logger.info(
            f"🧠 KernelCell [{self.identity.level}/{self.identity.role}] "
            f"(depth={self.budget.depth}) processing..."
        )

        # Track work unit on the shared kanban board
        task_title = ""
        if envelope.stdin:
            task_title = envelope.stdin.instruction.text[:100]

        self._work_unit = WorkUnit.create(
            title=task_title or f"Cell {self.cell_id}",
            work_type=WorkType.ANALYSIS,
            description=f"KernelCell [{self.identity.level}/{self.identity.role}]",
        )
        self.board.add(self._work_unit)
        self._work_unit.assign(agent_id=self.cell_id)
        self._work_unit.start()

        # ── Execution Guard (Phase 4) ────────────────────────────────
        guard = ExecutionGuard(
            cell_id=self.cell_id,
            budget_max=self.budget.max_tokens,
            budget_remaining=self.budget.remaining,
            max_execution_ms=60_000,
            depth=self.budget.depth,
            max_depth=self.budget.max_depth,
        )

        if not guard.can_execute():
            logger.warning(f"Cell {self.cell_id}: ExecutionGuard rejected — {guard._warnings}")
            if self._work_unit:
                self._work_unit.fail("Pre-flight check failed")
            return self._package_error(
                f"Pre-flight check failed: {'; '.join(guard._warnings)}",
                task_title,
            )

        # ── Graceful Degradation (Phase 4) ───────────────────────────
        degrader = get_degrader()

        try:
            async with degrader.throttle():
                async with guard:
                    # Phase 1: INTAKE
                    task_text, context = await self._intake(envelope)

                    # Phase 2: ASSESS complexity (heuristic-first, saves LLM calls)
                    processing_mode = await self._assess_complexity(task_text, context)

                    # Phase 3: EXECUTE
                    if processing_mode in (ProcessingMode.DIRECT, ProcessingMode.SOLO):
                        result_content = await self._execute_solo(task_text, context, envelope)
                    elif self.budget.can_delegate:
                        result_content = await self._execute_delegation(
                            task_text, context, envelope
                        )
                    else:
                        # Budget exhausted, fall back to solo
                        logger.warning(
                            f"Cell {self.cell_id}: Budget too low for delegation, "
                            f"falling back to solo execution"
                        )
                        result_content = await self._execute_solo(task_text, context, envelope)

                    # Phase 3.5: HEAL (Recursive Self-Healing)
                    if self._should_heal():
                        result_content = await self._execute_heal(
                            task_text,
                            result_content,
                            context,
                            envelope,
                        )

                    # Phase 4: QUALITY ASSURANCE
                    scored_result = await self._quality_check(result_content, task_text)

                    # Phase 5: OUTPUT
                    self._work_unit.complete("Quality gate passed")

                    # Store execution audit in working memory
                    self.working_memory.store_fact(
                        "execution_audit",
                        str(guard.get_audit()),
                    )

                    return self._package_output(scored_result, task_text)

        except Exception as e:
            logger.error(f"Cell {self.cell_id} failed: {e}")
            if self._work_unit:
                self._work_unit.fail(str(e))
            return self._package_error(str(e), task_title)

        finally:
            # Clean up communication registration
            self.comm.cleanup()

    # ================================================================== #
    # Phase 1: INTAKE
    # ================================================================== #

    async def _intake(
        self,
        envelope: StdioEnvelope,
    ) -> tuple[str, InferenceContext]:
        """Parse instruction and build inference context with knowledge."""
        task_text = ""
        domain_hints: list[str] = []

        if envelope.stdin:
            task_text = envelope.stdin.instruction.text
            domain_hints = envelope.stdin.context.domain_hints

        # Build inference context
        context = InferenceContext(
            identity=self.identity,
            skill_query=task_text,
            domain_filter=self.identity.domain if self.identity.domain != "general" else None,
            quality_bar=self._get_quality_bar(envelope),
            task_description=task_text,
            parent_cell_id=self.parent.cell_id if self.parent else "",
        )

        logger.info(
            f"Cell {self.cell_id} intake: task='{task_text[:60]}...' domain={self.identity.domain}"
        )

        return task_text, context

    # ================================================================== #
    # Phase 2: ASSESS
    # ================================================================== #

    async def _assess_complexity(
        self,
        task_text: str,
        context: InferenceContext,
    ) -> ProcessingMode:
        """
        Determine how to process this task: solo or delegation.

        Optimization: Uses the existing heuristic classifier (zero LLM cost)
        as a fast-path. Only falls back to LLM assessment for ambiguous
        MEDIUM-tier queries where delegation vs solo is non-obvious.
        """
        # If budget doesn't allow delegation, force solo
        if not self.budget.can_delegate:
            return ProcessingMode.SOLO

        # ── Fast path: use existing heuristic classifier (FREE) ──────────
        heuristic = classify_complexity(task_text)
        tier_name = heuristic.tier.value  # trivial | low | medium | high | extreme

        # Load the tier→mode mapping from config (cached)
        if self._complexity_modes is None:
            self._complexity_modes = get_kernel_config("kernel_cell.complexity_mode_mapping") or {}

        mapped_mode_str = self._complexity_modes.get(tier_name)

        # For clear-cut tiers, skip the LLM entirely
        if tier_name in ("trivial", "low") and mapped_mode_str:
            mode = ProcessingMode(mapped_mode_str)
            logger.info(
                f"Cell {self.cell_id} complexity (heuristic): "
                f"tier={tier_name} → {mode.value} [FREE]"
            )
            return mode

        if tier_name in ("high", "extreme") and mapped_mode_str:
            mode = ProcessingMode(mapped_mode_str)
            logger.info(
                f"Cell {self.cell_id} complexity (heuristic): "
                f"tier={tier_name} → {mode.value} [FREE]"
            )
            return mode

        # ── Slow path: MEDIUM tier is ambiguous → ask the LLM ────────────
        try:
            messages = [
                LLMMessage(
                    role=LLMRole.SYSTEM,
                    content=(
                        "You assess task complexity. Respond with JSON.\n"
                        "Consider: How many distinct sub-tasks? "
                        "How many tool calls needed? "
                        "Does it require multiple domains of expertise?"
                    ),
                ),
                LLMMessage(
                    role=LLMRole.USER,
                    content=(
                        f"Task: {task_text}\n"
                        f"My level: {self.identity.level}\n"
                        f"My domain: {self.identity.domain}\n"
                        f"Budget remaining: {self.budget.remaining} tokens\n"
                        f"Depth: {self.budget.depth}/{self.budget.max_depth}\n"
                        f"Heuristic assessment: {tier_name} "
                        f"(composite={heuristic.composite:.2f}, "
                        f"entities={heuristic.entity_count})"
                    ),
                ),
            ]

            config = LLMConfig(
                model=self.model,
                temperature=0.1,
                max_tokens=512,
            )

            result = await self.engine.structured_complete(
                messages,
                config,
                context,
                output_schema=ComplexityAssessment,
            )

            if isinstance(result, ComplexityAssessment):
                mode = result.processing_mode
                logger.info(
                    f"Cell {self.cell_id} complexity (LLM): "
                    f"tier={result.tier} mode={mode.value} "
                    f"[heuristic was: {tier_name}]"
                )
                self.budget.consume(50)  # Assessment cost
                return mode

        except Exception as e:
            logger.warning(f"LLM complexity assessment failed: {e}")

        # Final fallback: use the heuristic mapping or default to SOLO
        fallback_str = mapped_mode_str or "solo"
        return ProcessingMode(fallback_str)

    # ================================================================== #
    # Phase 3a: SOLO Execution (Full Cognitive Cycle)
    # ================================================================== #

    async def _execute_solo(
        self,
        task_text: str,
        context: InferenceContext,
        envelope: StdioEnvelope,
    ) -> str:
        """
        Execute task using the full cognitive cycle.

        Replaces the flat ReAct loop with:
            Perceive → Frame → Plan → [Execute ↔ Monitor → Adapt] → Package

        The cognitive profile (based on organizational level) modulates
        how many phases are executed and how deeply:
        - Interns skip framing, use direct lookup
        - Senior staff do full deep analysis with hypothesis tracking
        - Managers plan and review more than they execute
        """
        logger.info(
            f"Cell {self.cell_id}: Solo execution via CognitiveCycle "
            f"(profile={self.cognitive_profile.level}, "
            f"style={self.cognitive_profile.reasoning_style.value})"
        )

        # Build the cognitive cycle with level-aware profile
        cycle = CognitiveCycle(
            profile=self.cognitive_profile,
            memory=self.working_memory,
            llm_call=self._cognitive_llm_call,
            tool_call=self._execute_tool_for_cycle,
            task_id=self.cell_id,
            communicator=self.comm,
        )

        # Discover available tools via MCP Host REST API
        available_tools: list[dict[str, Any]] = []
        try:
            from services.orchestrator.core.tool_bridge import discover_tools

            available_tools = await discover_tools(timeout=5.0)
            if available_tools:
                logger.info(f"Cell {self.cell_id}: Discovered {len(available_tools)} tools")
        except Exception as e:
            logger.debug(f"Cell {self.cell_id}: Tool discovery skipped: {e}")

        # Build context string from envelope
        context_str = ""
        if envelope.stdin and envelope.stdin.context:
            ctx = envelope.stdin.context
            if ctx.domain_hints:
                context_str += f"Domain: {', '.join(ctx.domain_hints)}\n"
            if ctx.parent_task_id:
                context_str += f"Parent task: {ctx.parent_task_id}\n"

        # Run the full cognitive cycle
        cycle_output: CycleOutput = await cycle.run(
            task=task_text,
            context=context_str,
            available_tools=available_tools,
        )

        # Handle delegation signal from the cognitive cycle
        if cycle_output.needs_delegation and self.budget.can_delegate:
            logger.info(f"Cell {self.cell_id}: Cognitive cycle recommends delegation")
            return await self._execute_delegation(task_text, context, envelope)

        # Transfer working memory signals to the score card
        wm_state = cycle_output.memory_state
        self.score_card.self_confidence = wm_state.get("overall_confidence", 0.5)
        self.score_card.facts_contributed = wm_state.get("facts_count", 0)
        if cycle_output.framing:
            self.score_card.assumptions = cycle_output.framing.assumptions[:5]
            self.score_card.data_gaps = cycle_output.framing.unknown_gaps[:5]

        # Record step count in legacy state
        self.state.current_step = wm_state.get("step_count", 0)

        # Record tool calls in legacy state
        for tool_result in cycle_output.tool_results:
            self.state.tool_executions.append(
                {
                    "tool": tool_result.get("tool", ""),
                    "arguments": tool_result.get("args", {}),
                    "success": True,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )

        # Budget accounting (approximate)
        estimated_tokens = int(cycle_output.elapsed_ms / 10)  # Rough heuristic
        self.budget.consume(max(estimated_tokens, 200))

        # Store work package for later packaging (v2.0)
        if cycle_output.work_package:
            self.last_work_package = cycle_output.work_package

        # ── Rerank facts by relevance to original query ───────────────
        await self._rerank_facts(task_text)

        # If cycle produced content, use it; otherwise fall back to synthesis
        if cycle_output.content:
            return cycle_output.content

        # Fallback synthesis if cognitive cycle produced no content
        logger.warning(
            f"Cell {self.cell_id}: Cognitive cycle produced no content, falling back to synthesis"
        )
        return await self._synthesize(
            task_text,
            "\n".join(f"- {k}: {v}" for k, v in self.working_memory.all_facts.items())
            or "No data gathered",
            context,
        )

    async def _cognitive_llm_call(
        self,
        system_prompt: str = "",
        user_prompt: str = "",
    ) -> Any:
        """
        LLM call adapter for the CognitiveCycle.

        Bridges the cycle's simple (system_prompt, user_prompt) → str
        interface to the engine's full message-based API.
        """
        messages = [
            LLMMessage(role=LLMRole.SYSTEM, content=system_prompt),
            LLMMessage(role=LLMRole.USER, content=user_prompt),
        ]
        config = LLMConfig(
            model=self.model,
            temperature=0.3,
            max_tokens=4096,
        )
        response = await self.engine.complete(messages, config)
        return response.content

    async def _execute_tool_for_cycle(
        self,
        tool_name: str,
        tool_args: dict[str, Any],
    ) -> Any:
        """
        Tool execution adapter for the CognitiveCycle.

        Wraps the existing tool_executor to also record in CellState.
        """
        return await self._execute_tool(tool_name, tool_args)

    # ================================================================== #
    # Phase 3b: DELEGATION Execution (Recursive)
    # ================================================================== #

    async def _execute_delegation(
        self,
        task_text: str,
        context: InferenceContext,
        envelope: StdioEnvelope,
    ) -> str:
        """
        Execute task by planning and delegating to child cells.

        v2.0: Children are registered as peers on the message bus.
        Incoming messages (CLARIFY, PROGRESS, etc.) are processed
        between phases, allowing the parent to course-correct.

        v2.0.1 (Phase 3): Uses the DelegationProtocol for iterative
        review — parent reviews child outputs, sends feedback for
        revisions, and resolves conflicts between siblings before
        final synthesis.
        """
        logger.info(f"Cell {self.cell_id}: Delegation execution")

        # Step 1: Plan the delegation
        plan = await self._plan_delegation(task_text, context)

        if not plan or not plan.subtasks:
            logger.warning(f"Cell {self.cell_id}: Empty plan, falling back to solo")
            return await self._execute_solo(task_text, context, envelope)

        # Create a peer group for all children in this delegation
        peer_group = f"delegation-{self.cell_id}"

        # ── Load delegation config ────────────────────────────────────
        kernel_cfg = get_kernel_config()
        delegation_cfg = kernel_cfg.get("delegation", {})
        max_review_rounds = delegation_cfg.get("max_review_rounds", 2)
        min_budget_for_review = delegation_cfg.get(
            "min_budget_for_review",
            2000,
        )

        # Scale review rounds by budget — no reviews if budget is thin
        if self.budget.remaining < min_budget_for_review:
            max_review_rounds = 0
            logger.info(
                f"Cell {self.cell_id}: Budget too low for review rounds "
                f"({self.budget.remaining} < {min_budget_for_review})"
            )

        # ── Respect Graceful Degradation ──────────────────────────────
        degrader = get_degrader()
        if degrader.should_skip_optional():
            max_review_rounds = 0
            logger.warning(f"Cell {self.cell_id}: Degradation active, skipping optional reviews")
        elif degrader.get_current_level().level > 0:
            max_review_rounds = max(1, max_review_rounds // 2)
            logger.info(
                f"Cell {self.cell_id}: Degradation active, reducing review rounds to {max_review_rounds}"
            )

        # ── Step 2: Run the Delegation Protocol ──────────────────────
        # Wrap the inference engine for the protocol's llm_call interface
        async def _delegation_llm_call(
            system_prompt: str = "",
            user_prompt: str = "",
        ) -> str:
            messages = [
                LLMMessage(role=LLMRole.SYSTEM, content=system_prompt),
                LLMMessage(role=LLMRole.USER, content=user_prompt),
            ]
            config = LLMConfig(
                model=self.model,
                temperature=0.3,
                max_tokens=2048,
            )
            response = await self.engine.complete(messages, config)
            self.budget.consume(300)
            return response.content

        protocol = DelegationProtocol(
            parent_cell_id=self.cell_id,
            llm_call=_delegation_llm_call,
            budget_remaining=self.budget.remaining,
        )

        # Wrap _spawn_child for the protocol's interface
        async def _spawn_wrapper(
            subtask: SubTask,
            pg: str,
        ) -> StdioEnvelope:
            result = await self._spawn_child(subtask, peer_group=pg)
            self.state.child_results.append(result)
            return result

        delegation_state: DelegationState = await protocol.run(
            plan=plan,
            spawn_fn=_spawn_wrapper,
            max_rounds=max(1, max_review_rounds),
            peer_group=peer_group,
            govern_fn=self.governor.govern,
        )

        # ── Process trailing messages from children ──────────────────
        await self._process_delegation_messages()

        # ── Step 3: Record delegation metrics ────────────────────────
        self.working_memory.store_fact(
            "delegation_summary",
            f"{len(delegation_state.rounds)} rounds, "
            f"{len(delegation_state.accepted_outputs)} accepted, "
            f"{len(delegation_state.failed_subtasks)} failed, "
            f"{delegation_state.conflicts_detected} conflicts "
            f"({delegation_state.conflicts_resolved} resolved), "
            f"{delegation_state.total_revisions} revisions",
        )

        # ── Step 4: Synthesize accepted outputs ──────────────────────
        child_outputs = []
        all_artifacts: list[Artifact] = []

        # Collect artifacts from delegation_state
        for st_id, artifacts in delegation_state.accepted_artifacts.items():
            for art in artifacts:
                # Re-register artifacts in our own manager for the final package
                new_art = self.working_memory.artifacts.create_artifact(
                    id=f"{st_id}_{art.id}",
                    type=art.type,
                    title=art.title,
                    content=art.content,
                    summary=art.summary,
                    confidence=art.confidence,
                    metadata=art.metadata,
                )
                new_art.status = ArtifactStatus.PUBLISHED
                all_artifacts.append(new_art)

        for i, (st_id, content) in enumerate(
            delegation_state.accepted_outputs.items(),
        ):
            if content:
                child_outputs.append(f"[Subtask {st_id}]\n{content[:2000]}")

        # Include synthesis notes from the review if available
        synthesis_notes = ""
        if delegation_state.rounds:
            last_review = delegation_state.rounds[-1].review
            if last_review and last_review.synthesis_notes:
                synthesis_notes = f"\n\n[REVIEWER NOTES]: {last_review.synthesis_notes}"

        if not child_outputs:
            logger.warning(f"Cell {self.cell_id}: No accepted outputs, falling back to solo")
            return await self._execute_solo(task_text, context, envelope)

        gathered = "\n\n---\n\n".join(child_outputs) + synthesis_notes

        synthesis = await self._synthesize(
            task_text,
            gathered,
            context,
        )

        # Create a WorkPackage for the delegation result
        self.last_work_package = WorkPackage(
            summary=synthesis,
            artifacts=all_artifacts,
            overall_confidence=sum(a.confidence for a in all_artifacts)
            / max(len(all_artifacts), 1),
            key_findings=[f"Synthesis of {len(delegation_state.accepted_outputs)} work products"],
            metadata={"produced_by": "delegation", "rounds": len(delegation_state.rounds)},
        )

        return synthesis

    async def _plan_delegation(
        self,
        task_text: str,
        context: InferenceContext,
    ) -> PlannerOutput | None:
        """Plan task decomposition using structured output."""
        planner_prompt = get_agent_prompt("kernel_delegation_planner")

        messages = [
            LLMMessage(
                role=LLMRole.SYSTEM,
                content=planner_prompt,
            ),
            LLMMessage(
                role=LLMRole.USER,
                content=(
                    f"Task: {task_text}\n\n"
                    f"Available depth: {self.budget.max_depth - self.budget.depth}\n"
                    f"Remaining budget: {self.budget.remaining} tokens\n"
                    f"My level: {self.identity.level}\n"
                    f"My domain: {self.identity.domain}\n\n"
                    "Decompose this into subtasks. Each subtask should be "
                    "independently executable."
                ),
            ),
        ]

        config = LLMConfig(
            model=self.model,
            temperature=0.2,
            max_tokens=2048,
        )

        try:
            result = await self.engine.structured_complete(
                messages,
                config,
                context,
                output_schema=PlannerOutput,
            )
            self.budget.consume(200)  # Planning cost

            if isinstance(result, PlannerOutput):
                logger.info(
                    f"Cell {self.cell_id} plan: "
                    f"{len(result.subtasks)} subtasks in "
                    f"{len(result.execution_order)} phases"
                )
                return result

        except Exception as e:
            logger.error(f"Planning failed: {e}")

        return None

    async def _spawn_child(
        self,
        subtask: SubTask,
        peer_group: str = "",
    ) -> StdioEnvelope:
        """
        Spawn a child kernel cell — THIS IS THE RECURSION.

        v2.0: Children are registered with the message bus. If a
        peer_group is provided, all children in the same delegation
        are connected as peers for lateral communication.
        Before spawning, checks SwarmManager's resource status via REST API
        to respect system-level governance without importing SwarmManager code.
        """
        # Resource gate — check with SwarmManager before spawning child cells
        try:
            import httpx

            from shared.service_registry import ServiceName, ServiceRegistry

            swarm_url = ServiceRegistry.get_url(ServiceName.SWARM_MANAGER)
            async with httpx.AsyncClient(timeout=3.0) as _client:
                _resp = await _client.get(f"{swarm_url}/resource/status")
                if _resp.status_code == 200 and _resp.json().get("status") == "CRITICAL":
                    logger.warning(
                        f"Cell {self.cell_id}: SwarmManager reports CRITICAL load — "
                        "falling back to solo execution instead of spawning child."
                    )
                    return await self._execute_solo(subtask.description, {}, StdioEnvelope())
        except Exception as _gate_err:
            logger.debug(
                f"Cell {self.cell_id}: SwarmManager gate skipped (non-blocking): {_gate_err}"
            )

        # Resolve role for this subtask using Organization + roles.yaml
        child_lvl = child_level_for(self.identity.level)
        child_role = subtask.domain + "_analyst"  # Default fallback

        try:
            from services.orchestrator.core.organization import get_organization

            org = get_organization()
            dept = (
                org.resolve_department(subtask.domain)
                if hasattr(org, "resolve_department")
                else None
            )
            if dept:
                child_role = getattr(dept, "default_role", child_role) or child_role

            # Match from roles.yaml for better specificity
            roles_cfg = self._load_roles_config()
            if roles_cfg:
                matched = self._match_role(subtask.domain, subtask.description, roles_cfg)
                if matched:
                    child_role = matched.get("name", child_role)
                    role_level = matched.get("level")
                    if role_level:
                        child_lvl = role_level
        except Exception as e:
            logger.debug(f"Cell {self.cell_id}: Role resolution fallback: {e}")

        child_identity = AgentIdentity(
            role=child_role,
            level=child_lvl,
            domain=subtask.domain,
        )

        # Allocate budget fraction
        child_budget = self.budget.allocate_fraction(
            fraction=1.0 / max(len(self.children) + 1, 1),
            min_tokens=1000,
        )

        # Create child cell (its __init__ registers with the bus)
        child = KernelCell(
            identity=child_identity,
            tool_executor=self.tool_executor,
            knowledge_retriever=self.knowledge,
            inference_engine=self.engine,
            parent=self,
            budget=child_budget,
            model=self.model,
        )
        self.children.append(child)

        # ── Register child in peer group for lateral messaging ────────
        if peer_group:
            bus = get_message_bus()
            bus.register(
                cell_id=child.cell_id,
                parent_id=self.cell_id,
                peer_group=peer_group,
            )
            # Update the child's communicator with the peer group
            child.comm._peer_group = peer_group

        # ── Register child with Resource Governor ────────────────────
        self.governor.register_child(
            child_id=child.cell_id,
            subtask_id=subtask.id,
            allocated=child_budget.max_tokens,
        )

        # Build instruction envelope for child
        child_envelope = StdioEnvelope(
            stdin=StdinEnvelope(
                instruction=Instruction(text=subtask.description),
                context=TaskContext(
                    parent_task_id=self.cell_id,
                    domain_hints=[subtask.domain],
                ),
                constraints=Constraints(
                    token_budget=child_budget.remaining,
                    max_delegation_depth=child_budget.max_depth - child_budget.depth,
                ),
            ),
            message_type=MessageType.DELEGATE,
        )

        logger.info(
            f"Cell {self.cell_id} → spawned child {child.cell_id} "
            f"({child_identity.role}, budget={child_budget.remaining}, "
            f"peers={'yes' if peer_group else 'no'})"
        )

        # RECURSIVE CALL — child runs the same process() loop
        result = await child.process(child_envelope)

        # ── Record completion and reclaim surplus ────────────────────
        # In a real async system, this would be an event, but here we await
        tokens_used = (
            result.stdout.metadata.get("tokens_used", 0) if hasattr(result, "stdout") else 0
        )
        surplus = self.governor.child_completed(child.cell_id, tokens_used=tokens_used)
        if surplus > 0:
            logger.debug(f"Cell {self.cell_id}: Reclaimed {surplus} tokens from {child.cell_id}")

        return result

    # ================================================================== #
    # Phase 4: QUALITY ASSURANCE
    # ================================================================== #

    async def _quality_check(self, content: str, task_text: str) -> str:
        """Run quality assurance appropriate to this level."""
        gate = get_quality_gate(self.identity.level)

        if self.identity.level in ("intern", "staff"):
            # Staff/Intern: self-review only (cost-effective)
            self.score_card = await self._self_review(content, task_text)

        else:
            # Manager+: use consensus engine for quality check
            try:
                from services.orchestrator.core.consensus import ConsensusEngine

                max_rounds = 1 if self.identity.level == "manager" else 2
                engine = ConsensusEngine(max_rounds=max_rounds)

                consensus = await engine.reach_consensus(
                    query=task_text,
                    facts=[content[:2000]],
                    sources=[],
                )

                self.score_card.accuracy = consensus.get("confidence", 0.5)
                self.score_card.self_confidence = consensus.get("confidence", 0.5)
                self.budget.consume(500 * max_rounds)

                # If consensus produced a better answer, use it
                if consensus.get("final_answer"):
                    content = consensus["final_answer"]

            except Exception as e:
                logger.warning(f"Consensus failed, using self-review: {e}")
                self.score_card = await self._self_review(content, task_text)

        # Check quality gate
        if not gate.passes(self.score_card):
            failures = gate.get_failures(self.score_card)
            logger.warning(f"Cell {self.cell_id} failed quality gate: {failures}")

            # Record in error journal for self-healing awareness
            self.working_memory.error_journal.record_from_quality_gate(
                failures=failures,
                score_card_summary=str(self.score_card.composite_score),
            )

            # Try to revise if budget allows
            if self.score_card.retries < gate.max_retries and self.budget.has_remaining:
                self.score_card.retries += 1
                logger.info(
                    f"Cell {self.cell_id}: Revision attempt "
                    f"{self.score_card.retries}/{gate.max_retries}"
                )
                content = await self._revise(content, task_text, failures)

        return content

    async def _self_review(self, content: str, task_text: str) -> ScoreCard:
        """Quick self-review scoring (for staff/intern level)."""
        try:
            reviewer_prompt = get_agent_prompt("kernel_self_reviewer")

            messages = [
                LLMMessage(
                    role=LLMRole.SYSTEM,
                    content=reviewer_prompt,
                ),
                LLMMessage(
                    role=LLMRole.USER,
                    content=(f"Task: {task_text}\n\nOutput:\n{content[:2000]}"),
                ),
            ]

            config = LLMConfig(
                model=self.model,
                temperature=0.1,
                max_tokens=256,
            )

            response = await self.engine.complete(messages, config)
            self.budget.consume(50)

            # Parse scores
            try:
                scores_text = response.content.strip()
                start = scores_text.find("{")
                end = scores_text.rfind("}") + 1
                if start >= 0 and end > start:
                    scores = json.loads(scores_text[start:end])
                    self.score_card.accuracy = float(scores.get("accuracy", 0.5))
                    self.score_card.completeness = float(scores.get("completeness", 0.5))
                    self.score_card.relevance = float(scores.get("relevance", 0.5))
                    self.score_card.depth = float(scores.get("depth", 0.5))
                    self.score_card.novelty = float(scores.get("novelty", 0.3))
                    self.score_card.coherence = float(scores.get("coherence", 0.5))
                    self.score_card.actionability = float(scores.get("actionability", 0.4))
            except Exception:
                pass

        except Exception as e:
            logger.warning(f"Self-review failed: {e}")

        return self.score_card

    async def _revise(
        self,
        content: str,
        task_text: str,
        failures: list[str],
    ) -> str:
        """Revise content based on quality gate failures."""
        context = InferenceContext(
            identity=self.identity,
            skill_query=task_text,
            quality_bar="professional",
            task_description=task_text,
        )

        revisor_prompt = get_agent_prompt("kernel_revisor")

        messages = [
            LLMMessage(
                role=LLMRole.SYSTEM,
                content=revisor_prompt,
            ),
            LLMMessage(
                role=LLMRole.USER,
                content=(
                    f"Original task: {task_text}\n\n"
                    f"Current output:\n{content[:3000]}\n\n"
                    f"Quality failures:\n"
                    + "\n".join(f"- {f}" for f in failures)
                    + "\n\nRevise the output to address these failures."
                ),
            ),
        ]

        config = LLMConfig(
            model=self.model,
            temperature=0.3,
            max_tokens=4096,
        )

        response = await self.engine.complete(messages, config, context)
        self.budget.consume(200)

        return response.content

    # ================================================================== #
    # Phase 3.5: HEAL (Recursive Self-Healing at Cell Level)
    # ================================================================== #

    def _should_heal(self) -> bool:
        """Decide if self-healing is needed based on error journal state."""
        journal = self.working_memory.error_journal

        # No errors → no healing
        if journal.get_unresolved_count() == 0:
            return False

        # Budget too low for healing
        if self.budget.remaining < 1000:
            return False

        # Only levels staff+ can self-heal (interns just retry)
        if self.identity.level == "intern":
            return False

        # Check healing config
        heal_cfg = self._get_heal_config()
        if not heal_cfg.get("enabled", True):
            return False

        return True

    async def _execute_heal(
        self,
        task_text: str,
        original_result: str,
        context: InferenceContext,
        envelope: StdioEnvelope,
    ) -> str:
        """
        Recursive self-healing at the cell level.

        After execution, if errors were recorded, this method:
        1. Collects unresolved errors from the error journal
        2. Separates into solo-fixable vs delegation-required
        3. Fixes simple errors inline
        4. Delegates complex errors to child cells (if budget allows)
        5. Re-synthesises with fixes applied
        """
        from .convergence import ConvergenceDetector, IterationSnapshot
        from .error_journal import ErrorStatus

        journal = self.working_memory.error_journal
        heal_cfg = self._get_heal_config()

        max_heal_rounds = min(
            heal_cfg.get("max_iterations", 3),
            self.budget.max_depth - self.budget.depth,
        )
        budget_fraction = heal_cfg.get("budget_fraction", 0.25)
        heal_budget = int(self.budget.remaining * budget_fraction)

        detector = ConvergenceDetector(
            max_iterations=max(1, max_heal_rounds),
            max_cascade_depth=heal_cfg.get("max_cascade_depth", 3),
            min_budget_for_heal=heal_cfg.get("min_budget_for_heal", 500),
        )

        logger.info(
            f"Cell {self.cell_id}: Starting self-healing "
            f"({journal.get_unresolved_count()} unresolved errors, "
            f"heal_budget={heal_budget})"
        )

        iteration = 0
        while True:
            decision = detector.should_continue(journal, heal_budget)
            if not decision.continue_healing:
                logger.info(f"Cell {self.cell_id}: Healing stopped — {decision.reason}")
                break

            iteration += 1
            journal.advance_iteration()
            fixes_this_round = 0
            cascades_this_round = 0

            unresolved = journal.get_unresolved()

            # Separate fixable errors by complexity
            solo_fixes = [e for e in unresolved if e.estimated_complexity in ("trivial", "simple")]
            delegation_fixes = [
                e for e in unresolved if e.estimated_complexity in ("moderate", "complex")
            ]

            # Solo fixes: run via cognitive cycle LLM call
            for error in solo_fixes[:3]:
                if heal_budget < 300:
                    break

                # Quick LLM fix
                fix_prompt = (
                    f"Fix this error that occurred during '{task_text[:100]}':\n"
                    f"Error: {error.message[:200]}\n"
                    f"Source: {error.source.value}\n"
                    f"Suggest a corrective action or alternative approach."
                )

                try:
                    fix_response = await self._cognitive_llm_call(
                        system_prompt="You are a diagnostic expert. Fix errors concisely.",
                        user_prompt=fix_prompt,
                    )
                    error.status = ErrorStatus.FIXED
                    error.root_cause = "Diagnosed and resolved inline"
                    fixes_this_round += 1
                    heal_budget -= 200
                    self.budget.consume(200)

                    # Incorporate fix into result
                    self.working_memory.store_fact(
                        f"heal_fix_{error.id}",
                        str(fix_response)[:300],
                    )
                    self.working_memory.learn_fix(
                        error,
                        FixAttempt(
                            attempt_number=1,
                            strategy="inline_llm_fix",
                            result=FixResult.SUCCESS,
                        ),
                    )
                except Exception as e:
                    logger.warning(f"Cell {self.cell_id}: Inline fix failed: {e}")

            # Complex fixes: delegate to child cells
            if delegation_fixes and self.budget.can_delegate and heal_budget > 2000:
                fix_subtasks = self._errors_to_subtasks(delegation_fixes[:2])
                peer_group = f"heal-{self.cell_id}"

                for subtask in fix_subtasks:
                    try:
                        child_result = await self._spawn_child(subtask, peer_group)
                        if (
                            hasattr(child_result, "stdout")
                            and child_result.stdout
                            and child_result.stdout.content
                        ):
                            # Record as fixed
                            err_id = subtask.id.replace("fix_", "")
                            entry = journal.get_entry(err_id)
                            if entry:
                                entry.status = ErrorStatus.FIXED
                                fixes_this_round += 1
                            self.working_memory.store_fact(
                                f"heal_delegation_{subtask.id}",
                                child_result.stdout.content[:300],
                            )
                        heal_budget -= 1000
                        self.budget.consume(500)
                    except Exception as e:
                        logger.warning(f"Cell {self.cell_id}: Heal delegation failed: {e}")
                        cascades_this_round += 1

            detector.record_iteration(
                IterationSnapshot(
                    iteration=iteration,
                    unresolved_count=journal.get_unresolved_count(),
                    fixed_count=fixes_this_round,
                    cascaded_count=cascades_this_round,
                    tokens_consumed=fixes_this_round * 300,
                )
            )

        # Re-synthesise if fixes were applied
        if journal.count_by_status(ErrorStatus.FIXED) > 0:
            heal_facts = {
                k: v for k, v in self.working_memory.all_facts.items() if k.startswith("heal_")
            }
            if heal_facts:
                heal_context = "\n".join(f"- {k}: {v[:200]}" for k, v in heal_facts.items())
                return await self._synthesize(
                    task_text,
                    f"{original_result}\n\n[HEALING FIXES APPLIED]:\n{heal_context}",
                    context,
                )

        return original_result

    def _errors_to_subtasks(
        self,
        errors: list[Any],
    ) -> list[SubTask]:
        """Convert detected errors into subtasks for child delegation."""
        subtasks = []
        for error in errors:
            subtasks.append(
                SubTask(
                    id=f"fix_{error.id}",
                    description=(
                        f"Investigate and fix the following error:\n"
                        f"Error: {error.message[:300]}\n"
                        f"Source: {error.source.value}\n"
                        f"Context: {json.dumps(error.context, default=str)[:200]}\n\n"
                        f"Diagnose the root cause, apply a fix, and verify "
                        f"the fix doesn't introduce new issues."
                    ),
                    domain=self.identity.domain,
                    required_tools=error.context.get("related_tools", []),
                    depends_on=[],
                    estimated_complexity=error.estimated_complexity or "moderate",
                )
            )
        return subtasks

    def _get_heal_config(self) -> dict[str, Any]:
        """Load healing configuration from kernel.yaml."""
        try:
            cfg = get_kernel_config("kernel_cell") or {}
            return cfg.get("healing", {})
        except Exception:
            return {}

    # ================================================================== #
    # Phase 5: OUTPUT
    # ================================================================== #

    def _package_output(self, content: str, task_text: str) -> StdioEnvelope:
        """
        Package result as a StdioEnvelope.

        v2.0: Enriched with working memory signals — confirmed hypotheses,
        low-confidence areas, decisions made, and assumptions are surfaced
        in the envelope's warnings and metadata.
        """
        elapsed_ms = 0.0
        if self._start_time:
            elapsed_ms = (datetime.utcnow() - self._start_time).total_seconds() * 1000

        self.score_card.tokens_consumed = self.budget.max_tokens - self.budget.remaining
        self.score_card.time_ms = elapsed_ms
        self.score_card.tools_used = len(self.state.tool_executions)
        self.score_card.tools_failed = sum(
            1 for t in self.state.tool_executions if not t.get("success", True)
        )
        self.score_card.children_spawned = len(self.children)
        self.score_card.delegation_depth = self.budget.depth

        # ── Build warnings from working memory signals ────────────────
        warnings: list[Warning] = []

        # Data gaps
        for gap in self.score_card.data_gaps:
            warnings.append(
                Warning(
                    type="data_gap",
                    message=gap,
                    severity=WarningSeverity.MEDIUM,
                )
            )

        # Low-confidence areas from working memory
        for topic, conf in self.working_memory.low_confidence_topics:
            warnings.append(
                Warning(
                    type="low_confidence",
                    message=f"Low confidence ({conf:.2f}) on: {topic}",
                    severity=WarningSeverity.LOW,
                )
            )

        # Unanswered questions
        for q in self.working_memory.unanswered_questions[:3]:
            warnings.append(
                Warning(
                    type="unanswered_question",
                    message=f"Unanswered: {q.question[:100]}",
                    severity=WarningSeverity.LOW,
                )
            )

        # Assumptions from working memory
        for assumption in self.score_card.assumptions:
            warnings.append(
                Warning(
                    type="assumption",
                    message=f"Assumed: {assumption[:100]}",
                    severity=WarningSeverity.LOW,
                )
            )

        # Published artifacts from memory
        published_artifacts = self.working_memory.artifacts.get_published()

        # Ensure work package always exists with at least one artifact
        work_package = self.last_work_package
        if not work_package and content:
            work_package = WorkPackage(
                summary=content[:500],
                artifacts=[
                    Artifact(
                        id=f"report_{self.cell_id}",
                        type="report",
                        title=f"Research Report: {task_text[:60]}",
                        content=content,
                        summary=content[:200],
                        confidence=self.score_card.self_confidence,
                        metadata=ArtifactMetadata(
                            sources=[],
                            data_gaps=self.score_card.data_gaps,
                        ),
                    )
                ],
                overall_confidence=self.score_card.self_confidence,
                key_findings=[f"Produced by {self.identity.level}/{self.identity.role}"],
            )
        elif work_package and not work_package.artifacts and content:
            work_package.artifacts = [
                Artifact(
                    id=f"report_{self.cell_id}",
                    type="report",
                    title=f"Research Report: {task_text[:60]}",
                    content=content,
                    summary=content[:200],
                    confidence=self.score_card.self_confidence,
                    metadata=ArtifactMetadata(
                        sources=[],
                        data_gaps=self.score_card.data_gaps,
                    ),
                )
            ]

        return StdioEnvelope(
            stdout=StdoutEnvelope(
                content=content,
                summary=content[:200] if content else "",
                work_package=work_package,
            ),
            stderr=StderrEnvelope(
                warnings=warnings,
            ),
            artifacts=published_artifacts,
            metadata=EnvelopeMetadata(
                cell_id=self.cell_id,
                level=self.identity.level,
                role=self.identity.role,
                domain=self.identity.domain,
                confidence=self.score_card.self_confidence,
                tokens_used=self.score_card.tokens_consumed,
                tokens_remaining=self.budget.remaining,
                duration_ms=elapsed_ms,
                children_count=len(self.children),
                # Communication stats (v2.0)
                messages_sent=self.comm.stats.get("messages_sent", 0) if self.comm else 0,
                messages_received=self.comm.stats.get("messages_received", 0) if self.comm else 0,
                comm_tokens_spent=self.comm.stats.get("comm_budget_spent", 0) if self.comm else 0,
                clarifications_resolved=self.comm.stats.get("clarifications_answered", 0)
                if self.comm
                else 0,
                # Self-healing stats (v2.1)
                heal_errors_fixed=self.working_memory.error_journal.count_by_status(
                    ErrorStatus.FIXED,
                ),
                heal_errors_remaining=self.working_memory.error_journal.get_unresolved_count(),
                heal_cascade_depth=self.working_memory.error_journal.max_cascade_depth(),
            ),
            message_type=MessageType.REPORT,
        )

    def _package_error(self, error: str, task_title: str) -> StdioEnvelope:
        """Package an error as a StdioEnvelope."""
        return StdioEnvelope(
            stdout=StdoutEnvelope(content=""),
            stderr=StderrEnvelope(
                failures=[
                    Failure(task_id=self.cell_id, error=error),
                ],
            ),
            metadata=EnvelopeMetadata(
                cell_id=self.cell_id,
                level=self.identity.level,
                role=self.identity.role,
                confidence=0.0,
            ),
            message_type=MessageType.ESCALATE,
        )

    # ================================================================== #
    # Helper Methods
    # ================================================================== #

    async def _rerank_facts(self, query: str) -> None:
        """
        Rerank accumulated facts by relevance to the original query.

        Uses the shared reranker provider if available. Falls back to
        keeping original order if reranker is unavailable.
        Config-driven: kernel_cell.reranking.enabled in kernel.yaml.
        """
        reranking_cfg = get_kernel_config("kernel_cell.reranking") or {}
        if not reranking_cfg.get("enabled", False):
            return

        facts = self.working_memory.all_facts
        if len(facts) < 3:
            return  # Not enough facts to bother reranking

        try:
            from shared.embedding.model_manager import get_reranker_provider

            reranker = get_reranker_provider()
            if not reranker:
                return

            top_k = reranking_cfg.get("top_k", 10)
            fact_texts = [f"{k}: {v}" for k, v in facts.items()]

            ranked = await reranker.rerank(
                query=query,
                documents=fact_texts[:50],
                top_k=min(top_k, len(fact_texts)),
            )

            # Store reranked order as metadata in working memory
            if ranked:
                self.working_memory.store_fact(
                    "reranked_top_facts",
                    " | ".join(ranked[:5]),
                )

        except Exception as e:
            logger.debug(f"Cell {self.cell_id}: Reranking skipped: {e}")

    async def _execute_tool(self, tool_name: str, arguments: dict) -> str:
        """Execute a tool and record the result."""
        logger.info(f"Cell {self.cell_id} tool: {tool_name}")

        start_time = datetime.utcnow()
        try:
            result = await self.tool_executor(tool_name, arguments)
            duration = (datetime.utcnow() - start_time).total_seconds() * 1000

            self.state.tool_executions.append(
                {
                    "tool": tool_name,
                    "arguments": arguments,
                    "success": True,
                    "duration_ms": duration,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )

            # Store as artifact
            key = f"tool_{len(self.state.tool_executions)}"
            self.state.artifacts[key] = result

            if isinstance(result, str):
                return result[:2000]
            return json.dumps(result, default=str)[:2000]

        except Exception as e:
            logger.error(f"Tool {tool_name} failed: {e}")
            self.state.tool_executions.append(
                {
                    "tool": tool_name,
                    "arguments": arguments,
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )
            return f"ERROR: {e}"

    async def _process_delegation_messages(self) -> None:
        """
        Process messages from children during delegation.

        Handles CLARIFY, PROGRESS, PARTIAL, ESCALATE, and BLOCKED
        messages from child cells. This is the "two-way street" that
        was missing in v1 — children can now talk back to the parent.

        For CLARIFY messages, we use the LLM to generate a contextual
        answer. For PROGRESS and PARTIAL messages, we log them. For
        ESCALATE and BLOCKED, we record in working memory.
        """

        async def _handle_child_message(msg):
            """Auto-handle common message types from children."""
            if msg.channel == MessageChannel.CLARIFY:
                # Use the LLM to answer the child's question
                answer = await self._answer_child_clarification(msg)
                return answer

            elif msg.channel == MessageChannel.PROGRESS:
                pct = msg.payload.get("progress_pct", 0)
                logger.info(
                    f"Cell {self.cell_id} ← progress from {msg.sender_id}: "
                    f"{pct:.0%} — {msg.content[:80]}"
                )
                return None  # No response needed

            elif msg.channel == MessageChannel.PARTIAL:
                logger.info(
                    f"Cell {self.cell_id} ← partial from {msg.sender_id}: {msg.content[:80]}"
                )
                if msg.payload.get("needs_feedback"):
                    return "Continue with current approach."
                return None

            elif msg.channel == MessageChannel.ESCALATE:
                severity_str = msg.payload.get("severity", "medium")
                try:
                    severity = EscalationSeverity(severity_str)
                except ValueError:
                    severity = EscalationSeverity.MEDIUM

                record = await self.governor.handle_escalation(
                    child_id=msg.sender_id,
                    reason=msg.content,
                    severity=severity,
                    context=msg.payload.get("context", ""),
                )

                # Record in memory
                self.working_memory.focus_observation(
                    f"escalation-{msg.sender_id}",
                    f"Child {msg.sender_id} escalated ({severity.value}): {msg.content[:200]} "
                    f"— Resolution Strategy: {record.strategy.value}",
                    source=f"child:{msg.sender_id}",
                )
                return record.response

            elif msg.channel == MessageChannel.BLOCKED:
                # Treat BLOCKED as high-severity escalation
                record = await self.governor.handle_escalation(
                    child_id=msg.sender_id,
                    reason=msg.content,
                    severity=EscalationSeverity.HIGH,
                    context=msg.payload.get("context", ""),
                )
                return record.response

            elif msg.channel == MessageChannel.INSIGHT:
                # Bottom-up insight propagation
                urgency = msg.payload.get("urgency", "normal")
                logger.info(
                    f"Cell {self.cell_id} ← INSIGHT from {msg.sender_id} "
                    f"(urgency={urgency}): {msg.content[:80]}"
                )
                # Store in working memory
                self.working_memory.store_fact(
                    f"insight_{msg.sender_id}",
                    msg.content[:500],
                )
                # If high urgency, share with peer group (sibling cells)
                if urgency in ("high", "critical") and self.comm:
                    await self.comm.share_with_peers(
                        content=f"[INSIGHT from sibling] {msg.content[:300]}",
                        subject="Insight Propagation",
                    )
                # If the insight changes strategic direction, propagate further up
                if urgency == "critical" and self.comm:
                    await self.comm.share_upward(
                        content=msg.content,
                        urgency="high",
                    )
                return None

            return None

        await self.comm.process_incoming_messages(handler=_handle_child_message)

    async def _answer_child_clarification(self, msg) -> str:
        """
        Generate an answer to a child's clarification question.

        Uses the parent's working memory context and the original task
        to provide a relevant answer.
        """
        try:
            wm_context = self.working_memory.compress(max_chars=1000)
            options = msg.payload.get("options", [])
            options_str = ""
            if options:
                options_str = f"\nOptions provided: {', '.join(options)}"

            messages = [
                LLMMessage(
                    role=LLMRole.SYSTEM,
                    content=(
                        "You are a manager answering a subordinate's question. "
                        "Be concise, specific, and actionable. If you don't know, "
                        "say so and provide your best guidance."
                    ),
                ),
                LLMMessage(
                    role=LLMRole.USER,
                    content=(
                        f"My subordinate ({msg.sender_id}) asks:\n"
                        f"{msg.content}\n"
                        f"{options_str}\n\n"
                        f"Context from my own work:\n{wm_context}\n\n"
                        f"Provide a clear, actionable answer."
                    ),
                ),
            ]

            config = LLMConfig(
                model=self.model,
                temperature=0.2,
                max_tokens=256,
            )

            response = await self.engine.complete(messages, config)
            self.budget.consume(30)  # Clarification cost
            return response.content

        except Exception as e:
            logger.warning(f"Failed to answer clarification: {e}")
            return "Proceed with your best judgment."

    async def _synthesize(
        self,
        task_text: str,
        gathered_data: str,
        context: InferenceContext,
    ) -> str:
        """
        Synthesize final answer from gathered data.

        v2.0.1: Updated to handle [CONFLICT RESOLUTION] notes and [REVIEWER NOTES]
        produced by the iterative delegation protocol.
        """
        synthesizer_prompt = get_agent_prompt("kernel_synthesizer")

        messages = [
            LLMMessage(
                role=LLMRole.SYSTEM,
                content=(
                    f"{synthesizer_prompt}\n\n"
                    "Note: The gathered data may contain [CONFLICT RESOLUTION NOTE] markers "
                    "where contradictions between analysts were resolved. Prioritize the "
                    "content of these notes when reconciling differences."
                ),
            ),
            LLMMessage(
                role=LLMRole.USER,
                content=(
                    f"Original Task: {task_text}\n\n"
                    f"Gathered Data:\n{gathered_data[:8000]}\n\n"
                    "Instructions: Synthesize a single, cohesive response that integrates all "
                    "gathered data. If contradictions were noted in the data markers, use the "
                    "resolution provided in the marker."
                ),
            ),
        ]

        config = LLMConfig(
            model=self.model,
            temperature=0.3,
            max_tokens=8192,
        )

        response = await self.engine.complete(messages, config, context)
        self.budget.consume(500)

        return response.content

    def _build_reasoning_prompt(
        self,
        task_text: str,
        step_num: int,
        accumulated: str,
    ) -> str:
        """Build the reasoning prompt for a ReAct step."""
        # Format previous steps
        history = ""
        for step in self.state.reasoning_steps[-5:]:
            history += f"\n[Step {step['step']}] {step.get('action', '?')}: "
            history += f"{step.get('thought', '')[:200]}"
            if step.get("observation"):
                history += f"\n  Observation: {step['observation'][:300]}"

        return (
            f"TASK: {task_text}\n\n"
            f"STEP: {step_num + 1}/{self.state.max_steps}\n"
            f"BUDGET: {self.budget.remaining} tokens remaining\n\n"
            f"PREVIOUS STEPS:{history or ' None yet'}\n\n"
            f"ACCUMULATED DATA:\n{accumulated[:2000] if accumulated else 'None yet'}\n\n"
            "What should I do next?"
        )

    def _get_solo_system_prompt(self) -> str:
        """
        System prompt for solo execution.

        v2.0: Combines the base agentic step prompt with the cognitive
        profile's system prompt modifier and reasoning instruction.
        """
        base = get_agent_prompt("agentic_step")
        modifier = self.cognitive_profile.system_prompt_modifier
        reasoning = self.cognitive_profile.get_reasoning_instruction()
        return f"{base}\n\n{modifier}\n\nREASONING APPROACH:\n{reasoning}"

    def _get_quality_bar(self, envelope: StdioEnvelope) -> str:
        """Extract quality bar from envelope constraints."""
        if envelope.stdin and envelope.stdin.constraints:
            return envelope.stdin.constraints.quality_level.value
        return "professional"

    def _child_level(self) -> str:
        """
        Determine the level for a child cell.

        v2.0: Delegates to cognitive_profiles.child_level_for() which
        uses the full board→intern hierarchy chain.
        """
        return child_level_for(self.identity.level)

    def _load_roles_config(self) -> dict | None:
        """Load roles from configs/roles.yaml. Cached after first load."""
        if not hasattr(self, "_roles_cache"):
            try:
                from pathlib import Path

                import yaml

                roles_path = Path(__file__).parent.parent.parent.parent / "configs" / "roles.yaml"
                if roles_path.exists():
                    with open(roles_path) as f:
                        self._roles_cache = yaml.safe_load(f) or {}
                else:
                    self._roles_cache = None
            except Exception:
                self._roles_cache = None
        return self._roles_cache

    def _match_role(
        self,
        domain: str,
        description: str,
        roles_cfg: dict,
    ) -> dict | None:
        """Match a subtask to the best role from roles.yaml."""
        roles = roles_cfg.get("roles", {})
        matching_cfg = roles_cfg.get("matching", {})
        fallback = matching_cfg.get("fallback_role", "general_analyst")

        best_match: dict | None = None
        best_score = 0.0

        for role_name, role_def in roles.items():
            role_domains = role_def.get("domains", [])
            role_skills = role_def.get("skills", [])

            # Domain match score
            domain_score = 1.0 if domain in role_domains else 0.0

            # Skill keyword overlap with description
            desc_lower = description.lower()
            skill_hits = sum(1 for s in role_skills if s.replace("_", " ") in desc_lower)
            skill_score = skill_hits / max(len(role_skills), 1)

            # Combined score
            total = (domain_score * 0.7) + (skill_score * 0.3)

            if total > best_score:
                best_score = total
                best_match = {**role_def, "name": role_name}

        min_match = matching_cfg.get("min_domain_match", 0.3)
        if best_match and best_score >= min_match:
            return best_match

        # Return fallback role
        if fallback in roles:
            return {**roles[fallback], "name": fallback}

        return None


# ============================================================================
# Convenience Functions
# ============================================================================


async def _retrieve_prior_knowledge(query: str, domain: str) -> list[dict]:
    """
    Retrieve relevant facts from Vault for cross-session knowledge.

    Non-blocking: if Vault is unavailable, returns empty list.
    """
    try:
        import httpx

        vault_url = ServiceRegistry.get_url(ServiceName.VAULT)
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(
                f"{vault_url}/research/query",
                params={"q": query[:200], "limit": 5, "domain": domain},
            )
            if resp.status_code == 200:
                data = resp.json()
                return data.get("facts", [])
    except Exception:
        pass  # Vault not available — non-fatal
    return []


async def _store_result_in_vault(
    query: str,
    envelope: StdioEnvelope,
    job_id: str = "",
) -> None:
    """
    Persist StdioEnvelope result to Vault for cross-session knowledge.

    Fire-and-forget: errors are logged but don't block the response.
    """
    try:
        import httpx

        vault_url = ServiceRegistry.get_url(ServiceName.VAULT)

        payload = {
            "query": query[:500],
            "job_id": job_id,
            "content": envelope.stdout.content[:5000] if envelope.stdout else "",
            "confidence": envelope.metadata.confidence,
            "facts": [
                {"text": kf.finding, "confidence": kf.confidence}
                for kf in (envelope.stdout.key_findings if envelope.stdout else [])
            ],
        }

        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post(
                f"{vault_url}/research/sessions",
                json=payload,
            )
    except Exception as e:
        logger.debug(f"Vault storage skipped: {e}")


async def _store_fix_patterns(
    patterns: list[Any],
    domain: str,
) -> None:
    """
    Persist learned fix patterns to Vault for cross-session healing.

    Fire-and-forget: errors are logged but don't block the response.
    """
    try:
        import httpx

        vault_url = ServiceRegistry.get_url(ServiceName.VAULT)

        payload = {
            "type": "fix_patterns",
            "domain": domain,
            "patterns": [
                {
                    "error_signature": p.error_signature,
                    "successful_fix": p.successful_fix,
                    "frequency": p.frequency,
                }
                for p in patterns[:20]  # Cap at 20 patterns
            ],
        }

        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post(
                f"{vault_url}/research/sessions",
                json=payload,
            )
        logger.debug(f"Stored {len(patterns)} fix patterns in Vault")
    except Exception as e:
        logger.debug(f"Fix pattern storage skipped: {e}")


async def run_kernel(
    query: str,
    tool_executor: Callable[[str, dict], Awaitable[Any]],
    level: str = "ceo",
    domain: str = "general",
    budget: int = 30_000,
    max_depth: int = 3,
) -> StdioEnvelope:
    """
    Run the kernel for a query.

    This is the primary entry point for the entire Kea kernel.

    v4.1: Now wired into /research and /chat/message routes.
    - Retrieves prior knowledge from Vault (cross-session)
    - Stores results in Vault after completion
    - Resets the message bus for clean communication

    Args:
        query: User's query/objective.
        tool_executor: Async function to execute tools: (name, args) -> result.
        level: Starting organizational level.
        domain: Primary domain for the query.
        budget: Total token budget.
        max_depth: Maximum delegation depth.

    Returns:
        StdioEnvelope with the complete result.

    Example:
        result = await run_kernel(
            "Analyze the competitive landscape of vertical farming",
            tool_executor=mcp_host.call_tool,
            budget=50000,
        )
        print(result.stdout.content)
    """
    # Reset communication network for this session
    reset_message_bus()

    # Retrieve prior knowledge from Vault (cross-session facts)
    prior_findings = await _retrieve_prior_knowledge(query, domain)

    identity = AgentIdentity(role="orchestrator", level=level, domain=domain)
    token_budget = TokenBudget(
        max_tokens=budget,
        remaining=budget,
        max_depth=max_depth,
    )

    cell = KernelCell(
        identity=identity,
        tool_executor=tool_executor,
        budget=token_budget,
    )

    envelope = StdioEnvelope(
        stdin=StdinEnvelope(
            instruction=Instruction(text=query),
            context=TaskContext(
                domain_hints=[domain],
                prior_findings=prior_findings,
            ),
            constraints=Constraints(token_budget=budget),
        ),
    )

    result = await cell.process(envelope)

    # Store result in Vault for future cross-session knowledge (non-blocking)
    asyncio.create_task(_store_result_in_vault(query, result))

    # Store learned fix patterns for cross-session healing (non-blocking)
    if cell.working_memory.fix_patterns:
        asyncio.create_task(_store_fix_patterns(cell.working_memory.fix_patterns, domain))

    return result
