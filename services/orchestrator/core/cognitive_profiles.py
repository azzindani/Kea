"""
Cognitive Profiles — Level-Aware Thinking.

Defines *how* a kernel cell thinks based on its organizational level.
An intern does direct lookups; a Director plans and delegates; a VP
makes strategic trade-offs.

Each profile specifies:
- **Primary cognitive modes** — What this level spends most of its time doing.
- **Execution vs. delegation balance** — How much work it does itself.
- **Review depth** — How thoroughly it reviews subordinate work.
- **Reasoning style** — Prompt modifiers that shape the LLM's output.
- **Time horizon** — How far into the future this level thinks.
- **Max reasoning steps** — Budget for the cognitive cycle.
- **Autonomy level** — How much this level can decide on its own.

Profiles are loaded from ``kernel.yaml`` with sensible defaults.

Version: 2.0.0 — Part of Kernel Brain Upgrade (Phase 1)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from shared.logging import get_logger
from shared.prompts import get_kernel_config

logger = get_logger(__name__)


# ============================================================================
# Cognitive Modes
# ============================================================================


class CognitiveMode(str, Enum):
    """Fundamental cognitive operations available to a kernel cell."""

    # Perception & Comprehension
    PERCEIVE = "perceive"           # Understand instruction, detect intent
    RECALL = "recall"               # Retrieve relevant knowledge
    FRAME = "frame"                 # Restate problem, identify assumptions

    # Planning & Reasoning
    DECOMPOSE = "decompose"         # Break problem into sub-problems
    PRIORITIZE = "prioritize"       # Rank by importance and dependency
    ESTIMATE = "estimate"           # Assess effort, risk, feasibility
    STRATEGIZE = "strategize"       # Choose approach (depth-first, etc.)

    # Execution
    RESEARCH = "research"           # Gather information using tools
    ANALYZE = "analyze"             # Apply reasoning to data
    SYNTHESIZE = "synthesize"       # Combine data into conclusions
    CREATE = "create"               # Produce new artifacts

    # Metacognition (Self-Monitoring)
    SELF_ASSESS = "self_assess"     # "Am I on track?"
    CALIBRATE = "calibrate"         # "How confident am I?"
    ADAPT = "adapt"                 # "Let me try a different approach"

    # Communication
    DELEGATE = "delegate"           # Assign work downward
    REPORT = "report"               # Send results upward
    CONSULT = "consult"             # Ask a peer
    ESCALATE = "escalate"           # Push problem upward


class ReviewDepth(str, Enum):
    """How thoroughly a level reviews subordinate work."""

    NONE = "none"               # Intern: no reviewing others
    CHECKLIST = "checklist"     # Staff: verify checklist items
    SELF_REVIEW = "self_review" # Sr. Staff: review own work
    DETAILED = "detailed"       # Manager: line-by-line review
    THOROUGH = "thorough"       # Director: structural review
    MODERATE = "moderate"       # VP: key-conclusions review
    LIGHT = "light"             # C-Suite/Board: executive summary only


class ReasoningStyle(str, Enum):
    """The cognitive approach — shapes the LLM system prompt."""

    DIRECT_LOOKUP = "direct_lookup"                 # Fast, no analysis
    PROCEDURAL = "procedural"                       # Follow SOP step by step
    DEEP_ANALYTICAL = "deep_analytical"             # Thorough, exhaustive
    TASK_ORIENTED = "task_oriented"                 # Get-it-done, practical
    STRUCTURED_ANALYSIS = "structured_analysis"     # Frameworks, matrices
    CROSS_FUNCTIONAL = "cross_functional"           # Across-domain thinking
    STRATEGIC_PATTERN = "strategic_pattern"         # Pattern recognition, vision


# ============================================================================
# Cognitive Profile
# ============================================================================


class CognitiveProfile(BaseModel):
    """
    Complete cognitive profile for an organizational level.

    This is the *personality* of a kernel cell — it defines how the cell
    approaches problems, how much it delegates, and how it reviews work.
    """

    level: str = Field(description="Organizational level name")

    # ── What this level primarily does ────────────────────────────────
    primary_modes: list[CognitiveMode] = Field(
        default_factory=list,
        description="Cognitive modes this level spends most time on",
    )

    # ── Balance of work ──────────────────────────────────────────────
    execution_pct: float = Field(
        default=0.5, ge=0.0, le=1.0,
        description="Fraction of work done by self (vs. delegated)",
    )
    delegation_pct: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="Fraction of work delegated to subordinates",
    )

    # ── Review behaviour ─────────────────────────────────────────────
    review_depth: ReviewDepth = Field(
        default=ReviewDepth.SELF_REVIEW,
        description="How deeply this level reviews work",
    )

    # ── Reasoning style (shapes LLM prompt) ──────────────────────────
    reasoning_style: ReasoningStyle = Field(
        default=ReasoningStyle.DEEP_ANALYTICAL,
        description="Cognitive approach — injected into system prompt",
    )

    # ── Time horizon ─────────────────────────────────────────────────
    time_horizon: str = Field(
        default="hours_to_days",
        description="How far ahead this level thinks",
    )

    # ── Cognitive budget ─────────────────────────────────────────────
    max_reasoning_steps: int = Field(
        default=8,
        description="Max reasoning steps in the cognitive cycle",
    )
    max_tool_calls: int = Field(
        default=5,
        description="Max tool calls before forced synthesis",
    )
    max_self_monitor_checks: int = Field(
        default=3,
        description="Mid-execution quality checks",
    )

    # ── Autonomy ─────────────────────────────────────────────────────
    can_delegate: bool = Field(
        default=False,
        description="Whether this level can delegate to subordinates",
    )
    can_escalate: bool = Field(
        default=True,
        description="Whether this level can escalate to parent",
    )
    can_consult_peers: bool = Field(
        default=False,
        description="Whether this level can consult sibling cells",
    )

    # ── Prompt modifiers ─────────────────────────────────────────────
    system_prompt_modifier: str = Field(
        default="",
        description=(
            "Extra instructions appended to the system prompt, "
            "shaping HOW the LLM reasons for this level"
        ),
    )

    def get_reasoning_instruction(self) -> str:
        """
        Generate a reasoning instruction for the LLM based on this
        profile's reasoning style and primary modes.
        """
        style_instructions = {
            ReasoningStyle.DIRECT_LOOKUP: (
                "Answer directly and concisely. Do not analyze or elaborate "
                "unless the data specifically requires interpretation. "
                "Focus on precision and speed."
            ),
            ReasoningStyle.PROCEDURAL: (
                "Follow a clear step-by-step procedure. For each step, "
                "state what you're doing and why. Check your work against "
                "the expected output format before proceeding."
            ),
            ReasoningStyle.DEEP_ANALYTICAL: (
                "Analyze thoroughly. For each data point, consider: "
                "(1) what it means, (2) what it implies, (3) what's missing. "
                "Look for patterns, anomalies, and non-obvious connections. "
                "Quantify wherever possible."
            ),
            ReasoningStyle.TASK_ORIENTED: (
                "Focus on getting the task done efficiently. Break it into "
                "concrete steps, execute them, and verify the result. "
                "Prioritize actionable output over exhaustive analysis."
            ),
            ReasoningStyle.STRUCTURED_ANALYSIS: (
                "Use structured analytical frameworks. Organize your "
                "thinking into clear categories, comparisons, and trade-offs. "
                "Use matrices, pro/con lists, or SWOT-style analysis "
                "where appropriate."
            ),
            ReasoningStyle.CROSS_FUNCTIONAL: (
                "Think across domains and perspectives. Consider how this "
                "issue connects to other areas (financial, legal, technical, "
                "operational). Identify cross-cutting themes and conflicts "
                "between viewpoints."
            ),
            ReasoningStyle.STRATEGIC_PATTERN: (
                "Think at the strategic level. Identify long-term patterns, "
                "market dynamics, and systemic forces. Focus on 'so what' "
                "implications rather than raw data. Recommend positioning "
                "and directional choices."
            ),
        }
        return style_instructions.get(
            self.reasoning_style,
            style_instructions[ReasoningStyle.DEEP_ANALYTICAL],
        )


# ============================================================================
# Default Profiles (fallback when kernel.yaml is missing)
# ============================================================================


_DEFAULT_PROFILES: dict[str, CognitiveProfile] = {

    "board": CognitiveProfile(
        level="board",
        primary_modes=[
            CognitiveMode.STRATEGIZE, CognitiveMode.FRAME,
            CognitiveMode.PRIORITIZE,
        ],
        execution_pct=0.05,
        delegation_pct=0.80,
        review_depth=ReviewDepth.LIGHT,
        reasoning_style=ReasoningStyle.STRATEGIC_PATTERN,
        time_horizon="years",
        max_reasoning_steps=4,
        max_tool_calls=0,
        max_self_monitor_checks=1,
        can_delegate=True,
        can_escalate=False,
        can_consult_peers=True,
        system_prompt_modifier=(
            "You are a board-level strategic thinker. Focus on vision, "
            "direction, and high-level resource allocation. Delegate all "
            "execution. Review only executive summaries."
        ),
    ),

    "ceo": CognitiveProfile(
        level="ceo",
        primary_modes=[
            CognitiveMode.FRAME, CognitiveMode.DECOMPOSE,
            CognitiveMode.STRATEGIZE, CognitiveMode.SYNTHESIZE,
        ],
        execution_pct=0.10,
        delegation_pct=0.70,
        review_depth=ReviewDepth.MODERATE,
        reasoning_style=ReasoningStyle.CROSS_FUNCTIONAL,
        time_horizon="quarters_to_years",
        max_reasoning_steps=6,
        max_tool_calls=1,
        max_self_monitor_checks=2,
        can_delegate=True,
        can_escalate=True,
        can_consult_peers=True,
        system_prompt_modifier=(
            "You are a C-level executive synthesizer. Your job is to "
            "break strategic objectives into departmental mandates, "
            "coordinate across functions, and ensure coherent output."
        ),
    ),

    "vp": CognitiveProfile(
        level="vp",
        primary_modes=[
            CognitiveMode.DECOMPOSE, CognitiveMode.PRIORITIZE,
            CognitiveMode.SYNTHESIZE, CognitiveMode.SELF_ASSESS,
        ],
        execution_pct=0.15,
        delegation_pct=0.55,
        review_depth=ReviewDepth.MODERATE,
        reasoning_style=ReasoningStyle.STRUCTURED_ANALYSIS,
        time_horizon="months_to_quarters",
        max_reasoning_steps=8,
        max_tool_calls=2,
        max_self_monitor_checks=3,
        can_delegate=True,
        can_escalate=True,
        can_consult_peers=True,
        system_prompt_modifier=(
            "You are a VP-level programme orchestrator. Decompose objectives "
            "into projects, assign to Director-level leads, and synthesize "
            "results into executive-ready deliverables."
        ),
    ),

    "director": CognitiveProfile(
        level="director",
        primary_modes=[
            CognitiveMode.DECOMPOSE, CognitiveMode.PRIORITIZE,
            CognitiveMode.ANALYZE, CognitiveMode.SYNTHESIZE,
        ],
        execution_pct=0.20,
        delegation_pct=0.50,
        review_depth=ReviewDepth.THOROUGH,
        reasoning_style=ReasoningStyle.STRUCTURED_ANALYSIS,
        time_horizon="weeks_to_months",
        max_reasoning_steps=10,
        max_tool_calls=3,
        max_self_monitor_checks=3,
        can_delegate=True,
        can_escalate=True,
        can_consult_peers=True,
        system_prompt_modifier=(
            "You are a Director-level technical lead. Structure projects "
            "into well-scoped tasks, review team output for accuracy "
            "and completeness, and produce architecture-level summaries."
        ),
    ),

    "manager": CognitiveProfile(
        level="manager",
        primary_modes=[
            CognitiveMode.DECOMPOSE, CognitiveMode.RESEARCH,
            CognitiveMode.ANALYZE, CognitiveMode.SELF_ASSESS,
        ],
        execution_pct=0.30,
        delegation_pct=0.40,
        review_depth=ReviewDepth.DETAILED,
        reasoning_style=ReasoningStyle.TASK_ORIENTED,
        time_horizon="days_to_weeks",
        max_reasoning_steps=12,
        max_tool_calls=5,
        max_self_monitor_checks=4,
        can_delegate=True,
        can_escalate=True,
        can_consult_peers=True,
        system_prompt_modifier=(
            "You are a hands-on team lead. Break projects into concrete "
            "tasks, assign them, review deliverables closely, and fill "
            "gaps yourself when needed."
        ),
    ),

    "senior_staff": CognitiveProfile(
        level="senior_staff",
        primary_modes=[
            CognitiveMode.RESEARCH, CognitiveMode.ANALYZE,
            CognitiveMode.SYNTHESIZE, CognitiveMode.CREATE,
        ],
        execution_pct=0.70,
        delegation_pct=0.10,
        review_depth=ReviewDepth.SELF_REVIEW,
        reasoning_style=ReasoningStyle.DEEP_ANALYTICAL,
        time_horizon="hours_to_days",
        max_reasoning_steps=15,
        max_tool_calls=8,
        max_self_monitor_checks=5,
        can_delegate=False,
        can_escalate=True,
        can_consult_peers=True,
        system_prompt_modifier=(
            "You are a senior specialist and deep thinker. Produce "
            "thorough, well-sourced analysis. Challenge your own "
            "assumptions, quantify claims, and flag uncertainties."
        ),
    ),

    "staff": CognitiveProfile(
        level="staff",
        primary_modes=[
            CognitiveMode.RESEARCH, CognitiveMode.ANALYZE,
            CognitiveMode.CREATE,
        ],
        execution_pct=0.85,
        delegation_pct=0.0,
        review_depth=ReviewDepth.CHECKLIST,
        reasoning_style=ReasoningStyle.PROCEDURAL,
        time_horizon="minutes_to_hours",
        max_reasoning_steps=10,
        max_tool_calls=5,
        max_self_monitor_checks=2,
        can_delegate=False,
        can_escalate=True,
        can_consult_peers=False,
        system_prompt_modifier=(
            "You are a competent analyst. Follow the task instructions "
            "carefully, gather data, and produce clear output. "
            "Cite all sources and flag missing data."
        ),
    ),

    "intern": CognitiveProfile(
        level="intern",
        primary_modes=[
            CognitiveMode.RESEARCH, CognitiveMode.CREATE,
        ],
        execution_pct=0.95,
        delegation_pct=0.0,
        review_depth=ReviewDepth.NONE,
        reasoning_style=ReasoningStyle.DIRECT_LOOKUP,
        time_horizon="immediate",
        max_reasoning_steps=5,
        max_tool_calls=3,
        max_self_monitor_checks=1,
        can_delegate=False,
        can_escalate=True,
        can_consult_peers=False,
        system_prompt_modifier=(
            "You are a junior assistant. Answer the question directly "
            "and concisely. Do not over-analyze. If the task is simple, "
            "respond immediately. If you don't have the data, say so."
        ),
    ),
}


# ============================================================================
# Profile Loader
# ============================================================================


def _load_profiles_from_config() -> dict[str, CognitiveProfile]:
    """
    Load cognitive profiles from kernel.yaml.

    Expected YAML structure:
    ```yaml
    cognitive_profiles:
      board:
        primary_modes: [strategize, frame, prioritize]
        execution_pct: 0.05
        ...
    ```

    If the config is missing, returns the hardcoded defaults.
    """
    raw = get_kernel_config("cognitive_profiles")
    if not isinstance(raw, dict) or not raw:
        logger.debug("No cognitive_profiles in kernel.yaml, using defaults")
        return dict(_DEFAULT_PROFILES)

    profiles: dict[str, CognitiveProfile] = {}
    for level, data in raw.items():
        if not isinstance(data, dict):
            continue
        try:
            # Convert mode strings to enums
            if "primary_modes" in data:
                data["primary_modes"] = [
                    CognitiveMode(m) for m in data["primary_modes"]
                ]
            if "review_depth" in data:
                data["review_depth"] = ReviewDepth(data["review_depth"])
            if "reasoning_style" in data:
                data["reasoning_style"] = ReasoningStyle(data["reasoning_style"])

            profiles[level] = CognitiveProfile(level=level, **data)
            logger.info(f"Loaded cognitive profile: {level}")
        except Exception as e:
            logger.warning(
                f"Failed to load cognitive profile '{level}': {e}; "
                f"using default"
            )
            if level in _DEFAULT_PROFILES:
                profiles[level] = _DEFAULT_PROFILES[level]

    # Backfill any missing levels from defaults
    for default_level, default_profile in _DEFAULT_PROFILES.items():
        if default_level not in profiles:
            profiles[default_level] = default_profile

    return profiles


# Cached profiles (loaded once)
_profiles: dict[str, CognitiveProfile] | None = None


def get_cognitive_profile(level: str) -> CognitiveProfile:
    """
    Get the cognitive profile for a given organizational level.

    Falls back through: exact match → "staff" default → hardcoded default.
    """
    global _profiles
    if _profiles is None:
        _profiles = _load_profiles_from_config()

    return _profiles.get(level, _profiles.get("staff", _DEFAULT_PROFILES["staff"]))


def get_all_profiles() -> dict[str, CognitiveProfile]:
    """Return all loaded cognitive profiles."""
    global _profiles
    if _profiles is None:
        _profiles = _load_profiles_from_config()
    return dict(_profiles)


def child_level_for(parent_level: str) -> str:
    """
    Determine the appropriate child level when a parent delegates.

    Hierarchy: board → ceo → vp → director → manager → senior_staff → staff → intern
    """
    LEVEL_CHAIN = [
        "board", "ceo", "vp", "director", "manager",
        "senior_staff", "staff", "intern",
    ]
    try:
        idx = LEVEL_CHAIN.index(parent_level)
        return LEVEL_CHAIN[min(idx + 1, len(LEVEL_CHAIN) - 1)]
    except ValueError:
        return "staff"
