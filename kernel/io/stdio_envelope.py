"""
Standard I/O Envelope for Kernel Cells.

Every kernel cell communicates using structured envelopes   the universal
contract between processing stages, inspired by Unix stdin/stdout/stderr.

This replaces unstructured dict passing with typed, validated data flow.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from kernel.io.output_schemas import Artifact, WorkPackage

# ============================================================================
# Envelop Enums
# ============================================================================


class QualityLevel(str, Enum):
    """Expected output quality level."""

    DRAFT = "draft"
    PROFESSIONAL = "professional"
    EXECUTIVE = "executive"


class DeliverableFormat(str, Enum):
    """Format of the primary deliverable."""

    TEXT = "text"
    JSON = "json"
    TABLE = "table"
    REPORT = "report"
    CODE = "code"
    STRUCTURED_DATA = "structured_data"


class MessageType(str, Enum):
    """Communication message types between kernel cells."""

    # Top-Down
    DELEGATE = "delegate"
    CLARIFY = "clarify"
    REDIRECT = "redirect"
    CANCEL = "cancel"

    # Bottom-Up
    REPORT = "report"
    ESCALATE = "escalate"
    REQUEST_RESOURCE = "request_resource"
    FLAG = "flag"

    # Lateral
    CONSULT = "consult"
    SHARE = "share"
    COORDINATE = "coordinate"
    HANDOFF = "handoff"


class WarningSeverity(str, Enum):
    """Severity level for warnings."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# ============================================================================
# Stdin   Instruction + Context + Constraints
# ============================================================================


class Instruction(BaseModel):
    """The task instruction for a kernel cell."""

    text: str = Field(description="Plain-text instruction")
    intent: str = Field(default="", description="Classified intent of the instruction")
    urgency: str = Field(default="normal", description="Urgency: low | normal | high | critical")


class TaskContext(BaseModel):
    """Contextual information passed to a kernel cell."""

    parent_task_id: str | None = Field(default=None, description="ID of the parent task")
    organizational_goal: str = Field(default="", description="High-level goal from above")
    prior_findings: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Previously collected facts/findings",
    )
    error_feedback: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Errors from previous attempts to avoid repeating",
    )
    domain_hints: list[str] = Field(
        default_factory=list,
        description="Domains relevant to this task",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional contextual metadata",
    )


class Constraints(BaseModel):
    """Resource and quality constraints for a kernel cell."""

    time_budget_ms: int = Field(default=30_000, description="Max time in milliseconds")
    token_budget: int = Field(default=10_000, description="Max token budget")
    quality_level: QualityLevel = Field(
        default=QualityLevel.PROFESSIONAL,
        description="Expected output quality",
    )
    max_delegation_depth: int = Field(default=3, description="Max depth for recursive delegation")


class Authority(BaseModel):
    """What the kernel cell is allowed to do."""

    can_delegate: bool = Field(default=True, description="Can spawn child cells")
    can_escalate: bool = Field(default=True, description="Can push problems up to parent")
    tool_access: list[str] = Field(
        default_factory=list,
        description="Tool name patterns this cell can use (supports wildcards)",
    )
    budget_tokens: int = Field(default=10_000, description="Total token budget for this cell")


class StdinEnvelope(BaseModel):
    """Standard input: the instruction + context + constraints."""

    instruction: Instruction
    context: TaskContext = Field(default_factory=TaskContext)
    constraints: Constraints = Field(default_factory=Constraints)
    authority: Authority = Field(default_factory=Authority)


# ============================================================================
# Stdout   Primary Deliverable
# ============================================================================


class DeliverableSection(BaseModel):
    """A section of the deliverable output."""

    title: str
    content: str
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    sources: list[str] = Field(default_factory=list)
    data_gaps: list[str] = Field(default_factory=list)


class KeyFinding(BaseModel):
    """A single key finding from the analysis."""

    finding: str
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    evidence_strength: str = Field(default="moderate", description="weak | moderate | strong")


class StdoutEnvelope(BaseModel):
    """Standard output: the primary deliverable."""

    format: DeliverableFormat = Field(default=DeliverableFormat.TEXT)
    content: str = Field(default="", description="Primary output content")
    sections: list[DeliverableSection] = Field(default_factory=list)
    summary: str = Field(default="", description="One-paragraph executive summary")
    key_findings: list[KeyFinding] = Field(default_factory=list)
    work_package: WorkPackage | None = Field(
        default=None, description="Structured work package (v2.0)"
    )


# ============================================================================
# Stderr   Warnings, Failures, Escalations
# ============================================================================


class Warning(BaseModel):
    """A warning produced during processing."""

    type: str = Field(
        description="Warning type: data_gap | low_confidence | tool_failure | timeout"
    )
    message: str
    severity: WarningSeverity = Field(default=WarningSeverity.MEDIUM)


class Failure(BaseModel):
    """A failure that occurred during processing."""

    task_id: str = Field(default="")
    error: str
    recovery_action: str = Field(default="", description="What was done to recover")


class Escalation(BaseModel):
    """A problem that needs to be escalated to a higher level."""

    type: str = Field(description="needs_human_review | authority_exceeded | conflicting_data")
    reason: str
    context: dict[str, Any] = Field(default_factory=dict)


class StderrEnvelope(BaseModel):
    """Standard error: warnings, failures, and escalations."""

    warnings: list[Warning] = Field(default_factory=list)
    failures: list[Failure] = Field(default_factory=list)
    escalations: list[Escalation] = Field(default_factory=list)

    @property
    def has_critical(self) -> bool:
        """Check if there are any critical warnings."""
        return any(w.severity == WarningSeverity.CRITICAL for w in self.warnings)


# ============================================================================
# Artifacts
# ============================================================================


class ArtifactVisibility(str, Enum):
    """Visibility scope for artifacts."""

    PERSONAL = "personal"
    TEAM = "team"
    DEPARTMENT = "department"
    ORGANIZATION = "organization"


class ArtifactReference(BaseModel):
    """Reference to an artifact produced by a kernel cell."""

    name: str
    type: str = Field(
        description="Type: structured_data | tabular_data | working_document | report"
    )
    visibility: ArtifactVisibility = Field(default=ArtifactVisibility.TEAM)
    content: Any = Field(default=None, description="Inline content (for small artifacts)")
    size_bytes: int = Field(default=0)


# ============================================================================
# Metadata
# ============================================================================


class EnvelopeMetadata(BaseModel):
    """Metadata for the envelope: timing, cost, confidence."""

    cell_id: str = Field(default="")
    level: str = Field(default="staff")
    role: str = Field(default="")
    domain: str = Field(default="")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    tokens_used: int = Field(default=0)
    tokens_remaining: int = Field(default=0)
    duration_ms: float = Field(default=0.0)
    children_count: int = Field(default=0)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Communication stats (v2.0)
    messages_sent: int = Field(default=0)
    messages_received: int = Field(default=0)
    comm_tokens_spent: int = Field(default=0)
    clarifications_resolved: int = Field(default=0)

    # Self-healing stats (v2.1)
    heal_errors_fixed: int = Field(default=0)
    heal_errors_remaining: int = Field(default=0)
    heal_cascade_depth: int = Field(default=0)


# ============================================================================
# The Complete Envelope
# ============================================================================


class StdioEnvelope(BaseModel):
    """
    The complete standard I/O envelope for kernel cell communication.

    Every kernel cell receives a StdioEnvelope as input and produces
    a StdioEnvelope as output. This is the universal contract.

    Usage:
        # Create input envelope
        input_env = StdioEnvelope(
            stdin=StdinEnvelope(
                instruction=Instruction(text="Analyze AAPL financials"),
            ),
        )

        # Process and return output
        output_env = StdioEnvelope(
            stdout=StdoutEnvelope(content="AAPL analysis..."),
            stderr=StderrEnvelope(warnings=[...]),
            metadata=EnvelopeMetadata(cell_id="analyst-001", confidence=0.85),
        )
    """

    stdin: StdinEnvelope | None = Field(default=None, description="Input instruction")
    stdout: StdoutEnvelope = Field(default_factory=StdoutEnvelope, description="Primary output")
    stderr: StderrEnvelope = Field(default_factory=StderrEnvelope, description="Warnings/errors")
    artifacts: list[Artifact] = Field(default_factory=list, description="Produced artifacts (v2.0)")
    metadata: EnvelopeMetadata = Field(
        default_factory=EnvelopeMetadata, description="Processing metadata"
    )

    # Communication
    message_type: MessageType = Field(
        default=MessageType.REPORT,
        description="Type of communication this envelope represents",
    )

    class Config:
        extra = "allow"
