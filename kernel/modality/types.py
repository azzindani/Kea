"""
Tier 1 Modality — Types.

Pydantic models for omni-modal ingestion and demuxing.
Supports text, audio, image, video, and document inputs.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class ModalityType(StrEnum):
    """Input modality type."""

    TEXT = "TEXT"
    AUDIO = "AUDIO"
    IMAGE = "IMAGE"
    VIDEO = "VIDEO"
    DOCUMENT = "DOCUMENT"
    UNKNOWN = "UNKNOWN"


class RawInput(BaseModel):
    """Raw sensory input to the modality engine."""

    content: str | None = Field(default=None, description="Text content (for TEXT modality)")
    file_path: str | None = Field(default=None, description="Path to file on /tmp")
    mime_type: str | None = Field(default=None, description="MIME type if known")
    file_extension: str | None = Field(default=None, description="File extension (e.g., '.pdf')")


class FileHandle(BaseModel):
    """Lightweight pointer to a raw file for MCP tool consumption.

    Bypasses the cognitive engine for heavy media files. Tier 4 MCP
    tools grab this handle when they need the original file data.
    """

    file_path: str = Field(..., description="Path on /tmp")
    modality: ModalityType = Field(..., description="Detected modality type")
    size_bytes: int = Field(default=0, ge=0, description="File size in bytes")


class DocumentParts(BaseModel):
    """Extracted components from a complex document (PDF, XLSX, DOCX)."""

    text_blocks: list[str] = Field(default_factory=list, description="Extracted text sections")
    table_data: list[dict[str, str]] = Field(default_factory=list, description="Extracted table rows")
    embedded_image_paths: list[str] = Field(default_factory=list, description="Paths to extracted images")
    metadata: dict[str, str] = Field(default_factory=dict, description="Document metadata")


class VideoParts(BaseModel):
    """Extracted components from a video file."""

    keyframe_paths: list[str] = Field(default_factory=list, description="Paths to extracted keyframes")
    audio_path: str | None = Field(default=None, description="Path to extracted audio stream")
    duration_seconds: float = Field(default=0.0, ge=0.0)
    metadata: dict[str, str] = Field(default_factory=dict)


class ModalityOutput(BaseModel):
    """Combined output from modality ingestion.

    Up to three artifacts: semantic text, vector embedding, file handle.
    """

    cognitive_context: str | None = Field(
        default=None,
        description="Semantic text representation for LLM consumption",
    )
    associative_memory: list[float] | None = Field(
        default=None,
        description="Dense vector embedding for semantic recall",
    )
    file_handle: FileHandle | None = Field(
        default=None,
        description="Raw file pointer for MCP tools",
    )
    modality: ModalityType = Field(default=ModalityType.UNKNOWN)
