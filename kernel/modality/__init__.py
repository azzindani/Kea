"""
Tier 1: Modality Module.

Omni-modal ingestion and demuxing — text, audio, image, video, documents.

Usage::

    from kernel.modality import ingest, RawInput

    result = await ingest(RawInput(content="Hello world"))
    result = await ingest(RawInput(file_path="/tmp/doc.pdf"))
"""

from .engine import (
    create_file_handle,
    decompose_document,
    decompose_video,
    detect_modality,
    embed_text,
    ingest,
    parse_vision,
    transcribe_audio,
)
from .types import (
    DocumentParts,
    FileHandle,
    ModalityOutput,
    ModalityType,
    RawInput,
    VideoParts,
)

__all__ = [
    "ingest",
    "detect_modality",
    "create_file_handle",
    "decompose_document",
    "decompose_video",
    "transcribe_audio",
    "parse_vision",
    "embed_text",
    "ModalityType",
    "RawInput",
    "FileHandle",
    "DocumentParts",
    "VideoParts",
    "ModalityOutput",
]
