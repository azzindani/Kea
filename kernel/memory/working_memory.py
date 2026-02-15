"""
Working Memory for Kernel Cells.

Replaces the flat ``accumulated_content`` string with a structured,
human-inspired working memory system.  Every KernelCell owns a
WorkingMemory instance that tracks:

- **Focus Items** (~7 active items, Miller's Law).
- **Scratch Pad**   temporary notes, calculations, rough drafts.
- **Hypotheses**   active beliefs being evaluated.
- **Decisions**   choices made with rationale (audit trail).
- **Confidence Map**   per-topic confidence tracking.
- **Pending Questions**   queued for upward/lateral communication.

The memory can be *compressed* into a context-window-sized summary for
injection into LLM calls, and *serialised* for persistence into the
Vault or ArtifactStore.

Version: 0.4.0   Part of Kernel Brain Upgrade (Phase 1)
"""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any

from kernel.memory.error_journal import (
    ErrorEntry,
    ErrorJournal,
    FixAttempt,
    FixResult,
)
from kernel.io.output_schemas import (
    Artifact,
    ArtifactMetadata,
    ArtifactStatus,
    ArtifactType,
)
from shared.logging import get_logger

logger = get_logger(__name__)


# ============================================================================
# Enums
# ============================================================================


class FocusItemType(StrEnum):
    """What kind of thing is occupying attention."""

    FACT = "fact"
    HYPOTHESIS = "hypothesis"
    QUESTION = "question"
    OBSERVATION = "observation"
    TOOL_RESULT = "tool_result"
    SUB_PROBLEM = "sub_problem"
    DECISION = "decision"


class HypothesisStatus(StrEnum):
    """Hypothesis lifecycle."""

    PROPOSED = "proposed"
    SUPPORTED = "supported"
    WEAKENED = "weakened"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"


class QuestionTarget(StrEnum):
    """Who is the question directed at."""

    PARENT = "parent"
    PEER = "peer"
    SELF = "self"  # Rhetorical / needs-more-thought
    TOOL = "tool"  # Can be answered by a tool call


# ============================================================================
# Data Structures
# ============================================================================


@dataclass
class FocusItem:
    """A single item in working memory's focus buffer.

    Mirrors the psychological concept of a "chunk"   a unit of
    attention that can be a fact, a hypothesis, a sub-problem, etc.
    """

    id: str
    item_type: FocusItemType
    content: str
    relevance: float = 1.0  # 0 1, decays over time
    created_at: datetime = field(default_factory=datetime.utcnow)
    source: str = ""  # Where it came from (tool, step, cell)

    def decay(self, factor: float = 0.9) -> None:
        """Reduce relevance over time (items age out of focus)."""
        self.relevance *= factor


@dataclass
class Hypothesis:
    """An active hypothesis being evaluated during reasoning."""

    id: str
    statement: str
    status: HypothesisStatus = HypothesisStatus.PROPOSED
    confidence: float = 0.5  # 0 1
    supporting_evidence: list[str] = field(default_factory=list)
    contradicting_evidence: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)

    def support(self, evidence: str, boost: float = 0.1) -> None:
        """Add supporting evidence and increase confidence."""
        self.supporting_evidence.append(evidence)
        self.confidence = min(1.0, self.confidence + boost)
        if self.confidence >= 0.8:
            self.status = HypothesisStatus.CONFIRMED

    def weaken(self, evidence: str, penalty: float = 0.15) -> None:
        """Add contradicting evidence and decrease confidence."""
        self.contradicting_evidence.append(evidence)
        self.confidence = max(0.0, self.confidence - penalty)
        if self.confidence <= 0.2:
            self.status = HypothesisStatus.REJECTED
        elif self.status == HypothesisStatus.SUPPORTED:
            self.status = HypothesisStatus.WEAKENED


@dataclass
class Decision:
    """A decision made during reasoning   with explicit rationale.

    Decisions are immutable once made. They form the audit trail
    of *why* the cell chose a particular course of action.
    """

    id: str
    description: str
    rationale: str
    alternatives_considered: list[str] = field(default_factory=list)
    confidence: float = 0.5
    step_number: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class PendingQuestion:
    """A question the cell needs answered before it can proceed."""

    id: str
    question: str
    target: QuestionTarget
    context: str = ""
    priority: int = 1  # 1 = normal, 2 = important, 3 = blocking
    answered: bool = False
    answer: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)


class ArtifactManager:
    """
    Manages the collection of artifacts being produced by a cell.

    Tracks state transitions, versioning, and allows retrieving
    specific versions or the latest published artifacts.
    """

    def __init__(self, cell_id: str):
        self.cell_id = cell_id
        self._artifacts: dict[str, Artifact] = {}
        self._versions: dict[str, list[Artifact]] = defaultdict(list)

    def create_artifact(
        self,
        id: str,
        type: ArtifactType,
        title: str,
        content: str,
        summary: str = "",
        confidence: float = 0.5,
        metadata: ArtifactMetadata | None = None,
    ) -> Artifact:
        """Create a new artifact in DRAFT state."""
        artifact = Artifact(
            id=id,
            type=type,
            title=title,
            summary=summary,
            content=content,
            status=ArtifactStatus.DRAFT,
            version=1,
            confidence=confidence,
            metadata=metadata or ArtifactMetadata(),
            cell_id=self.cell_id,
            produced_at=datetime.utcnow().isoformat(),
        )
        self._artifacts[id] = artifact
        self._versions[id].append(artifact)
        logger.info(f"  Created artifact: {id} ({type.value}) - {title}")
        return artifact

    def update_artifact(
        self,
        id: str,
        content: str | None = None,
        summary: str | None = None,
        status: ArtifactStatus | None = None,
        confidence: float | None = None,
        metadata: ArtifactMetadata | None = None,
        new_version: bool = True,
    ) -> Artifact | None:
        """Update an existing artifact, optionally creating a new version."""
        if id not in self._artifacts:
            logger.warning(f"Artifact {id} not found for update.")
            return None

        current = self._artifacts[id]

        if new_version:
            # Create a new version
            updated = current.model_copy()
            updated.version += 1
            updated.parent_id = f"{id}-v{current.version}"
            updated.produced_at = datetime.utcnow().isoformat()

            if content is not None:
                updated.content = content
            if summary is not None:
                updated.summary = summary
            if status is not None:
                updated.status = status
            if confidence is not None:
                updated.confidence = confidence
            if metadata is not None:
                updated.metadata = metadata

            self._artifacts[id] = updated
            self._versions[id].append(updated)
            logger.info(
                f"  Updated artifact {id} to version {updated.version} (status: {updated.status.value})"
            )
            return updated
        else:
            # Update in-place
            if content is not None:
                current.content = content
            if summary is not None:
                current.summary = summary
            if status is not None:
                current.status = status
            if confidence is not None:
                current.confidence = confidence
            if metadata is not None:
                current.metadata = metadata

            logger.info(f"  Updated artifact {id} in-place (status: {current.status.value})")
            return current

    def get_artifact(self, id: str) -> Artifact | None:
        """Get the latest version of an artifact."""
        return self._artifacts.get(id)

    def get_published(self) -> list[Artifact]:
        """Get all artifacts in PUBLISHED state."""
        return [a for a in self._artifacts.values() if a.status == ArtifactStatus.PUBLISHED]

    def get_all_latest(self) -> list[Artifact]:
        """Get the latest version of all artifacts regardless of status."""
        return list(self._artifacts.values())

    def transition_all(self, from_status: ArtifactStatus, to_status: ArtifactStatus):
        """Transition all artifacts from one status to another."""
        for artifact in self._artifacts.values():
            if artifact.status == from_status:
                artifact.status = to_status


# ============================================================================
# Fix Pattern (Cross-Iteration Learning)
# ============================================================================


@dataclass
class FixPattern:
    """A learned pattern: 'when you see error X, try fix Y'.

    Persists across healing iterations and can be stored in Vault
    for cross-session learning.
    """

    error_signature: str  # Generalised error pattern
    successful_fix: str  # Strategy that worked
    frequency: int = 1  # How often this pattern has succeeded
    last_seen: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    domains: set[str] = field(default_factory=set)


# ============================================================================
# Working Memory
# ============================================================================


class WorkingMemory:
    """
    Structured working memory for a kernel cell.

    Models the human cognitive capacity limit (~7 active items) with
    explicit mechanisms for focus management, hypothesis evaluation,
    decision recording, and scratch-pad note-taking.

    Usage::

        mem = WorkingMemory(cell_id="analyst-42")

        # Add items to focus
        mem.focus(FocusItem(id="f1", item_type=FocusItemType.FACT,
                            content="Tesla Q4 revenue was $25.2B"))

        # Take notes
        mem.note("revenue_comparison", "TSLA $25.2B vs RIVN $1.7B")

        # Track hypotheses
        mem.propose_hypothesis("h1", "Tesla will maintain >50% US EV market share")
        mem.support_hypothesis("h1", "Current share is 57% and growing")

        # Record decisions
        mem.decide("d1", "Focus analysis on top 3 competitors",
                   rationale="Budget constrains full market coverage",
                   alternatives=["All 10 competitors", "Top 5"])

        # Compress for LLM context
        summary = mem.compress(max_tokens=2000)
    """

    # Maximum active focus items (Miller's Law)
    MAX_FOCUS_ITEMS: int = 7

    # Maximum recent entries kept in scratch pad
    MAX_SCRATCH_ENTRIES: int = 30

    def __init__(self, cell_id: str, max_focus: int = 7) -> None:
        self.cell_id = cell_id
        self.MAX_FOCUS_ITEMS = max_focus

        #   Focus Buffer  
        # Currently active items (bounded, LRU-evicts old ones)
        self._focus: deque[FocusItem] = deque(maxlen=self.MAX_FOCUS_ITEMS)

        #   Scratch Pad  
        # Temporary notes, calculations, rough ideas (key   content)
        self._scratch: dict[str, str] = {}

        #   Hypotheses  
        # Active hypotheses being evaluated
        self._hypotheses: dict[str, Hypothesis] = {}

        #   Decisions  
        # Decisions made (append-only audit trail)
        self._decisions: list[Decision] = []

        #   Confidence Map  
        # Per-topic confidence tracking (topic   confidence 0 1)
        self._confidence_map: dict[str, float] = {}

        #   Pending Questions  
        # Questions for others (queued for communication phase)
        self._pending_questions: list[PendingQuestion] = []

        #   Accumulated Facts  
        # Structured facts gathered during execution (key   content)
        self._facts: dict[str, str] = {}

        #   Artifact Manager (Phase 5)  
        self.artifacts = ArtifactManager(cell_id)

        #   Error Journal (Recursive Self-Healing)  
        self.error_journal = ErrorJournal()

        #   Fix Patterns (Cross-Iteration Learning)  
        self._fix_patterns: list[FixPattern] = []

        #   Step counter  
        self._step_count: int = 0

    # ================================================================ #
    # Focus Management
    # ================================================================ #

    def focus(self, item: FocusItem) -> None:
        """Push an item into focus, evicting oldest if at capacity."""
        # Decay existing items slightly
        for existing in self._focus:
            existing.decay(factor=0.95)

        self._focus.append(item)
        logger.debug(
            f"WM[{self.cell_id}] focus: +{item.item_type.value} "
            f"({len(self._focus)}/{self.MAX_FOCUS_ITEMS})"
        )

    def focus_fact(self, fact_id: str, content: str, source: str = "") -> None:
        """Convenience: add a fact to focus."""
        self.focus(
            FocusItem(
                id=fact_id,
                item_type=FocusItemType.FACT,
                content=content,
                source=source,
            )
        )

    def focus_observation(self, obs_id: str, content: str, source: str = "") -> None:
        """Convenience: add an observation to focus."""
        self.focus(
            FocusItem(
                id=obs_id,
                item_type=FocusItemType.OBSERVATION,
                content=content,
                source=source,
            )
        )

    @property
    def current_focus(self) -> list[FocusItem]:
        """Currently focused items, sorted by relevance (highest first)."""
        return sorted(self._focus, key=lambda i: i.relevance, reverse=True)

    @property
    def focus_summary(self) -> str:
        """One-line summary of what's currently in focus."""
        items = self.current_focus
        if not items:
            return "Nothing in focus"
        return " | ".join(f"[{i.item_type.value}] {i.content[:60]}" for i in items[:5])

    # ================================================================ #
    # Scratch Pad
    # ================================================================ #

    def note(self, key: str, content: str) -> None:
        """Write a note to the scratch pad."""
        self._scratch[key] = content
        # Evict oldest entries if too many
        if len(self._scratch) > self.MAX_SCRATCH_ENTRIES:
            oldest_key = next(iter(self._scratch))
            del self._scratch[oldest_key]

    def get_note(self, key: str) -> str:
        """Retrieve a scratch pad note."""
        return self._scratch.get(key, "")

    @property
    def scratch_pad(self) -> dict[str, str]:
        """Read-only access to the scratch pad."""
        return dict(self._scratch)

    # ================================================================ #
    # Hypothesis Management
    # ================================================================ #

    def propose_hypothesis(
        self,
        hypothesis_id: str,
        statement: str,
        initial_confidence: float = 0.5,
    ) -> Hypothesis:
        """Propose a new hypothesis."""
        h = Hypothesis(
            id=hypothesis_id,
            statement=statement,
            confidence=initial_confidence,
        )
        self._hypotheses[hypothesis_id] = h
        self.focus(
            FocusItem(
                id=f"hyp_{hypothesis_id}",
                item_type=FocusItemType.HYPOTHESIS,
                content=statement,
            )
        )
        return h

    def support_hypothesis(self, hypothesis_id: str, evidence: str) -> None:
        """Add supporting evidence to a hypothesis."""
        if hypothesis_id in self._hypotheses:
            self._hypotheses[hypothesis_id].support(evidence)

    def weaken_hypothesis(self, hypothesis_id: str, evidence: str) -> None:
        """Add contradicting evidence to a hypothesis."""
        if hypothesis_id in self._hypotheses:
            self._hypotheses[hypothesis_id].weaken(evidence)

    @property
    def active_hypotheses(self) -> list[Hypothesis]:
        """Hypotheses that are still being evaluated."""
        return [
            h
            for h in self._hypotheses.values()
            if h.status
            in (HypothesisStatus.PROPOSED, HypothesisStatus.SUPPORTED, HypothesisStatus.WEAKENED)
        ]

    @property
    def confirmed_hypotheses(self) -> list[Hypothesis]:
        """Hypotheses that have been confirmed."""
        return [h for h in self._hypotheses.values() if h.status == HypothesisStatus.CONFIRMED]

    # ================================================================ #
    # Decision Recording
    # ================================================================ #

    def decide(
        self,
        decision_id: str,
        description: str,
        rationale: str,
        alternatives: list[str] | None = None,
        confidence: float = 0.7,
    ) -> Decision:
        """Record a decision with rationale."""
        d = Decision(
            id=decision_id,
            description=description,
            rationale=rationale,
            alternatives_considered=alternatives or [],
            confidence=confidence,
            step_number=self._step_count,
        )
        self._decisions.append(d)
        return d

    @property
    def decisions(self) -> list[Decision]:
        """All decisions in chronological order."""
        return list(self._decisions)

    # ================================================================ #
    # Confidence Tracking
    # ================================================================ #

    def set_confidence(self, topic: str, confidence: float) -> None:
        """Set confidence level for a specific topic."""
        self._confidence_map[topic] = max(0.0, min(1.0, confidence))

    def get_confidence(self, topic: str) -> float:
        """Get confidence for a topic (default 0.5 if unknown)."""
        return self._confidence_map.get(topic, 0.5)

    @property
    def overall_confidence(self) -> float:
        """Average confidence across all tracked topics."""
        if not self._confidence_map:
            return 0.5
        return sum(self._confidence_map.values()) / len(self._confidence_map)

    @property
    def low_confidence_topics(self) -> list[tuple[str, float]]:
        """Topics where confidence is below 0.5."""
        return [(topic, conf) for topic, conf in self._confidence_map.items() if conf < 0.5]

    # ================================================================ #
    # Pending Questions
    # ================================================================ #

    def ask(
        self,
        question_id: str,
        question: str,
        target: QuestionTarget = QuestionTarget.SELF,
        context: str = "",
        priority: int = 1,
    ) -> PendingQuestion:
        """Queue a question that needs answering."""
        q = PendingQuestion(
            id=question_id,
            question=question,
            target=target,
            context=context,
            priority=priority,
        )
        self._pending_questions.append(q)
        return q

    def answer_question(self, question_id: str, answer: str) -> None:
        """Mark a pending question as answered."""
        for q in self._pending_questions:
            if q.id == question_id:
                q.answered = True
                q.answer = answer
                break

    @property
    def unanswered_questions(self) -> list[PendingQuestion]:
        """Questions still waiting for answers."""
        return [q for q in self._pending_questions if not q.answered]

    @property
    def blocking_questions(self) -> list[PendingQuestion]:
        """High-priority unanswered questions that may block progress."""
        return [q for q in self._pending_questions if not q.answered and q.priority >= 3]

    # ================================================================ #
    # Facts Store
    # ================================================================ #

    def store_fact(self, key: str, content: str) -> None:
        """Store a gathered fact."""
        self._facts[key] = content

    def get_fact(self, key: str) -> str:
        """Retrieve a stored fact."""
        return self._facts.get(key, "")

    @property
    def all_facts(self) -> dict[str, str]:
        """All gathered facts."""
        return dict(self._facts)

    @property
    def fact_count(self) -> int:
        """Number of facts gathered."""
        return len(self._facts)

    # ================================================================ #
    # Step Tracking
    # ================================================================ #

    def advance_step(self) -> int:
        """Advance the step counter and decay focus items."""
        self._step_count += 1
        for item in self._focus:
            item.decay(factor=0.92)
        return self._step_count

    @property
    def step_count(self) -> int:
        """Current step number."""
        return self._step_count

    # ================================================================ #
    # Compression & Serialisation
    # ================================================================ #

    def compress(self, max_chars: int = 4000) -> str:
        """
        Compress working memory into an LLM-ingestible summary.

        Prioritises: focus items > hypotheses > recent decisions > notes.
        Stays within ``max_chars`` to fit in context windows.
        """
        sections: list[str] = []
        budget = max_chars

        #   Focus (highest priority)  
        focus_items = self.current_focus
        if focus_items:
            lines = []
            for item in focus_items:
                line = f"- [{item.item_type.value}] {item.content}"
                lines.append(line[:200])
            section = "CURRENT FOCUS:\n" + "\n".join(lines)
            sections.append(section)
            budget -= len(section)

        #   Active Hypotheses  
        active = self.active_hypotheses
        if active and budget > 200:
            lines = []
            for h in active[:5]:
                lines.append(
                    f"- {h.statement} (conf={h.confidence:.2f}, "
                    f"support={len(h.supporting_evidence)}, "
                    f"contra={len(h.contradicting_evidence)})"
                )
            section = "ACTIVE HYPOTHESES:\n" + "\n".join(lines)
            sections.append(section)
            budget -= len(section)

        #   Gathered Facts (abbreviated)  
        if self._facts and budget > 200:
            lines = []
            for key, content in list(self._facts.items())[:10]:
                lines.append(f"- {key}: {content[:120]}")
            section = f"GATHERED FACTS ({self.fact_count} total):\n" + "\n".join(lines)
            sections.append(section)
            budget -= len(section)

        #   Recent Decisions  
        if self._decisions and budget > 200:
            lines = []
            for d in self._decisions[-5:]:
                lines.append(f"- {d.description} (reason: {d.rationale[:80]})")
            section = "RECENT DECISIONS:\n" + "\n".join(lines)
            sections.append(section)
            budget -= len(section)

        #   Confidence Map  
        low_conf = self.low_confidence_topics
        if low_conf and budget > 100:
            lines = [f"- {t}: {c:.2f}" for t, c in low_conf[:5]]
            section = "LOW-CONFIDENCE AREAS:\n" + "\n".join(lines)
            sections.append(section)
            budget -= len(section)

        #   Scratch Pad (only if space left)  
        if self._scratch and budget > 200:
            lines = []
            for key, val in list(self._scratch.items())[-5:]:
                lines.append(f"- {key}: {val[:100]}")
            section = "NOTES:\n" + "\n".join(lines)
            sections.append(section)

        #   Pending Questions  
        unanswered = self.unanswered_questions
        if unanswered and budget > 100:
            lines = [f"- [{q.target.value}] {q.question[:80]}" for q in unanswered[:3]]
            section = "OPEN QUESTIONS:\n" + "\n".join(lines)
            sections.append(section)
            budget -= len(section)

        #   Error Journal (Recursive Self-Healing)  
        error_summary = self.error_journal.compress_for_llm(max_chars=min(500, budget))
        if error_summary:
            sections.append(error_summary)

        return "\n\n".join(sections)

    def to_dict(self) -> dict[str, Any]:
        """Serialise working memory to a dict (for persistence)."""
        return {
            "cell_id": self.cell_id,
            "step_count": self._step_count,
            "focus_count": len(self._focus),
            "facts_count": self.fact_count,
            "hypotheses": {
                hid: {
                    "statement": h.statement,
                    "status": h.status.value,
                    "confidence": h.confidence,
                }
                for hid, h in self._hypotheses.items()
            },
            "decisions_count": len(self._decisions),
            "confidence_map": dict(self._confidence_map),
            "unanswered_questions": len(self.unanswered_questions),
            "overall_confidence": self.overall_confidence,
            "error_journal": self.error_journal.to_dict(),
            "fix_patterns_count": len(self._fix_patterns),
        }

    # ================================================================ #
    # Quality Signals (for self-monitoring)
    # ================================================================ #

    def detect_repetition(self, new_content: str, threshold: float = 0.3) -> bool:
        """
        Check if new content is too similar to existing facts/notes.

        Uses simple word-overlap as a cheap heuristic (no embeddings).
        Returns True if repetition exceeds threshold.
        """
        if not self._facts:
            return False

        new_words = set(new_content.lower().split())
        if not new_words:
            return False

        max_overlap = 0.0
        for existing in self._facts.values():
            existing_words = set(existing.lower().split())
            if not existing_words:
                continue
            overlap = len(new_words & existing_words) / len(new_words)
            max_overlap = max(max_overlap, overlap)

        return max_overlap >= threshold

    def detect_drift(self, original_task: str) -> float:
        """
        Estimate how far the current focus has drifted from the task.

        Returns 0.0 (fully on-track) to 1.0 (completely off-topic).
        Simple heuristic: word overlap between task and focus items.
        """
        task_words = set(original_task.lower().split())
        if not task_words or not self._focus:
            return 0.0

        focus_text = " ".join(item.content for item in self._focus)
        focus_words = set(focus_text.lower().split())
        if not focus_words:
            return 1.0

        overlap = len(task_words & focus_words) / len(task_words)
        return max(0.0, 1.0 - overlap)

    # ================================================================ #
    # Fix Pattern Learning (Recursive Self-Healing)
    # ================================================================ #

    def learn_fix(self, error: ErrorEntry, fix: FixAttempt) -> None:
        """Learn a successful fix pattern for future use."""
        if fix.result != FixResult.SUCCESS:
            return

        signature = self._generalise_error(error)
        # Check for existing pattern
        for pattern in self._fix_patterns:
            if pattern.error_signature == signature:
                pattern.frequency += 1
                pattern.last_seen = datetime.utcnow().isoformat()
                return

        self._fix_patterns.append(
            FixPattern(
                error_signature=signature,
                successful_fix=fix.strategy,
                frequency=1,
            )
        )

    def suggest_fix(self, error: ErrorEntry) -> str | None:
        """Suggest a fix based on learned patterns."""
        signature = self._generalise_error(error)
        for pattern in sorted(self._fix_patterns, key=lambda p: p.frequency, reverse=True):
            if self._signatures_match(signature, pattern.error_signature):
                return pattern.successful_fix
        return None

    @property
    def fix_patterns(self) -> list[FixPattern]:
        """All learned fix patterns."""
        return list(self._fix_patterns)

    @staticmethod
    def _generalise_error(error: ErrorEntry) -> str:
        """Generalise an error into a reusable signature."""
        parts = [error.source.value, error.error_type]
        # Strip specifics (UUIDs, numbers) from message
        msg = error.message[:100]
        for char in "0123456789":
            msg = msg.replace(char, "#")
        parts.append(msg)
        return "|".join(parts)

    @staticmethod
    def _signatures_match(a: str, b: str) -> bool:
        """Check if two error signatures are similar enough."""
        if a == b:
            return True
        # Split into parts and check component overlap
        parts_a = set(a.split("|"))
        parts_b = set(b.split("|"))
        if not parts_a or not parts_b:
            return False
        overlap = len(parts_a & parts_b) / max(len(parts_a), len(parts_b))
        return overlap >= 0.6

    def detect_stagnation(self, last_n_facts: int = 3) -> bool:
        """
        Check if the last N facts are suspiciously similar (going in circles).
        """
        fact_values = list(self._facts.values())
        if len(fact_values) < last_n_facts:
            return False

        recent = fact_values[-last_n_facts:]
        # Check pairwise similarity of recent facts
        for i, a in enumerate(recent):
            for b in recent[i + 1 :]:
                a_words = set(a.lower().split())
                b_words = set(b.lower().split())
                if a_words and b_words:
                    overlap = len(a_words & b_words) / max(len(a_words), len(b_words))
                    if overlap > 0.6:
                        return True
        return False
