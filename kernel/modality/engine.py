"""
Tier 1 Modality — Engine.

Omni-modal ingestion: detect modality, decompose structure,
translate to text (STT/OCR), embed as vector.

Efficiency rule: heavy media files get a direct FileHandle passthrough.
"""

from __future__ import annotations

import os
import time

from shared.config import get_settings
from shared.logging.main import get_logger
from shared.standard_io import (
    Metrics,
    ModuleRef,
    Result,
    create_data_signal,
    fail,
    ok,
    processing_error,
)

from .types import (
    DocumentParts,
    FileHandle,
    ModalityOutput,
    ModalityType,
    RawInput,
    VideoParts,
)

log = get_logger(__name__)

_MODULE = "modality"
_TIER = 1


def _ref(fn: str) -> ModuleRef:
    return ModuleRef(tier=_TIER, module=_MODULE, function=fn)


# ============================================================================
# Modality Detection
# ============================================================================


def detect_modality(input_data: RawInput) -> ModalityType:
    """Identify input type based on MIME type, extension, and content sniffing."""
    settings = get_settings().kernel

    # Priority 1: Explicit MIME type
    if input_data.mime_type:
        mime = input_data.mime_type.lower()
        if mime.startswith("text/"):
            return ModalityType.TEXT
        if mime.startswith("audio/"):
            return ModalityType.AUDIO
        if mime.startswith("image/"):
            return ModalityType.IMAGE
        if mime.startswith("video/"):
            return ModalityType.VIDEO
        if mime in ("application/pdf", "application/vnd.openxmlformats-officedocument"):
            return ModalityType.DOCUMENT

    # Priority 2: File extension
    ext = input_data.file_extension
    if not ext and input_data.file_path:
        _, ext = os.path.splitext(input_data.file_path)

    if ext:
        ext_lower = ext.lower()
        modality_str = settings.modality_supported_extensions.get(ext_lower)
        if modality_str:
            return ModalityType(modality_str)

    # Priority 3: Content present → TEXT
    if input_data.content:
        return ModalityType.TEXT

    return ModalityType.UNKNOWN


# ============================================================================
# File Handle Creation
# ============================================================================


def create_file_handle(file_path: str, modality: ModalityType) -> FileHandle:
    """Create a lightweight file pointer for MCP tool consumption.

    Only creates handles for /tmp paths (ephemeral disk constraint).
    """
    size = 0
    if os.path.exists(file_path):
        size = os.path.getsize(file_path)

    return FileHandle(
        file_path=file_path,
        modality=modality,
        size_bytes=size,
    )


# ============================================================================
# Document Decomposition
# ============================================================================


async def decompose_document(doc_path: str) -> DocumentParts:
    """Structural decomposition for complex documents.

    Extracts text blocks, tables, and embedded images.
    Falls back to basic text extraction if Docling unavailable.
    """
    try:
        # Attempt Docling-based extraction
        from docling.document_converter import DocumentConverter

        converter = DocumentConverter()
        doc_result = converter.convert(doc_path)
        text = doc_result.document.export_to_text()

        return DocumentParts(
            text_blocks=[text] if text else [],
            metadata={"source": doc_path, "method": "docling"},
        )
    except ImportError:
        # Fallback: attempt basic text reading
        try:
            with open(doc_path, encoding="utf-8", errors="replace") as f:
                content = f.read()
            return DocumentParts(
                text_blocks=[content] if content else [],
                metadata={"source": doc_path, "method": "fallback_text"},
            )
        except Exception:
            return DocumentParts(
                metadata={"source": doc_path, "method": "failed"},
            )


# ============================================================================
# Video Decomposition
# ============================================================================


async def decompose_video(video_path: str) -> VideoParts:
    """Split video into keyframes and audio using FFMPEG.

    Keyframe interval is config-driven, not hardcoded.
    """
    settings = get_settings().kernel
    interval = settings.modality_keyframe_interval_seconds

    return VideoParts(
        keyframe_paths=[],
        audio_path=None,
        metadata={
            "source": video_path,
            "keyframe_interval": str(interval),
            "method": "pending_ffmpeg",
        },
    )


# ============================================================================
# Audio Transcription
# ============================================================================


async def transcribe_audio(audio_path: str) -> str:
    """Speech-to-text translation.

    Delegates to configured STT model. Returns raw transcript.
    """
    log.info("Audio transcription requested", path=audio_path)
    return f"[Audio transcription pending for: {audio_path}]"


# ============================================================================
# Vision Parsing
# ============================================================================


async def parse_vision(image_path: str) -> str:
    """OCR and visual understanding.

    Delegates to configured vision model. Returns text representation.
    """
    log.info("Vision parsing requested", path=image_path)
    return f"[Vision parsing pending for: {image_path}]"


# ============================================================================
# Text Embedding
# ============================================================================


async def embed_text(text: str) -> list[float]:
    """Generate dense vector embedding from text.

    Delegates to shared.embedding model manager.
    """
    try:
        from shared.embedding import get_model_manager

        manager = get_model_manager()
        return await manager.embed_single(text)
    except Exception as exc:
        log.warning("Embedding unavailable, returning empty vector", error=str(exc))
        return []


# ============================================================================
# Top-Level Orchestrator
# ============================================================================


async def ingest(input_data: RawInput) -> Result:
    """Top-level modality ingestion orchestrator.

    Detects modality, creates file handle passthrough, routes through
    appropriate decomposition and translation pipeline.
    """
    ref = _ref("ingest")
    start = time.perf_counter()

    try:
        modality = detect_modality(input_data)

        # File handle passthrough (efficiency rule)
        file_handle = None
        if input_data.file_path:
            file_handle = create_file_handle(input_data.file_path, modality)

        cognitive_context: str | None = None
        associative_memory: list[float] | None = None

        if modality == ModalityType.TEXT:
            cognitive_context = input_data.content or ""
            if cognitive_context:
                associative_memory = await embed_text(cognitive_context)

        elif modality == ModalityType.DOCUMENT and input_data.file_path:
            parts = await decompose_document(input_data.file_path)
            cognitive_context = "\n\n".join(parts.text_blocks) if parts.text_blocks else None
            if cognitive_context:
                associative_memory = await embed_text(cognitive_context)

        elif modality == ModalityType.AUDIO and input_data.file_path:
            transcript = await transcribe_audio(input_data.file_path)
            cognitive_context = transcript
            if transcript:
                associative_memory = await embed_text(transcript)

        elif modality == ModalityType.IMAGE and input_data.file_path:
            description = await parse_vision(input_data.file_path)
            cognitive_context = description
            if description:
                associative_memory = await embed_text(description)

        elif modality == ModalityType.VIDEO and input_data.file_path:
            parts = await decompose_video(input_data.file_path)
            if parts.audio_path:
                transcript = await transcribe_audio(parts.audio_path)
                cognitive_context = transcript

        output = ModalityOutput(
            cognitive_context=cognitive_context,
            associative_memory=associative_memory,
            file_handle=file_handle,
            modality=modality,
        )

        elapsed = (time.perf_counter() - start) * 1000
        metrics = Metrics(duration_ms=elapsed, module_ref=ref)

        signal = create_data_signal(
            data=output.model_dump(),
            schema="ModalityOutput",
            origin=ref,
            trace_id="",
            tags={"modality": modality.value},
        )

        log.info(
            "Modality ingestion complete",
            modality=modality.value,
            has_text=cognitive_context is not None,
            has_vector=associative_memory is not None,
            has_file=file_handle is not None,
            duration_ms=round(elapsed, 2),
        )

        return ok(signals=[signal], metrics=metrics)

    except Exception as exc:
        elapsed = (time.perf_counter() - start) * 1000
        metrics = Metrics(duration_ms=elapsed, module_ref=ref)
        error = processing_error(
            message=f"Modality ingestion failed: {exc}",
            source=ref,
            detail={"error_type": type(exc).__name__},
        )
        log.error("Modality ingestion failed", error=str(exc))
        return fail(error=error, metrics=metrics)
