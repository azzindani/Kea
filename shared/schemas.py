"""
Base Pydantic Schemas.

Core data models used across the system.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, TypedDict

from pydantic import BaseModel, Field


class AuditEventType(str, Enum):
    """Types of auditable events."""

    # Query lifecycle
    QUERY_RECEIVED = "query_received"
    QUERY_CLASSIFIED = "query_classified"
    QUERY_COMPLETED = "query_completed"

    # Tool operations
    TOOL_CALLED = "tool_called"
    TOOL_RESULT = "tool_result"
    TOOL_ERROR = "tool_error"

    # Data operations
    DATA_ACCESSED = "data_accessed"
    DATA_MODIFIED = "data_modified"
    DATA_DELETED = "data_deleted"

    # Decisions
    DECISION_MADE = "decision_made"
    DECISION_OVERRIDDEN = "decision_overridden"

    # Human in the loop
    ESCALATION_CREATED = "escalation_created"
    ESCALATION_RESOLVED = "escalation_resolved"
    APPROVAL_REQUESTED = "approval_requested"
    APPROVAL_GRANTED = "approval_granted"
    APPROVAL_DENIED = "approval_denied"

    # Security
    SECURITY_CHECK = "security_check"
    SECURITY_VIOLATION = "security_violation"
    ACCESS_DENIED = "access_denied"

    # System
    SYSTEM_START = "system_start"
    SYSTEM_STOP = "system_stop"
    CONFIG_CHANGED = "config_changed"
    ERROR = "error"

from shared.mcp.protocol import (
    ToolResult, TextContent, ImageContent, 
    JSONContent, FileContent
)

# ============================================================================
# Execution State
# ============================================================================


class AtomicInsight(BaseModel):
    """
    Atomic Insight (Entity-Attribute-Value).
    
    The foundational granular finding for the system.
    """

    insight_id: str = Field(default="", description="Unique identifier")
    entity: str = Field(..., description="Subject of the insight")
    attribute: str = Field(..., description="Property described")
    value: str = Field(..., description="Measured or stated value")
    unit: str | None = Field(default=None, description="Units of measurement")
    period: str | None = Field(default=None, description="Time period applicable")
    origin_url: str = Field(..., description="Originating URL")
    origin_title: str = Field(default="", description="Originating document title")
    confidence_score: float = Field(default=0.8, ge=0.0, le=1.0)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class JobStatus(str, Enum):
    """System job status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# ============================================================================
# Core Models
# ============================================================================


class Origin(BaseModel):
    """Information origin."""

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

    AUTONOMOUS = "autonomous"
    TASK = "task"
    INTERACTIVE = "interactive"


class JobRequest(BaseModel):
    """General task/job request."""

    query: str
    job_type: JobType = JobType.AUTONOMOUS
    depth: int = 2
    max_steps: int = 20
    context_hints: list[str] = Field(default_factory=list)


class JobResponse(BaseModel):
    """General task response."""

    job_id: str
    status: JobStatus
    created_at: datetime
    updated_at: datetime | None = None
    progress: float = 0.0

    # Results (when completed)
    output: str | None = None
    steps_count: int = 0
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
# Standard I/O for Tool Communication (n8n-style)
# ============================================================================


class FileType(str, Enum):
    """Supported file types for tool I/O."""

    CSV = "csv"
    JSON = "json"
    PARQUET = "parquet"
    EXCEL = "xlsx"
    PDF = "pdf"
    IMAGE = "image"
    TEXT = "text"
    BINARY = "binary"
    DATAFRAME = "dataframe"  # In-memory pandas DataFrame reference


class FileReference(BaseModel):
    """
    Reference to a file that can be passed between tools.
    Supports both local paths and in-memory data.
    """

    file_id: str = Field(description="Unique identifier for this file")
    file_type: FileType = Field(description="Type of file content")
    path: str | None = Field(default=None, description="Local file path if persisted")
    url: str | None = Field(default=None, description="Remote URL if available")
    content_preview: str | None = Field(default=None, description="First N chars for display")
    size_bytes: int = Field(default=0, description="File size in bytes")
    encoding: str = Field(default="utf-8", description="Text encoding")

    # For DataFrames - column info
    columns: list[str] | None = Field(default=None, description="Column names for tabular data")
    row_count: int | None = Field(default=None, description="Row count for tabular data")

    class Config:
        extra = "allow"


class DataPayload(BaseModel):
    """
    Structured data payload for tool I/O.
    Replaces raw dict with typed structure.
    """

    data_type: str = Field(description="Type hint (e.g., 'list[dict]', 'dict', 'str')")
    data: Any = Field(description="The actual data")
    schema_hint: dict[str, Any] | None = Field(
        default=None, description="JSON Schema for validation"
    )

    # Convenience fields for common types
    is_list: bool = Field(default=False, description="True if data is a list")
    item_count: int = Field(default=0, description="Number of items if list")


class ToolOutput(BaseModel):
    """
    Comprehensive output from any MCP tool.

    Enables n8n-style data passing between tools:
    - Text output for display
    - Structured data for processing
    - File references for large data
    - Suggested next inputs for chaining

    Example:
        # Tool A returns stock data
        output = ToolOutput(
            text="Found 800 tickers",
            data=DataPayload(data_type="list[str]", data=tickers, is_list=True, item_count=800),
            files=[FileReference(file_id="tickers.csv", file_type=FileType.CSV, path="/tmp/tickers.csv")],
            next_input={"tool": "fetch_stock_data", "args": {"tickers": "$data"}}
        )

        # Tool B can consume this directly
        # The orchestrator substitutes $data with the actual data
    """

    # Primary text content (for LLM/display)
    text: str | None = Field(default=None, description="Human-readable text output")

    # Structured data (for processing)
    data: DataPayload | None = Field(default=None, description="Structured data payload")

    # File references (for large data)
    files: list[FileReference] = Field(default_factory=list, description="File references")

    # Suggested next tool input (n8n-style chaining)
    next_input: dict[str, Any] | None = Field(
        default=None,
        description="Suggested input for next tool. Use $data, $files[0], etc. as placeholders",
    )

    # Metadata
    tool_name: str = Field(default="", description="Name of tool that produced this")
    execution_time_ms: float = Field(default=0.0, description="Execution time in milliseconds")
    success: bool = Field(default=True, description="Whether tool executed successfully")
    error: str | None = Field(default=None, description="Error message if failed")

    def get_for_llm(self) -> str:
        """Get text representation for LLM consumption."""
        if self.text:
            return self.text
        if self.data:
            # Summarize data
            summary = f"Data: {self.data.data_type}"
            if self.data.is_list:
                summary += f" ({self.data.item_count} items)"
            return summary
        if self.files:
            return f"Files: {[f.file_id for f in self.files]}"
        return "(empty output)"

    def get_data_value(self) -> Any:
        """Get the raw data value for tool chaining."""
        if self.data:
            return self.data.data
        return None

    class Config:
        extra = "allow"
# ============================================================================
# MCP Tool Communication Models
# ============================================================================


class ToolRequest(BaseModel):
    """Single tool execution request."""
    tool_name: str
    arguments: dict[str, Any] = Field(default_factory=dict)


class ToolSearchRequest(BaseModel):
    """Semantic tool search request — used to discover relevant tools via RAG."""

    query: str = Field(
        ...,
        min_length=1,
        description="Natural-language task description for semantic matching",
    )
    limit: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Max number of tools to return",
    )
    min_similarity: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Minimum cosine similarity score (0.0-1.0)",
    )


class BatchToolRequest(BaseModel):
    """Batch tool execution request."""
    tasks: list[ToolRequest]


class ToolResponse(BaseModel):
    """
    Standardized tool response wrapper.
    
    Prevents LLM confusion by normalizing diverse outputs.
    """
    tool_name: str
    output: ToolOutput  # Use the shared comprehensive schema
    is_error: bool = False
    
    @classmethod
    def from_mcp_result(cls, tool_name: str, result: ToolResult) -> "ToolResponse":
        """Convert raw MCP ToolResult to standardized ToolResponse."""
        
        # 1. Aggregate Text (stdout/display)
        text_parts = [
            c.text for c in result.content 
            if isinstance(c, TextContent)
        ]
        text_display = "\n".join(text_parts) if text_parts else None

        # 2. Extract Structured Data (JSON)
        data_payload = None
        for c in result.content:
            if isinstance(c, JSONContent):
                # Found structured data
                data_payload = DataPayload(
                    data_type=type(c.data).__name__,
                    data=c.data,
                    is_list=isinstance(c.data, list),
                    item_count=len(c.data) if isinstance(c.data, list) else 0
                )
                break # Take first JSON block as primary data

        # 3. Extract Files (Images/Binaries/FileRefs)
        files_list = []
        
        # A. Embedded Images
        for i, c in enumerate(result.content):
            if isinstance(c, ImageContent):
                files_list.append(FileReference(
                    file_id=f"image_{i}_{datetime.utcnow().timestamp()}",
                    file_type=FileType.IMAGE,
                    content_preview="[Embedded Image]",
                    size_bytes=len(c.data) # Approximate base64 length
                ))
        
        # B. Explicit FileRefs
        for c in result.content:
            if isinstance(c, FileContent):
                files_list.append(FileReference(
                    file_id=__import__("pathlib").Path(c.path).name,
                    file_type=FileType.BINARY, # Generic fallback
                    path=c.path,
                    size_bytes=c.size_bytes
                ))

        # 4. Construct Output
        tool_output = ToolOutput(
            text=text_display,
            data=data_payload,
            files=files_list,
            tool_name=tool_name,
            success=not result.isError,
            error="Tool reported an error" if result.isError else None
        )
            
        return cls(
            tool_name=tool_name,
            output=tool_output,
            is_error=result.isError
        )
