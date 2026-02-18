"""
Delegation Protocol   Iterative, Feedback-Driven Delegation.

Upgrades the flat "spawn-and-wait" delegation into a multi-round
protocol where the parent can:

1. Review child outputs against quality criteria
2. Send feedback and request revisions
3. Detect conflicts between sibling outputs
4. Resolve conflicts by re-examining contradictory findings
5. Dynamically add/remove/modify subtasks mid-delegation

The protocol uses the Communication Network (Phase 2) for all
parent child messaging: the parent sends FEEDBACK/REDIRECT/CANCEL
messages; children respond to PARTIAL result requests.

Iteration Loop::

    Plan   Spawn   [Collect   Review   Feedback]   N   Synthesize
                     max rounds gated by budget  

Version: 0.4.0   Part of Kernel Brain Upgrade (Phase 3)
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from enum import Enum
from typing import Any, Awaitable, Callable

from pydantic import BaseModel, Field

from shared.logging import get_logger

from kernel.io.message_bus import (
    MessageBus,
    MessageChannel,
    get_message_bus,
)
from kernel.io.output_schemas import PlannerOutput, SubTask, Artifact

logger = get_logger(__name__)


# ============================================================================
# Delegation Enums & Models
# ============================================================================


class DelegationVerdict(str, Enum):
    """Verdict from parent's review of a child's output."""

    ACCEPTED = "accepted"               # Good enough; use as-is
    NEEDS_REVISION = "needs_revision"    # Send back with feedback
    FAILED = "failed"                    # Irrecoverable; skip or replace
    CONFLICTING = "conflicting"         # Contradicts a sibling's output


class ConflictSeverity(str, Enum):
    """How bad is the conflict between sibling outputs?"""

    MINOR = "minor"          # Stylistic/phrasing difference
    MODERATE = "moderate"    # Different data but compatible conclusions
    MAJOR = "major"          # Contradictory conclusions


class DelegationVerictEntry(BaseModel):
    """A single review verdict for a child's output."""

    subtask_id: str = Field(description="ID of the subtask that was reviewed")
    child_id: str = Field(default="", description="Cell ID of the child")
    verdict: DelegationVerdict = Field(description="Parent's verdict")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    issues: list[str] = Field(default_factory=list)
    feedback: str = Field(default="")


class ConflictReport(BaseModel):
    """Detected conflict between two sibling outputs."""

    subtask_a_id: str
    subtask_b_id: str
    topic: str = Field(description="What the conflict is about")
    finding_a: str = Field(description="What subtask A claims")
    finding_b: str = Field(description="What subtask B claims")
    severity: ConflictSeverity = Field(default=ConflictSeverity.MODERATE)
    resolution: str = Field(default="", description="How the conflict was resolved")


class DelegationReviewResult(BaseModel):
    """Output from a parent's review of all child outputs in a round."""

    verdicts: list[DelegationVerictEntry] = Field(default_factory=list)
    conflicts: list[ConflictReport] = Field(default_factory=list)
    overall_quality: str = Field(
        default="adequate",
        description="poor | adequate | good | excellent",
    )
    ready_to_synthesize: bool = Field(
        default=False,
        description="True if all outputs meet quality bar",
    )
    synthesis_notes: str = Field(
        default="",
        description="Instructions for the synthesizer",
    )


class DelegationRound(BaseModel):
    """Record of a single delegation round (attempt)."""

    round_number: int = Field(default=1)
    started_at: datetime = Field(default_factory=datetime.utcnow)
    subtask_ids: list[str] = Field(default_factory=list)
    results: dict[str, str] = Field(
        default_factory=dict,
        description="subtask_id   output content",
    )
    artifacts: dict[str, list[Artifact]] = Field(
        default_factory=dict,
        description="subtask_id   list of artifacts",
    )
    review: DelegationReviewResult | None = None
    revised_subtask_ids: list[str] = Field(
        default_factory=list,
        description="Subtask IDs sent back for revision",
    )
    elapsed_ms: float = Field(default=0.0)


class DelegationState(BaseModel):
    """Full state of an iterative delegation session."""

    plan: PlannerOutput | None = None
    rounds: list[DelegationRound] = Field(default_factory=list)
    max_rounds: int = Field(default=2)
    conflicts_detected: int = Field(default=0)
    conflicts_resolved: int = Field(default=0)
    total_revisions: int = Field(default=0)
    accepted_outputs: dict[str, str] = Field(
        default_factory=dict,
        description="subtask_id   final accepted content",
    )
    accepted_artifacts: dict[str, list[Artifact]] = Field(
        default_factory=dict,
        description="subtask_id   final accepted artifacts",
    )
    failed_subtasks: list[str] = Field(default_factory=list)
    final_quality: str = Field(default="not_assessed")


# ============================================================================
# Review Prompts
# ============================================================================

REVIEW_SYSTEM_PROMPT = (
    "You are a senior manager reviewing subordinate work. "
    "For each output, assess:\n"
    "1. Does it address the subtask completely?\n"
    "2. Are claims supported by evidence?\n"
    "3. Is the quality appropriate for the audience?\n"
    "4. Are there contradictions with other outputs?\n\n"
    "Be specific about issues. If something is good enough, accept it. "
    "Don't demand perfection   aim for 'good enough to be useful'."
)

CONFLICT_RESOLUTION_PROMPT = (
    "Two analysts produced contradictory findings on the same topic. "
    "Review both sides, determine which is more credible based on "
    "evidence quality, and produce a resolution."
)


# ============================================================================
# Delegation Protocol
# ============================================================================


class DelegationProtocol:
    """
    Orchestrates iterative parent child delegation.

    This protocol wraps the existing spawn-and-wait mechanism with a
    review-feedback loop, allowing the parent to reject sub-par work
    and request revisions. It also detects and resolves conflicts
    between sibling outputs.

    Usage::

        protocol = DelegationProtocol(
            parent_cell_id="analyst-42",
            llm_call=inference_function,
            budget_remaining=10000,
        )

        state = await protocol.run(
            plan=planner_output,
            spawn_fn=cell._spawn_child,
            max_rounds=2,
        )

        # state.accepted_outputs contains all reviewed outputs
        # state.conflicts_detected / resolved track conflict handling
    """

    def __init__(
        self,
        parent_cell_id: str,
        llm_call: Callable[..., Awaitable[Any]],
        budget_remaining: int = 10000,
        bus: MessageBus | None = None,
    ) -> None:
        self.parent_cell_id = parent_cell_id
        self.llm_call = llm_call
        self.budget_remaining = budget_remaining
        self._bus = bus or get_message_bus()

        # Cost tracking
        self._review_token_cost: int = 0

    #   Main Entry Point  

    async def run(
        self,
        plan: PlannerOutput,
        spawn_fn: Callable[[SubTask, str], Awaitable[Any]],
        max_rounds: int = 2,
        peer_group: str = "",
        govern_fn: Callable[[], Awaitable[list[dict[str, Any]]]] | None = None,
    ) -> DelegationState:
        """
        Execute the full iterative delegation protocol.

        Args:
            plan: The planner's task decomposition.
            spawn_fn: Function to spawn a child cell and get results.
                      Signature: (subtask, peer_group) -> StdioEnvelope
            max_rounds: Maximum review revision cycles.
            peer_group: Identifier for lateral messaging among children.

        Returns:
            DelegationState with all accepted outputs, conflict info, etc.
        """
        state = DelegationState(
            plan=plan,
            max_rounds=max_rounds,
        )

        # Track which subtasks still need work
        pending_subtasks: dict[str, SubTask] = {
            st.id: st for st in plan.subtasks
        }

        for round_num in range(1, max_rounds + 1):
            if not pending_subtasks:
                break

            round_record = DelegationRound(
                round_number=round_num,
                subtask_ids=list(pending_subtasks.keys()),
            )

            logger.info(
                f"Cell {self.parent_cell_id}: Delegation round {round_num}/"
                f"{max_rounds}   {len(pending_subtasks)} subtask(s)"
            )

            #   Step 1: Execute pending subtasks in parallel  
            results, artifacts = await self._execute_phase(
                subtasks=list(pending_subtasks.values()),
                plan=plan,
                spawn_fn=spawn_fn,
                peer_group=peer_group,
            )
            round_record.results = results
            round_record.artifacts = artifacts

            # Merge results into accepted (will be filtered by review)
            for st_id, content in results.items():
                if content:
                    state.accepted_outputs[st_id] = content
                    if st_id in artifacts:
                        state.accepted_artifacts[st_id] = artifacts[st_id]

            # Budget check: can we afford a review round?
            review_cost = 300 * len(results)  # Rough estimate
            if review_cost > self.budget_remaining:
                logger.info(
                    f"Cell {self.parent_cell_id}: Budget too low for review "
                    f"({review_cost} > {self.budget_remaining}), accepting all"
                )
                round_record.review = DelegationReviewResult(
                    overall_quality="not_reviewed",
                    ready_to_synthesize=True,
                )
                state.rounds.append(round_record)
                break

            #   Step 2: Review all outputs  
            review = await self._review_outputs(
                results=results,
                subtasks=pending_subtasks,
                existing_accepted=state.accepted_outputs,
            )
            round_record.review = review
            self.budget_remaining -= self._review_token_cost

            #   Step 3: Process verdicts  
            next_pending: dict[str, SubTask] = {}

            for verdict in review.verdicts:
                if verdict.verdict == DelegationVerdict.ACCEPTED:
                    # Keep in accepted_outputs
                    logger.info(
                        f"    {verdict.subtask_id}: accepted "
                        f"(conf={verdict.confidence:.2f})"
                    )

                elif verdict.verdict == DelegationVerdict.NEEDS_REVISION:
                    state.total_revisions += 1
                    if round_num < max_rounds:
                        # Put back in pending with feedback
                        original = pending_subtasks.get(verdict.subtask_id)
                        if original:
                            # Augment the subtask description with feedback
                            revised = original.model_copy(deep=True)
                            revised.description = (
                                f"{original.description}\n\n"
                                f"[REVISION FEEDBACK]:\n{verdict.feedback}\n"
                                f"Issues: {', '.join(verdict.issues)}"
                            )
                            next_pending[verdict.subtask_id] = revised
                            round_record.revised_subtask_ids.append(
                                verdict.subtask_id
                            )
                            logger.info(
                                f"    {verdict.subtask_id}: revision requested "
                                f"({len(verdict.issues)} issues)"
                            )

                            # Send feedback to child via communicator
                            await self._bus.send_to_child(
                                parent_id=self.parent_cell_id,
                                child_id=verdict.child_id,
                                channel=MessageChannel.FEEDBACK,
                                content=verdict.feedback,
                                payload={
                                    "issues": verdict.issues,
                                    "round": round_num,
                                },
                            )
                    else:
                        logger.warning(
                            f"    {verdict.subtask_id}: needs revision but "
                            f"max rounds reached, accepting as-is"
                        )

                elif verdict.verdict == DelegationVerdict.FAILED:
                    state.failed_subtasks.append(verdict.subtask_id)
                    state.accepted_outputs.pop(verdict.subtask_id, None)
                    logger.warning(
                        f"    {verdict.subtask_id}: failed   {verdict.feedback}"
                    )

            #   Step 3.5: Run Governance cycle  
            if govern_fn:
                gov_actions = await govern_fn()
                if gov_actions:
                    logger.debug(
                        f"Cell {self.parent_cell_id}: Governance actions: {gov_actions}"
                    )

            #   Step 4: Resolve conflicts  
            if review.conflicts:
                state.conflicts_detected += len(review.conflicts)
                resolved = await self._resolve_conflicts(
                    conflicts=review.conflicts,
                    current_outputs=state.accepted_outputs,
                )
                state.conflicts_resolved += resolved

            round_record.elapsed_ms = (
                datetime.utcnow() - round_record.started_at
            ).total_seconds() * 1000
            state.rounds.append(round_record)

            # Move to next round with only the subtasks that need revision
            pending_subtasks = next_pending

            if review.ready_to_synthesize:
                logger.info(
                    f"Cell {self.parent_cell_id}: All outputs accepted, "
                    f"ready to synthesize"
                )
                break

        state.final_quality = (
            state.rounds[-1].review.overall_quality
            if state.rounds and state.rounds[-1].review
            else "not_assessed"
        )

        logger.info(
            f"Cell {self.parent_cell_id}: Delegation complete   "
            f"{len(state.rounds)} rounds, "
            f"{len(state.accepted_outputs)} accepted, "
            f"{len(state.failed_subtasks)} failed, "
            f"{state.conflicts_detected} conflicts "
            f"({state.conflicts_resolved} resolved)"
        )

        return state

    #   Phase Execution  

    async def _execute_phase(
        self,
        subtasks: list[SubTask],
        plan: PlannerOutput,
        spawn_fn: Callable[[SubTask, str], Awaitable[Any]],
        peer_group: str = "",
    ) -> tuple[dict[str, str], dict[str, list[Artifact]]]:
        """
        Execute subtasks respecting the plan's execution_order.

        Returns a tuple of:
            (subtask_id   output content, subtask_id   list of artifacts)
        """
        results: dict[str, str] = {}
        artifacts: dict[str, list[Artifact]] = {}
        subtask_map = {st.id: st for st in subtasks}

        # Group subtasks by their phase in the execution order
        for phase_ids in plan.execution_order:
            phase_subtasks = [
                subtask_map[st_id]
                for st_id in phase_ids
                if st_id in subtask_map
            ]
            if not phase_subtasks:
                continue

            # Spawn in parallel
            coros = [
                spawn_fn(st, peer_group) for st in phase_subtasks
            ]
            phase_results = await asyncio.gather(
                *coros, return_exceptions=True,
            )

            for st, result in zip(phase_subtasks, phase_results):
                if isinstance(result, Exception):
                    logger.error(
                        f"Child for {st.id} failed: {result}"
                    )
                    results[st.id] = ""
                elif hasattr(result, "stdout") and hasattr(result.stdout, "content"):
                    # StdioEnvelope
                    results[st.id] = result.stdout.content or ""
                    if hasattr(result, "artifacts"):
                        artifacts[st.id] = result.artifacts
                else:
                    results[st.id] = str(result) if result else ""

        return results, artifacts

    #   Output Review  

    async def _review_outputs(
        self,
        results: dict[str, str],
        subtasks: dict[str, SubTask],
        existing_accepted: dict[str, str],
    ) -> DelegationReviewResult:
        """
        Review child outputs using an LLM-based quality assessment.

        Produces verdicts for each output and detects cross-output
        conflicts.
        """
        # Build review prompt with all outputs
        outputs_text = ""
        for st_id, content in results.items():
            st = subtasks.get(st_id)
            description = st.description[:200] if st else "Unknown"
            truncated = content[:1500] if content else "[NO OUTPUT]"
            outputs_text += (
                f"\n--- Subtask: {st_id} ---\n"
                f"Assignment: {description}\n"
                f"Output:\n{truncated}\n"
            )

        prompt = (
            f"Review these {len(results)} subordinate outputs.\n\n"
            f"{outputs_text}\n\n"
            f"For each subtask, provide:\n"
            f"1. subtask_id\n"
            f"2. verdict: accepted | needs_revision | failed\n"
            f"3. confidence: 0.0-1.0\n"
            f"4. issues: list of specific problems (empty if accepted)\n"
            f"5. feedback: what to improve (empty if accepted)\n\n"
            f"Also check for CONFLICTS between outputs   cases where "
            f"two subtasks make contradictory claims.\n\n"
            f"Respond in JSON with keys: verdicts (list), conflicts (list), "
            f"overall_quality, ready_to_synthesize, synthesis_notes"
        )

        try:
            raw = await self.llm_call(
                system_prompt=REVIEW_SYSTEM_PROMPT,
                user_prompt=prompt,
            )
            self._review_token_cost = 300  # Approximate

            data = _parse_json_safe(raw)

            # Parse verdicts
            verdicts = []
            for v in data.get("verdicts", []):
                try:
                    verdicts.append(DelegationVerictEntry(
                        subtask_id=v.get("subtask_id", ""),
                        verdict=DelegationVerdict(
                            v.get("verdict", "accepted"),
                        ),
                        confidence=float(v.get("confidence", 0.5)),
                        issues=v.get("issues", []),
                        feedback=v.get("feedback", ""),
                    ))
                except (ValueError, KeyError):
                    continue

            # Parse conflicts
            conflicts = []
            for c in data.get("conflicts", []):
                try:
                    conflicts.append(ConflictReport(
                        subtask_a_id=c.get("subtask_a_id", ""),
                        subtask_b_id=c.get("subtask_b_id", ""),
                        topic=c.get("topic", ""),
                        finding_a=c.get("finding_a", ""),
                        finding_b=c.get("finding_b", ""),
                        severity=ConflictSeverity(
                            c.get("severity", "moderate"),
                        ),
                    ))
                except (ValueError, KeyError):
                    continue

            return DelegationReviewResult(
                verdicts=verdicts,
                conflicts=conflicts,
                overall_quality=data.get("overall_quality", "adequate"),
                ready_to_synthesize=data.get("ready_to_synthesize", True),
                synthesis_notes=data.get("synthesis_notes", ""),
            )

        except Exception as e:
            logger.warning(
                f"Review LLM call failed: {e}; accepting all outputs"
            )
            # Fallback: accept everything
            verdicts = [
                DelegationVerictEntry(
                    subtask_id=st_id,
                    verdict=DelegationVerdict.ACCEPTED,
                    confidence=0.5,
                )
                for st_id in results
            ]
            return DelegationReviewResult(
                verdicts=verdicts,
                overall_quality="not_reviewed",
                ready_to_synthesize=True,
            )

    #   Conflict Resolution  

    async def _resolve_conflicts(
        self,
        conflicts: list[ConflictReport],
        current_outputs: dict[str, str],
    ) -> int:
        """
        Resolve detected conflicts between sibling outputs.

        Uses the LLM to determine which finding is more credible
        and updates the accepted outputs accordingly.

        Returns:
            Number of conflicts successfully resolved.
        """
        resolved_count = 0

        for conflict in conflicts:
            # Skip minor conflicts
            if conflict.severity == ConflictSeverity.MINOR:
                conflict.resolution = "Minor difference, no action needed"
                resolved_count += 1
                continue

            output_a = current_outputs.get(conflict.subtask_a_id, "")
            output_b = current_outputs.get(conflict.subtask_b_id, "")

            prompt = (
                f"Two analysts disagree on: {conflict.topic}\n\n"
                f"Analyst A ({conflict.subtask_a_id}) claims:\n"
                f"{conflict.finding_a}\n\n"
                f"Analyst B ({conflict.subtask_b_id}) claims:\n"
                f"{conflict.finding_b}\n\n"
                f"Analyst A's full output (excerpt):\n"
                f"{output_a[:800]}\n\n"
                f"Analyst B's full output (excerpt):\n"
                f"{output_b[:800]}\n\n"
                f"Determine:\n"
                f"1. preferred: A or B (which is more credible?)\n"
                f"2. resolution: how to reconcile\n"
                f"3. confidence: 0.0-1.0\n\n"
                f"Respond in JSON."
            )

            try:
                raw = await self.llm_call(
                    system_prompt=CONFLICT_RESOLUTION_PROMPT,
                    user_prompt=prompt,
                )

                data = _parse_json_safe(raw)
                preferred = data.get("preferred", "A").upper()
                resolution = data.get("resolution", "")

                conflict.resolution = resolution
                resolved_count += 1

                # Annotate the losing output with the resolution
                loser_id = (
                    conflict.subtask_b_id
                    if preferred == "A"
                    else conflict.subtask_a_id
                )
                if loser_id in current_outputs:
                    current_outputs[loser_id] = (
                        f"{current_outputs[loser_id]}\n\n"
                        f"[CONFLICT RESOLUTION NOTE]: {resolution}"
                    )

                logger.info(
                    f"  Conflict resolved ({conflict.topic}): "
                    f"preferred {preferred}   {resolution[:80]}"
                )

            except Exception as e:
                logger.warning(
                    f"Conflict resolution failed for {conflict.topic}: {e}"
                )

        return resolved_count


# ============================================================================
# JSON Parsing Helper
# ============================================================================


def _parse_json_safe(raw: Any) -> dict[str, Any]:
    """
    Parse LLM output as JSON, handling common formatting issues.

    Handles:
    - Pydantic model objects (with .model_dump())
    - Raw strings (with json.loads())
    - Markdown-wrapped JSON (```json ... ```)
    - Already parsed dicts
    """
    import json
    import re

    if hasattr(raw, "model_dump"):
        return raw.model_dump()

    if isinstance(raw, dict):
        return raw

    text = str(raw).strip()

    # Strip markdown code fences
    match = re.search(r"```(?:json)?\s*\n?(.*?)\n?\s*```", text, re.DOTALL)
    if match:
        text = match.group(1).strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Try to find JSON object in the text
        brace_start = text.find("{")
        brace_end = text.rfind("}")
        if brace_start >= 0 and brace_end > brace_start:
            try:
                return json.loads(text[brace_start:brace_end + 1])
            except json.JSONDecodeError:
                pass

    return {}
