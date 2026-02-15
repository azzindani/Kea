"""
StdioEnvelope to HTTP Response Transformer.

Transforms the kernel's universal StdioEnvelope output into HTTP-friendly
responses for the API Gateway. Serves as the single boundary between the
kernel's internal I/O contract and the external HTTP interface.

Supported transformations:
- StdioEnvelope   ResearchResponse dict (for /research)
- StdioEnvelope   ChatResponse dict (for /chat/message)
- StdioEnvelope   SSE event stream (for /research/stream)
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from kernel.io.stdio_envelope import StdioEnvelope
from shared.logging import get_logger

logger = get_logger(__name__)


def envelope_to_research_response(envelope: StdioEnvelope) -> dict[str, Any]:
    """
    Transform a StdioEnvelope into a dict matching ResearchResponse.

    Extracts:
    - report: Main content + work package artifacts
    - confidence: From metadata
    - sources: From work package artifacts metadata
    - facts: From work package key findings
    - errors: From stderr failures
    """
    stdout = envelope.stdout
    stderr = envelope.stderr
    meta = envelope.metadata

    # Build report content from stdout
    report_parts: list[str] = []

    # Primary content
    if stdout.content:
        report_parts.append(stdout.content)

    # Work package sections
    wp = stdout.work_package
    if wp and wp.artifacts:
        for artifact in wp.artifacts:
            report_parts.append(f"\n## {artifact.title}\n\n{artifact.content}")

    report = "\n\n".join(report_parts) if report_parts else ""

    # Extract sources from artifacts and content
    sources: list[dict] = []
    if wp and wp.artifacts:
        for artifact in wp.artifacts:
            art_meta = artifact.metadata
            if art_meta and hasattr(art_meta, "sources") and art_meta.sources:
                for src in art_meta.sources:
                    if isinstance(src, str):
                        sources.append({"url": src, "title": artifact.title})
                    elif isinstance(src, dict):
                        sources.append(src)

    # Extract facts from work package key findings
    facts: list[dict] = []
    if wp and wp.key_findings:
        for finding in wp.key_findings:
            facts.append({"text": finding, "source": "kernel", "persist": True})

    # Also include key findings from stdout
    for kf in stdout.key_findings:
        facts.append(
            {
                "text": kf.finding,
                "confidence": kf.confidence,
                "evidence_strength": kf.evidence_strength,
                "source": "kernel",
            }
        )

    # Collect errors for cross-attempt sharing
    errors: list[dict] = []
    for failure in stderr.failures:
        errors.append(
            {
                "task_id": failure.task_id,
                "error": failure.error,
                "recovery_action": failure.recovery_action,
            }
        )

    # Collect warnings
    warnings: list[dict] = []
    for warning in stderr.warnings:
        warnings.append(
            {
                "type": warning.type,
                "message": warning.message,
                "severity": warning.severity.value,
            }
        )

    return {
        "report": report,
        "confidence": meta.confidence,
        "sources_count": len(sources),
        "facts_count": len(facts),
        "facts": facts,
        "errors": errors,
        "warnings": warnings,
        "metadata": {
            "cell_id": meta.cell_id,
            "level": meta.level,
            "role": meta.role,
            "domain": meta.domain,
            "duration_ms": meta.duration_ms,
            "tokens_used": meta.tokens_used,
            "children_count": meta.children_count,
            "messages_sent": meta.messages_sent,
            "messages_received": meta.messages_received,
        },
    }


def envelope_to_chat_response(envelope: StdioEnvelope) -> dict[str, Any]:
    """
    Transform a StdioEnvelope into a chat-friendly response dict.

    Focuses on content and sources for the chat interface.
    """
    stdout = envelope.stdout
    meta = envelope.metadata

    # For chat, content is the primary deliverable
    content = stdout.content or ""

    # Attach work package summary if available
    wp = stdout.work_package
    if wp and wp.summary and not content:
        content = wp.summary

    # Extract sources
    sources: list[dict] = []
    if wp and wp.artifacts:
        for artifact in wp.artifacts:
            art_meta = artifact.metadata
            if art_meta and hasattr(art_meta, "sources") and art_meta.sources:
                for src in art_meta.sources:
                    if isinstance(src, str):
                        sources.append({"url": src})
                    elif isinstance(src, dict):
                        sources.append(src)

    # Facts from key findings
    facts: list[dict] = []
    for kf in stdout.key_findings:
        facts.append({"text": kf.finding, "confidence": kf.confidence})
    if wp and wp.key_findings:
        for finding in wp.key_findings:
            facts.append({"text": finding, "source": "kernel"})

    return {
        "content": content,
        "confidence": meta.confidence,
        "sources": sources,
        "tool_calls": [],
        "facts": facts,
        "duration_ms": int(meta.duration_ms),
        "query_type": "kernel",
        "was_cached": False,
    }


async def envelope_to_sse_events(
    envelope: StdioEnvelope,
    job_id: str = "",
) -> AsyncIterator[dict[str, Any]]:
    """
    Transform a StdioEnvelope into a stream of SSE-compatible events.

    Events:
    - {"event": "start", "job_id": ..., "level": ...}
    - {"event": "phase", "phase": "kernel_processing"}
    - {"event": "chunk", "content": "..."}  (content streamed in parts)
    - {"event": "artifact", "artifact": {...}}
    - {"event": "warning", "warning": {...}}
    - {"event": "complete", "confidence": ..., ...}
    """
    meta = envelope.metadata
    stdout = envelope.stdout
    stderr = envelope.stderr

    yield {
        "event": "start",
        "job_id": job_id,
        "level": meta.level,
        "role": meta.role,
    }

    yield {"event": "phase", "phase": "kernel_processing"}

    # Stream content in chunks
    content = stdout.content or ""
    chunk_size = 100
    for i in range(0, len(content), chunk_size):
        yield {"event": "chunk", "phase": "synthesis", "content": content[i : i + chunk_size]}

    # Stream artifacts
    wp = stdout.work_package
    if wp and wp.artifacts:
        for artifact in wp.artifacts:
            yield {
                "event": "artifact",
                "artifact": {
                    "id": artifact.id,
                    "type": artifact.type,
                    "title": artifact.title,
                    "confidence": artifact.confidence,
                    "summary": artifact.summary or artifact.content[:200],
                },
            }

    # Stream warnings
    for warning in stderr.warnings:
        yield {
            "event": "warning",
            "warning": {
                "type": warning.type,
                "message": warning.message,
                "severity": warning.severity.value,
            },
        }

    # Completion event
    yield {
        "event": "complete",
        "job_id": job_id,
        "report": content,
        "confidence": meta.confidence,
        "facts_count": len(stdout.key_findings),
        "sources_count": 0,
        "duration_ms": meta.duration_ms,
    }
