"""
The Re-Architected Cognitive Cycle (v3.0).

Replaces the monolithic cognitive_cycle.py with a modular pipeline.
Orchestrates:
    Perceive -> Frame -> Plan -> Execute -> Monitor -> Adapt -> Package
"""

from __future__ import annotations

from typing import Any, Awaitable, Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from kernel.awareness.context_fusion import AwarenessEnvelope

from pydantic import BaseModel, Field

from kernel.cognition.base import CycleContext, CyclePhase
from kernel.cognition.perceiver import Perceiver, PerceptionResult
from kernel.cognition.framer import Framer, FramingResult
from kernel.cognition.planner import Planner, PlanResult
from kernel.cognition.executor import Executor
from kernel.cognition.monitor import Monitor, MonitorResult
from kernel.cognition.adapter import Adapter
from kernel.cognition.packager import Packager
from kernel.memory.working_memory import WorkingMemory
from kernel.actions.cell_communicator import CellCommunicator
from kernel.io.output_schemas import WorkPackage
from shared.logging import get_logger

logger = get_logger(__name__)


class CycleOutput(BaseModel):
    """Standard output of the cycle execution."""
    content: str = ""
    work_package: WorkPackage | None = None
    needs_delegation: bool = False
    needs_clarification: bool = False
    clarification_questions: list[str] = Field(default_factory=list)
    perception: PerceptionResult | None = None
    framing: FramingResult | None = None
    plan: PlanResult | None = None
    quality: str = "not_assessed"
    tool_results: list[dict] = Field(default_factory=list)
    memory_state: dict[str, Any] = Field(default_factory=dict)
    elapsed_ms: float = 0.0
    facts_gathered: int = 0
    decisions_made: int = 0


class CognitiveCycle:
    """
    Modular Cognitive Cycle.
    """

    def __init__(
        self,
        profile: Any, # CognitiveProfile
        memory: WorkingMemory,
        llm_call: Callable[[str, str], Awaitable[str]],
        tool_call: Callable[[str, dict], Awaitable[Any]],
        task_id: str = "",
        communicator: CellCommunicator | None = None,
        awareness: AwarenessEnvelope | None = None,
    ):
        self.profile = profile
        self.memory = memory
        self.llm_call = llm_call
        self.tool_call = tool_call
        self.task_id = task_id
        self.communicator = communicator

        # Initialize context holder (will be populated in run)
        self.context = CycleContext(
            task_id=task_id,
            task_text="",
            memory=memory,
            communicator=communicator,
            llm_call=llm_call,
            tool_call=tool_call,
            awareness=awareness,
        )

    async def run(
        self,
        task: str,
        context: str = "",
        available_tools: list[dict] | None = None,
        seed_facts: list[dict] | None = None,
        error_feedback: list[dict] | None = None,
        awareness: AwarenessEnvelope | None = None,
    ) -> CycleOutput:
        """Run the full cognitive cycle."""

        # 0. Setup
        self.context.task_text = task
        self.context.available_tools = available_tools or []

        # Override awareness if provided at run-time (takes precedence over __init__)
        if awareness is not None:
            self.context.awareness = awareness

        # Inject seed facts into working memory
        if seed_facts:
            for fact in seed_facts:
                key = fact.get("key", "seed_fact")
                value = fact.get("value", str(fact))
                self.memory.store_fact(key, value)

        # Inject error feedback as a memory signal
        if error_feedback:
            self.memory.store_fact(
                "error_feedback",
                str(error_feedback[-3:]),  # Last 3 errors
            )
        
        # 1. PERCEIVE
        perceiver = Perceiver(self.context)
        perception = await perceiver.run()
        
        # 2. FRAME
        framer = Framer(self.context)
        framing = await framer.run(perception)

        # ── Epistemic Feedback Loop (Phase 4) ──
        # Framer identified knowledge gaps → update the epistemic state so
        # Monitor and Packager see an accurate picture of what we don't know.
        if hasattr(self.context, "awareness") and self.context.awareness is not None:
            epistemic = self.context.awareness.epistemic
            for gap in framing.unknown_gaps:
                if gap not in epistemic.known_unknowns:
                    epistemic.known_unknowns.append(gap)
        
        # 3. PLAN
        planner = Planner(self.context)
        plan = await planner.run(perception, framing)
        
        # Check for delegation/clarification
        if getattr(plan, "needs_delegation", False):
            return CycleOutput(
                needs_delegation=True,
                perception=perception,
                framing=framing,
                plan=plan,
                memory_state=self.memory.to_dict(),
                elapsed_ms=self.context.elapsed_ms
            )

        if getattr(plan, "needs_clarification", False):
             # Simplified: just return request
             return CycleOutput(
                needs_clarification=True,
                clarification_questions=getattr(plan, "clarification_questions", []),
                perception=perception,
                framing=framing,
                plan=plan,
                memory_state=self.memory.to_dict(),
                elapsed_ms=self.context.elapsed_ms
            )
        
        # 4. EXECUTE
        executor = Executor(self.context)
        exec_result = await executor.run(plan)
        
        # 5. MONITOR
        monitor = Monitor(self.context)
        monitor_result = await monitor.run()
        
        # 6. ADAPT (Loop logic simplified for V2 Refactor)
        if monitor_result.decision == "replan":
            logger.info("Cycle triggering replan based on monitor feedback")
            
            adapter = Adapter(self.context)
            feedback = await adapter.run(monitor_result)
            
            new_plan = await planner.run(
                perception, 
                framing, 
                feedback=feedback
            ) 
            exec_result = await executor.run(new_plan)
            monitor_result = await monitor.run()

        # 7. PACKAGE
        packager = Packager(self.context)
        package = await packager.run(perception, framing)
        
        # Construct Output
        return CycleOutput(
            content=package.summary,
            work_package=package,
            perception=perception,
            framing=framing,
            plan=plan,
            quality=str(monitor_result.confidence),
            tool_results=self.context.tool_results,
            memory_state=self.memory.to_dict(),
            elapsed_ms=self.context.elapsed_ms,
            facts_gathered=self.memory.fact_count,
            decisions_made=len(self.memory.decisions)
        )

    @property
    def tool_call_count(self) -> int:
        """Total number of tool calls made during the cycle."""
        return self.context.tool_call_count
