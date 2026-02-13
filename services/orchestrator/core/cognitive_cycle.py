"""
Cognitive Cycle — The Full Human Thinking Loop.

Replaces the flat ReAct loop (think→act→observe→repeat) with a
biologically-inspired cognitive cycle:

    Perceive → Frame → Plan → Execute → Monitor → Adapt → Package

Each phase is a discrete async method that can be overridden or
customised per cognitive profile.  The cycle integrates with
``WorkingMemory`` for structured state, ``CognitiveProfile`` for
level-aware behaviour, and ``CellCommunicator`` for inter-cell
messaging during execution.

The ``CognitiveCycle`` is used *inside* `KernelCell._execute_solo()` to
replace the old flat reasoning loop.  Delegation is handled separately
by the kernel cell's own delegation path — this module only governs
how a single cell *thinks and works*.

Communication Integration (v2.0):
- PLAN phase: if clarification is needed AND a communicator is present,
  the cycle asks the parent directly instead of returning early.
- EXECUTE loop: checks for redirect/cancel messages and peer-shared
  data between steps; reports progress at configurable intervals.
- MONITOR phase: includes communication signals (redirects, shared data)
  in the self-assessment.

Version: 2.0.1 — Brain Upgrade + Communication Network
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Awaitable, Callable

from pydantic import BaseModel, Field

from shared.logging import get_logger
from shared.prompts import get_agent_prompt

from .cognitive_profiles import CognitiveProfile, ReasoningStyle
from .output_schemas import (
    WorkPackage,
    Artifact,
    ArtifactType,
    ArtifactStatus,
    ArtifactMetadata,
)
from .working_memory import (
    FocusItem,
    FocusItemType,
    QuestionTarget,
    WorkingMemory,
)

logger = get_logger(__name__)


# ============================================================================
# Cycle Phase Enum
# ============================================================================


class CyclePhase(str, Enum):
    """Current phase in the cognitive cycle."""

    PERCEIVE = "perceive"       # Understand the instruction
    FRAME = "frame"             # Restate the problem, identify assumptions
    PLAN = "plan"               # Choose approach, estimate effort
    EXECUTE = "execute"         # Do the work (tool calls, analysis)
    MONITOR = "monitor"         # Self-check: am I on track?
    ADAPT = "adapt"             # Change approach if needed
    PACKAGE = "package"         # Format results for consumer


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


class FramingResult(BaseModel):
    """Output of the FRAME phase."""

    restatement: str = Field(description="Problem restated in own words")
    assumptions: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    scope_boundaries: str = Field(
        default="",
        description="What IS and IS NOT in scope",
    )
    known_facts: list[str] = Field(
        default_factory=list,
        description="Facts already known (from memory/context)",
    )
    unknown_gaps: list[str] = Field(
        default_factory=list,
        description="Information gaps that need to be filled",
    )


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


class MonitorResult(BaseModel):
    """Output of the MONITOR phase (self-assessment)."""

    on_track: bool = Field(default=True)
    progress_pct: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="Estimated progress 0.0–1.0",
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


# ============================================================================
# Cognitive Cycle Runner
# ============================================================================


class CognitiveCycle:
    """
    The full human-inspired cognitive cycle for a single kernel cell.

    This replaces the flat ReAct loop with:

        Perceive → Frame → Plan → [Execute ↔ Monitor → Adapt] → Package

    The Execute↔Monitor loop runs iteratively until the cell either:
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

        # Communication (v2.0) — typed as Any to avoid circular import
        # Actual type: CellCommunicator | None
        self.comm = communicator

        # Internal state
        self.current_phase = CyclePhase.PERCEIVE
        self.monitor_count = 0
        self.tool_call_count = 0
        self.accumulated_content: list[str] = []       # Draft sections
        self.tool_results: list[dict[str, Any]] = []   # Raw tool outputs

        # Communication tracking
        self._progress_report_interval: int = 3  # Report every N steps
        self._last_progress_report: int = 0

    # ================================================================ #
    # Main Entry Point
    # ================================================================ #

    async def run(
        self,
        task: str,
        context: str = "",
        available_tools: list[dict[str, Any]] | None = None,
    ) -> CycleOutput:
        """
        Execute the full cognitive cycle.

        Returns a ``CycleOutput`` containing the produced content,
        quality signals, and working memory state.
        """
        start_time = datetime.utcnow()
        available_tools = available_tools or []

        logger.info(
            f"🧠 CognitiveCycle [{self.profile.level}] starting | "
            f"style={self.profile.reasoning_style.value} | "
            f"max_steps={self.profile.max_reasoning_steps}"
        )

        # ── Phase 1: PERCEIVE ─────────────────────────────────────────
        self.current_phase = CyclePhase.PERCEIVE
        perception = await self._perceive(task, context)

        # ── Phase 2: FRAME ────────────────────────────────────────────
        self.current_phase = CyclePhase.FRAME
        framing = await self._frame(task, context, perception)

        # ── Phase 3: PLAN ────────────────────────────────────────────
        self.current_phase = CyclePhase.PLAN
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
                    # Clarifications answered → continue execution
                    plan.needs_clarification = False
                    plan.clarification_questions = []
                    logger.info(
                        f"🧠 CognitiveCycle: {len(resolved)} clarifications "
                        f"resolved via communicator, continuing"
                    )
                else:
                    # No answers → fall through to early return
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

        # ── Phase 4+5+6: EXECUTE ↔ MONITOR → ADAPT loop ──────────────
        self.current_phase = CyclePhase.EXECUTE
        await self._execute_loop(task, context, plan, available_tools)

        # ── Phase 7: PACKAGE ──────────────────────────────────────────
        self.current_phase = CyclePhase.PACKAGE
        work_package = await self._package(perception, framing)

        elapsed = _elapsed_ms(start_time)
        logger.info(
            f"🧠 CognitiveCycle [{self.profile.level}] done | "
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
                system_prompt=get_agent_prompt("kernel_perceiver") or (
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

        # Store in working memory
        self.memory.focus_observation(
            "perception",
            f"Task: {result.task_text[:200]}",
            source="perceive",
        )
        for entity in result.key_entities[:5]:
            self.memory.focus_fact(f"entity_{entity}", entity, source="perceive")

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
                system_prompt=get_agent_prompt("kernel_framer") or (
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
            self.memory.focus(FocusItem(
                id=f"gap_{gap[:20]}",
                item_type=FocusItemType.QUESTION,
                content=f"Need to find: {gap}",
                source="frame",
            ))

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
        tools_summary = ""
        if available_tools:
            tool_names = [t.get("name", "?") for t in available_tools[:15]]
            tools_summary = f"\nAvailable tools: {', '.join(tool_names)}"

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
            f"3. estimated_tools: number of tool calls needed\n"
            f"4. estimated_steps: number of reasoning steps\n"
            f"5. risk_factors: what could go wrong\n"
            f"6. can_complete_solo: can you do this alone?\n"
            f"7. needs_delegation: should this be split across agents?\n"
            f"8. needs_clarification: do you need more info first?\n"
            f"9. clarification_questions: if so, what questions?\n\n"
            f"Respond in JSON only."
        )

        try:
            raw = await self.llm_call(
                system_prompt=get_agent_prompt("kernel_planner") or (
                    "You are an execution planner. Create actionable plans "
                    "with clear steps. Be realistic about effort. Respond in JSON."
                ),
                user_prompt=prompt,
            )
            data = _parse_json_safe(raw)
            result = PlanResult(
                approach=data.get("approach", "Sequential analysis"),
                steps=data.get("steps", ["Research and analyze"]),
                estimated_tools=data.get("estimated_tools", 0),
                estimated_steps=data.get("estimated_steps", 3),
                risk_factors=data.get("risk_factors", []),
                can_complete_solo=data.get("can_complete_solo", True),
                needs_delegation=data.get("needs_delegation", False),
                needs_clarification=data.get("needs_clarification", False),
                clarification_questions=data.get("clarification_questions", []),
            )
        except Exception as e:
            logger.warning(f"Planning LLM call failed: {e}; using default plan")
            result = PlanResult(
                approach="Sequential research and analysis",
                steps=["Gather data", "Analyze", "Synthesize"],
            )

        # Record plan in working memory
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
    # Phase 4+5+6: EXECUTE ↔ MONITOR → ADAPT loop
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

        Iterates through plan steps, calling tools and analyzing results.
        Periodically self-monitors and adapts if quality is declining.

        v2.0 Communication hooks:
        - Check for REDIRECT/CANCEL from parent between steps
        - Incorporate peer-shared data as it arrives
        - Report progress to parent at regular intervals
        """
        max_steps = self.profile.max_reasoning_steps
        monitor_interval = max(
            1,
            max_steps // (self.profile.max_self_monitor_checks + 1),
        )

        reasoning_instruction = self.profile.get_reasoning_instruction()
        tools_summary = self._format_tools(available_tools)

        for step_idx in range(max_steps):
            self.memory.advance_step()

            # ── Communication check (between steps) ───────────────────
            if self.comm and step_idx > 0:
                # Check for redirect/cancel from parent
                redirect = self.comm.check_for_redirect()
                if redirect:
                    logger.info(
                        f"  📨 Redirect received at step {step_idx}: "
                        f"{redirect.content[:80]}"
                    )
                    self.memory.focus_observation(
                        f"redirect-{step_idx}",
                        f"Parent redirect: {redirect.content[:200]}",
                        source="parent",
                    )
                    # If it's a cancel, stop immediately
                    from .message_bus import MessageChannel
                    if redirect.channel == MessageChannel.CANCEL:
                        logger.info("  Execution cancelled by parent")
                        break
                    # Otherwise, record the new direction and let
                    # the monitor/adapt phases incorporate it

                # Incorporate peer-shared data
                shared = self.comm.check_for_shared_data()
                if shared:
                    logger.info(
                        f"  📨 Received {len(shared)} shared item(s) from peers"
                    )

                # Report progress at intervals
                if (
                    step_idx - self._last_progress_report
                    >= self._progress_report_interval
                ):
                    progress = step_idx / max_steps if max_steps > 0 else 0.0
                    await self._report_progress(progress, task, step_idx)
                    self._last_progress_report = step_idx

            # ── Monitor check (periodic) ──────────────────────────────
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
                        f"  Monitor detected redirect, adapting: "
                        f"{monitor.redirect_content[:80]}"
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

            # ── Execute one reasoning step ────────────────────────────
            step_prompt = self._build_step_prompt(
                task=task,
                context=context,
                step_idx=step_idx,
                total_steps=max_steps,
                plan=plan,
                tools_summary=tools_summary,
                reasoning_instruction=reasoning_instruction,
            )

            try:
                raw = await self.llm_call(
                    system_prompt=self._build_execute_system_prompt(),
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

            logger.debug(
                f"  Step {step_idx}: action={action} "
                f"confidence={confidence:.2f}"
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

            # Update confidence
            topic = f"step_{step_idx}"
            self.memory.set_confidence(topic, confidence)

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
            self.tool_results.append({
                "tool": tool_name,
                "args": tool_args,
                "result": result_str,
                "step": step_idx,
            })

            self.memory.store_fact(
                f"tool_{tool_name}_{step_idx}",
                result_str[:500],
            )
            self.memory.focus(FocusItem(
                id=f"tool_result_{step_idx}",
                item_type=FocusItemType.TOOL_RESULT,
                content=f"{tool_name}: {result_str[:200]}",
                source=tool_name,
            ))

            logger.debug(f"  Tool {tool_name}: {len(result_str)} chars")

        except Exception as e:
            logger.warning(f"  Tool {tool_name} failed: {e}")
            self.memory.note(
                f"tool_error_{step_idx}",
                f"{tool_name} failed: {str(e)[:200]}",
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

        # ── Communication signals (v2.0) ──────────────────────────────
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
                    prompt += (
                        f"Peer data received: {shared_data_count} item(s)\n"
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
                    system_prompt=(
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

        # Combine heuristic + LLM signals
        should_continue = True
        if not has_content and progress > 0.5:
            should_continue = False    # Half budget spent, no content = stalled
        if drift > 0.7:
            should_change = True
            suggested_adjustment = "Refocus on original task — output is drifting"

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
                    adjustment="Moving to synthesis — stagnation detected",
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

        This is the synthesis step — combines all gathered data, analysis,
        and reasoning into a structured WorkPackage containing multiple
        artifacts, tailored to the audience.
        """
        if not self.accumulated_content and not self.memory.all_facts:
            return WorkPackage(
                summary="No data was gathered or analysis produced for this task.",
                overall_confidence=0.0
            )

        # Gather all material for the LLM
        all_content = "\n\n".join(self.accumulated_content)
        facts_text = "\n".join(
            f"- {k}: {v[:500]}" for k, v in self.memory.all_facts.items()
        )
        tool_summary = "\n".join(
            f"- {t['tool']}({t.get('args', {})}): {t['result'][:200]}"
            for t in self.tool_results
        )

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
            f"  \"summary\": \"Executive summary of the whole package\",\n"
            f"  \"artifacts\": [\n"
            f"    {{\n"
            f"      \"id\": \"unique_id\",\n"
            f"      \"type\": \"report|analysis|dataset|recommendation\",\n"
            f"      \"title\": \"Title of artifact\",\n"
            f"      \"content\": \"Full markdown content\",\n"
            f"      \"confidence\": 0.9,\n"
            f"      \"metadata\": {{ \"sources\": [...], \"data_gaps\": [...] }}\n"
            f"    }}\n"
            f"  ],\n"
            f"  \"overall_confidence\": 0.85,\n"
            f"  \"key_findings\": [\"finding 1\", ...]\n"
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
                metadata={"produced_by": self.profile.level, "steps": self.monitor_count}
            )
            return package

        except Exception as e:
            logger.error(f"Structured packaging failed: {e}")
            # Fallback to a simple package
            return WorkPackage(
                summary=f"Analysis encountered error during packaging: {e}",
                artifacts=[self.memory.artifacts.create_artifact(
                    id="fallback_report",
                    type=ArtifactType.REPORT,
                    title="Incomplete Report",
                    content=all_content or "No content available."
                )],
                overall_confidence=0.1
            )

    # ================================================================ #
    # Helpers
    # ================================================================ #

    def _build_execute_system_prompt(self) -> str:
        """Build the system prompt for execute steps."""
        base = get_agent_prompt("kernel_executor") or (
            "You are an autonomous research agent executing tasks step by step."
        )
        modifier = self.profile.system_prompt_modifier
        reasoning = self.profile.get_reasoning_instruction()
        return f"{base}\n\n{modifier}\n\nREASONING APPROACH:\n{reasoning}"

    def _build_step_prompt(
        self,
        task: str,
        context: str,
        step_idx: int,
        total_steps: int,
        plan: PlanResult,
        tools_summary: str,
        reasoning_instruction: str,
    ) -> str:
        """Build the user prompt for a single execution step."""
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

        force_synthesis = self.memory.get_note("force_synthesis")
        if force_synthesis:
            prompt_parts.append(
                f"\n⚠️ {force_synthesis}. Move to synthesis/complete."
            )

        prompt_parts.append(
            '\n=== RESPOND ===\n'
            'JSON with keys: thought, action '
            '(call_tool|analyze|synthesize|complete), '
            'action_input, confidence (0.0-1.0)'
        )

        return "\n".join(prompt_parts)

    def _format_tools(self, tools: list[dict[str, Any]]) -> str:
        """Format available tools for inclusion in prompts."""
        if not tools:
            return ""
        lines = []
        for t in tools[:15]:
            name = t.get("name", "?")
            desc = t.get("description", "")[:100]
            lines.append(f"- {name}: {desc}")
        return "\n".join(lines)

    def _assess_final_quality(self) -> str:
        """Quick final quality assessment based on working memory signals."""
        if not self.accumulated_content:
            return "poor"

        confidence = self.memory.overall_confidence
        facts = self.memory.fact_count
        content_length = sum(len(c) for c in self.accumulated_content)

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
                logger.info(
                    f"  Clarification answered: {question[:50]} → "
                    f"{answer[:50]}"
                )
            else:
                logger.info(
                    f"  Clarification unanswered: {question[:50]}"
                )

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

    # ── Control signals ──────────────────────────────────────────────
    needs_delegation: bool = Field(default=False)
    needs_clarification: bool = Field(default=False)
    clarification_questions: list[str] = Field(default_factory=list)

    # ── Phase results ────────────────────────────────────────────────
    perception: PerceptionResult | None = None
    framing: FramingResult | None = None
    plan: PlanResult | None = None

    # ── Quality ──────────────────────────────────────────────────────
    quality: str = Field(default="not_assessed")

    # ── Metrics ──────────────────────────────────────────────────────
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
