"""
Base Pydantic Schemas.

Core data models used across the system.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# ============================================================================
# Research State
# ============================================================================

class ResearchStatus(str, Enum):
    """Research job status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class QueryPath(str, Enum):
    """Research execution path."""
    MEMORY_FORK = "A"      # Incremental research from memory
    SHADOW_LAB = "B"       # Recalculation with new assumptions
    GRAND_SYNTHESIS = "C"  # Meta-analysis across topics
    DEEP_RESEARCH = "D"    # Zero-shot deep research


class ResearchState(BaseModel):
    """LangGraph state for research flow."""
    job_id: str
    query: str
    path: QueryPath = QueryPath.DEEP_RESEARCH
    status: ResearchStatus = ResearchStatus.PENDING
    
    # Planning
    sub_queries: list[str] = Field(default_factory=list)
    hypotheses: list[str] = Field(default_factory=list)
    
    # Execution
    facts: list["AtomicFact"] = Field(default_factory=list)
    sources: list["Source"] = Field(default_factory=list)
    artifacts: list[str] = Field(default_factory=list)  # Artifact IDs
    tool_invocations: list[dict] = Field(default_factory=list)  # Tool call records
    
    # Consensus
    generator_output: str = ""
    critic_feedback: str = ""
    judge_verdict: str = ""
    
    # Output
    report: str = ""
    confidence: float = 0.0
    
    # Metadata
    iteration: int = 0
    max_iterations: int = 3
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    error: str | None = None


# ============================================================================
# Atomic Fact Schema
# ============================================================================

class AtomicFact(BaseModel):
    """
    Atomic fact extracted from research.
    
    Represents a single, verifiable data point.
    """
    fact_id: str
    entity: str                    # What/who
    attribute: str                 # What property
    value: str                     # The data
    unit: str | None = None        # Unit of measurement
    period: str | None = None      # Time reference
    source_url: str                # Source URL
    source_title: str = ""         # Source title
    confidence_score: float = 0.8  # 0.0 - 1.0
    extracted_at: datetime = Field(default_factory=datetime.utcnow)


class Source(BaseModel):
    """Research source."""
    url: str
    title: str
    domain: str
    accessed_at: datetime = Field(default_factory=datetime.utcnow)
    content_hash: str = ""
    reliability_score: float = 0.5


# ============================================================================
# Job Request/Response
# ============================================================================

class JobType(str, Enum):
    """Job types."""
    DEEP_RESEARCH = "deep_research"
    MEMORY_FORK = "memory_fork"
    SHADOW_LAB = "shadow_lab"
    GRAND_SYNTHESIS = "grand_synthesis"
    QUICK_ANSWER = "quick_answer"  # Simple fact-based answers


class JobRequest(BaseModel):
    """Research job request."""
    query: str
    job_type: JobType = JobType.DEEP_RESEARCH
    depth: int = 2
    max_sources: int = 10
    domain_hints: list[str] = Field(default_factory=list)
    
    # For shadow lab
    artifact_id: str | None = None
    recalc_instruction: str | None = None
    
    # For grand synthesis
    topic_ids: list[str] | None = None


class JobResponse(BaseModel):
    """Research job response."""
    job_id: str
    status: ResearchStatus
    created_at: datetime
    updated_at: datetime | None = None
    progress: float = 0.0
    
    # Results (when completed)
    report: str | None = None
    facts_count: int = 0
    sources_count: int = 0
    artifact_ids: list[str] = Field(default_factory=list)
    confidence: float = 0.0
    
    # Error (when failed)
    error: str | None = None


# ============================================================================
# Tool Invocation
# ============================================================================

class ToolInvocation(BaseModel):
    """Record of a tool invocation."""
    tool_name: str
    server_name: str
    arguments: dict[str, Any]
    result: Any | None = None
    is_error: bool = False
    duration_ms: float = 0.0
    invoked_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# Session/Project
# ============================================================================

class SessionManifest(BaseModel):
    """Research session manifest."""
    session_id: str
    name: str
    description: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Related entities
    job_ids: list[str] = Field(default_factory=list)
    fact_ids: list[str] = Field(default_factory=list)
    artifact_ids: list[str] = Field(default_factory=list)
    
    # Metadata
    tags: list[str] = Field(default_factory=list)
    domain: str = ""


# ============================================================================
# Universal Node Protocol
# ============================================================================

class NodeOutput(BaseModel):
    """
    Standardized output from any Node/Tool in the system.
    Enables n8n-style communication and uniform memory storage.
    """
    trace_id: str = Field(description="Linking ID (Job ID or Trace ID)")
    source_node: str = Field(description="Name of the tool/node that produced this")
    content: dict[str, Any] = Field(description="Structured content (text, data, files)")
    metadata: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        extra = "allow"
