"""
The Kernel Cell — Universal Recursive Processing Unit.

Every level of the corporate hierarchy — from CEO to intern — runs this
exact same code. Only the configuration differs: identity, tools, knowledge,
budget, quality bar.

This is the CORE module of Kea's kernel. It wires together:
- KnowledgeEnhancedInference → for context engineering per inference
- KnowledgeRetriever → for skill/rule/procedure retrieval
- ConsensusEngine → for per-level quality assurance
- Organization → for role resolution during delegation
- WorkBoard → for kanban-style task tracking
- ScoreCard → for multi-dimensional quality scoring
- StdioEnvelope → for structured I/O contracts
- Output Schemas → for validated LLM output parsing

Features:
- Recursive delegation: spawn_child() creates child cells
- Budget-controlled execution: TokenBudget prevents infinite recursion
- Solo execution: ReAct loop with tool calls for simple tasks
- Quality gates: per-level thresholds with configurable failure actions
- Contribution tracking: who produced what in the final output
"""

from __future__ import annotations

import asyncio
import json
import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from shared.config import get_settings
from shared.knowledge.retriever import KnowledgeRetriever, get_knowledge_retriever
from shared.llm import LLMConfig, OpenRouterProvider
from shared.llm.provider import LLMMessage, LLMRole
from shared.logging import get_logger
from shared.prompts import get_agent_prompt, get_kernel_config

from services.orchestrator.core.inference_context import (
    AgentIdentity,
    InferenceContext,
    KnowledgeEnhancedInference,
    get_inference_engine,
)
from services.orchestrator.core.complexity import classify_complexity
from services.orchestrator.core.output_schemas import (
    ActionType,
    ComplexityAssessment,
    PlannerOutput,
    ProcessingMode,
    ReasoningOutput,
    RoleResolution,
    SubTask,
    SynthesisOutput,
)
from services.orchestrator.core.score_card import (
    ContributionLedger,
    ContributionRecord,
    QualityGate,
    ScoreCard,
    aggregate_scores,
    get_quality_gate,
)
from services.orchestrator.core.work_unit import (
    WorkUnit,
    WorkType,
    get_work_board,
)
from services.orchestrator.core.stdio_envelope import (
    ArtifactReference,
    Constraints,
    DeliverableSection,
    EnvelopeMetadata,
    Escalation,
    Failure,
    Instruction,
    KeyFinding,
    MessageType,
    StderrEnvelope,
    StdinEnvelope,
    StdioEnvelope,
    StdoutEnvelope,
    TaskContext,
    Warning,
    WarningSeverity,
)

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
    """

    max_tokens: int = 10_000
    remaining: int = 10_000
    depth: int = 0
    max_depth: int = 5

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
    The Universal Employee — recursive kernel processing unit.

    Every level of the hierarchy runs this exact same code. Only the
    configuration differs: identity, tools, knowledge, budget, quality bar.

    Phases:
        1. INTAKE — Parse instruction, load context and knowledge
        2. ASSESS — Determine complexity → solo vs. delegation
        3. EXECUTE — ReAct loop (solo) or spawn children (delegation)
        4. QUALITY — Run consensus/self-review quality gate
        5. OUTPUT — Package result as StdioEnvelope

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

        # State
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

    # ================================================================== #
    # Phase 0: Main Entry Point
    # ================================================================== #

    async def process(self, envelope: StdioEnvelope) -> StdioEnvelope:
        """
        The Universal Processing Loop.

        Every employee — CEO to intern — runs this exact loop.
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

        try:
            # Phase 1: INTAKE
            task_text, context = await self._intake(envelope)

            # Phase 2: ASSESS complexity (heuristic-first, saves LLM calls)
            processing_mode = await self._assess_complexity(task_text, context)

            # Phase 3: EXECUTE
            if processing_mode in (ProcessingMode.DIRECT, ProcessingMode.SOLO):
                result_content = await self._execute_solo(task_text, context, envelope)
            elif self.budget.can_delegate:
                result_content = await self._execute_delegation(task_text, context, envelope)
            else:
                # Budget exhausted, fall back to solo
                logger.warning(
                    f"Cell {self.cell_id}: Budget too low for delegation, "
                    f"falling back to solo execution"
                )
                result_content = await self._execute_solo(task_text, context, envelope)

            # Phase 4: QUALITY ASSURANCE
            scored_result = await self._quality_check(result_content, task_text)

            # Phase 5: OUTPUT
            self._work_unit.complete(result="Quality gate passed")
            return self._package_output(scored_result, task_text)

        except Exception as e:
            logger.error(f"Cell {self.cell_id} failed: {e}")
            if self._work_unit:
                self._work_unit.fail(str(e))
            return self._package_error(str(e), task_title)

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
            f"Cell {self.cell_id} intake: "
            f"task='{task_text[:60]}...' domain={self.identity.domain}"
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
            self._complexity_modes = (
                get_kernel_config("kernel_cell.complexity_mode_mapping") or {}
            )

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
                messages, config, context,
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
    # Phase 3a: SOLO Execution (ReAct Loop)
    # ================================================================== #

    async def _execute_solo(
        self,
        task_text: str,
        context: InferenceContext,
        envelope: StdioEnvelope,
    ) -> str:
        """Execute task using a ReAct-style reasoning loop with tools."""
        logger.info(f"Cell {self.cell_id}: Solo execution (ReAct loop)")

        max_steps = min(self.state.max_steps, 15)
        accumulated_content = ""

        for step_num in range(max_steps):
            if not self.budget.has_remaining:
                logger.warning(f"Cell {self.cell_id}: Budget exhausted at step {step_num}")
                break

            self.state.current_step = step_num + 1

            try:
                # Build reasoning context
                reasoning_prompt = self._build_reasoning_prompt(
                    task_text, step_num, accumulated_content,
                )

                messages = [
                    LLMMessage(role=LLMRole.SYSTEM, content=self._get_solo_system_prompt()),
                    LLMMessage(role=LLMRole.USER, content=reasoning_prompt),
                ]

                config = LLMConfig(
                    model=self.model,
                    temperature=0.3,
                    max_tokens=4096,
                )

                # Get next action with structured output
                result = await self.engine.structured_complete(
                    messages, config, context,
                    output_schema=ReasoningOutput,
                )

                if not isinstance(result, ReasoningOutput):
                    # Fallback: treat as text analysis
                    accumulated_content += f"\n{result.content}"
                    continue

                reasoning = result
                self.budget.consume(100)  # Approximate cost per step

                # Record step
                step_record = {
                    "step": step_num + 1,
                    "thought": reasoning.thought,
                    "action": reasoning.action.value,
                    "confidence": reasoning.confidence,
                    "timestamp": datetime.utcnow().isoformat(),
                }

                logger.info(
                    f"Cell {self.cell_id} step {step_num + 1}: "
                    f"{reasoning.action.value} (conf={reasoning.confidence:.2f})"
                )

                # Execute the action
                if reasoning.action == ActionType.COMPLETE:
                    accumulated_content = reasoning.action_input.get(
                        "answer", accumulated_content,
                    )
                    step_record["observation"] = "Task completed"
                    self.state.reasoning_steps.append(step_record)
                    break

                elif reasoning.action == ActionType.CALL_TOOL:
                    tool_name = reasoning.action_input.get("tool", "")
                    tool_args = reasoning.action_input.get("arguments", {})
                    observation = await self._execute_tool(tool_name, tool_args)
                    step_record["observation"] = observation[:500]
                    accumulated_content += f"\n[Tool: {tool_name}]\n{observation[:1000]}"

                elif reasoning.action == ActionType.ANALYZE:
                    step_record["observation"] = reasoning.thought
                    accumulated_content += f"\n[Analysis]\n{reasoning.thought}"

                elif reasoning.action == ActionType.SYNTHESIZE:
                    synthesis = await self._synthesize(task_text, accumulated_content, context)
                    accumulated_content = synthesis
                    step_record["observation"] = "Synthesis complete"
                    self.state.reasoning_steps.append(step_record)
                    break

                elif reasoning.action in (ActionType.DELEGATE, ActionType.ESCALATE):
                    # Can't delegate in solo mode, treat as escalation note
                    accumulated_content += (
                        f"\n[Note: Recommended {reasoning.action.value} "
                        f"to {reasoning.delegate_to or 'parent'}]"
                    )
                    step_record["observation"] = f"Cannot {reasoning.action.value} in solo mode"

                self.state.reasoning_steps.append(step_record)

            except Exception as e:
                logger.error(f"Cell {self.cell_id} step {step_num} error: {e}")
                self.state.reasoning_steps.append({
                    "step": step_num + 1,
                    "thought": f"Error: {e}",
                    "action": "error",
                    "timestamp": datetime.utcnow().isoformat(),
                })

        # Force synthesis if we ran out of steps
        if not accumulated_content or self.state.status != "complete":
            accumulated_content = await self._synthesize(
                task_text, accumulated_content, context,
            )

        return accumulated_content

    # ================================================================== #
    # Phase 3b: DELEGATION Execution (Recursive)
    # ================================================================== #

    async def _execute_delegation(
        self,
        task_text: str,
        context: InferenceContext,
        envelope: StdioEnvelope,
    ) -> str:
        """Execute task by planning and delegating to child cells."""
        logger.info(f"Cell {self.cell_id}: Delegation execution")

        # Step 1: Plan the delegation
        plan = await self._plan_delegation(task_text, context)

        if not plan or not plan.subtasks:
            logger.warning(f"Cell {self.cell_id}: Empty plan, falling back to solo")
            return await self._execute_solo(task_text, context, envelope)

        # Step 2: Execute each phase
        all_results: list[StdioEnvelope] = []

        for phase_idx, phase in enumerate(plan.execution_order):
            logger.info(
                f"Cell {self.cell_id}: Phase {phase_idx + 1}/{len(plan.execution_order)} "
                f"— {len(phase)} parallel subtasks"
            )

            # Find subtasks for this phase
            phase_subtasks = [
                st for st in plan.subtasks if st.id in phase
            ]

            # Spawn children in parallel
            child_coros = [
                self._spawn_child(subtask) for subtask in phase_subtasks
            ]
            phase_results = await asyncio.gather(*child_coros, return_exceptions=True)

            for result in phase_results:
                if isinstance(result, StdioEnvelope):
                    all_results.append(result)
                    self.state.child_results.append(result)
                elif isinstance(result, Exception):
                    logger.error(f"Child cell failed: {result}")
                    all_results.append(self._package_error(
                        str(result), "Child cell execution",
                    ))

        # Step 3: Aggregate child score cards
        child_cards = [
            ScoreCard(**r.metadata.model_dump())
            for r in all_results
            if r.metadata.confidence > 0
        ]
        if child_cards:
            self.score_card = aggregate_scores(self.score_card, child_cards)

        # Step 4: Synthesize all child outputs
        child_outputs = []
        for i, result in enumerate(all_results):
            child_outputs.append(
                f"[Subtask {i + 1}]\n{result.stdout.content[:2000]}"
            )

        synthesis = await self._synthesize(
            task_text,
            "\n\n---\n\n".join(child_outputs),
            context,
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
                messages, config, context,
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

    async def _spawn_child(self, subtask: SubTask) -> StdioEnvelope:
        """Spawn a child kernel cell — THIS IS THE RECURSION."""
        # Resolve role for this subtask
        child_identity = AgentIdentity(
            role=subtask.domain + "_analyst",
            level=self._child_level(),
            domain=subtask.domain,
        )

        # Allocate budget fraction
        child_budget = self.budget.allocate_fraction(
            fraction=1.0 / max(len(self.children) + 1, 1),
            min_tokens=1000,
        )

        # Create child cell
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
            f"({child_identity.role}, budget={child_budget.remaining})"
        )

        # RECURSIVE CALL — child runs the same process() loop
        return await child.process(child_envelope)

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
            logger.warning(
                f"Cell {self.cell_id} failed quality gate: {failures}"
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
                    content=(
                        f"Task: {task_text}\n\n"
                        f"Output:\n{content[:2000]}"
                    ),
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
                    f"Quality failures:\n" +
                    "\n".join(f"- {f}" for f in failures) +
                    "\n\nRevise the output to address these failures."
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
    # Phase 5: OUTPUT
    # ================================================================== #

    def _package_output(self, content: str, task_text: str) -> StdioEnvelope:
        """Package result as a StdioEnvelope."""
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

        return StdioEnvelope(
            stdout=StdoutEnvelope(
                content=content,
                summary=content[:200] if content else "",
            ),
            stderr=StderrEnvelope(
                warnings=[
                    Warning(
                        type="data_gap",
                        message=gap,
                        severity=WarningSeverity.MEDIUM,
                    )
                    for gap in self.score_card.data_gaps
                ],
            ),
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

    async def _execute_tool(self, tool_name: str, arguments: dict) -> str:
        """Execute a tool and record the result."""
        logger.info(f"Cell {self.cell_id} tool: {tool_name}")

        start_time = datetime.utcnow()
        try:
            result = await self.tool_executor(tool_name, arguments)
            duration = (datetime.utcnow() - start_time).total_seconds() * 1000

            self.state.tool_executions.append({
                "tool": tool_name,
                "arguments": arguments,
                "success": True,
                "duration_ms": duration,
                "timestamp": datetime.utcnow().isoformat(),
            })

            # Store as artifact
            key = f"tool_{len(self.state.tool_executions)}"
            self.state.artifacts[key] = result

            if isinstance(result, str):
                return result[:2000]
            return json.dumps(result, default=str)[:2000]

        except Exception as e:
            logger.error(f"Tool {tool_name} failed: {e}")
            self.state.tool_executions.append({
                "tool": tool_name,
                "arguments": arguments,
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            })
            return f"ERROR: {e}"

    async def _synthesize(
        self,
        task_text: str,
        gathered_data: str,
        context: InferenceContext,
    ) -> str:
        """Synthesize final answer from gathered data."""
        synthesizer_prompt = get_agent_prompt("kernel_synthesizer")

        messages = [
            LLMMessage(
                role=LLMRole.SYSTEM,
                content=synthesizer_prompt,
            ),
            LLMMessage(
                role=LLMRole.USER,
                content=(
                    f"Original Task: {task_text}\n\n"
                    f"Gathered Data:\n{gathered_data[:6000]}\n\n"
                    "Synthesize a complete answer."
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
        """System prompt for solo ReAct execution."""
        return get_agent_prompt("agentic_step")

    def _get_quality_bar(self, envelope: StdioEnvelope) -> str:
        """Extract quality bar from envelope constraints."""
        if envelope.stdin and envelope.stdin.constraints:
            return envelope.stdin.constraints.quality_level.value
        return "professional"

    def _child_level(self) -> str:
        """Determine the level for a child cell."""
        hierarchy = ["ceo", "vp", "director", "manager", "staff", "intern"]
        try:
            current_idx = hierarchy.index(self.identity.level)
            return hierarchy[min(current_idx + 1, len(hierarchy) - 1)]
        except ValueError:
            return "staff"


# ============================================================================
# Convenience Functions
# ============================================================================


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
    identity = AgentIdentity(role="orchestrator", level=level, domain=domain)
    token_budget = TokenBudget(
        max_tokens=budget, remaining=budget, max_depth=max_depth,
    )

    cell = KernelCell(
        identity=identity,
        tool_executor=tool_executor,
        budget=token_budget,
    )

    envelope = StdioEnvelope(
        stdin=StdinEnvelope(
            instruction=Instruction(text=query),
            context=TaskContext(domain_hints=[domain]),
            constraints=Constraints(token_budget=budget),
        ),
    )

    return await cell.process(envelope)
