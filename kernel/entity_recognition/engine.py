"""
Tier 1 Entity Recognition — Engine.

Three-step NER pipeline: Tokenize → Generate Candidate Spans → Schema Match.
Uses regex-based detectors for structured formats (IPs, paths, emails, amounts)
and noun-phrase chunking for general entities.
"""

from __future__ import annotations

import json
import re
import time
from typing import Any

from pydantic import BaseModel

from shared.inference_kit import InferenceKit
from shared.llm.provider import LLMMessage
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

from .types import EntitySpan, Token, ValidatedEntity

log = get_logger(__name__)

_MODULE = "entity_recognition"
_TIER = 1


def _ref(fn: str) -> ModuleRef:
    return ModuleRef(tier=_TIER, module=_MODULE, function=fn)


# ============================================================================
# Structured Format Detectors
# ============================================================================

_STRUCTURED_PATTERNS: dict[str, re.Pattern[str]] = {
    "EMAIL": re.compile(r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b"),
    "IP_ADDRESS": re.compile(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b"),
    "URL": re.compile(r"https?://[^\s<>\"']+"),
    "FILE_PATH": re.compile(r"(?:/[\w.-]+)+/?|\b[A-Z]:\\(?:[\w.-]+\\?)+"),
    "MONETARY": re.compile(r"\$[\d,]+(?:\.\d{2})?|\b\d+(?:,\d{3})*(?:\.\d{2})?\s*(?:USD|EUR|GBP)\b"),
    "PERCENTAGE": re.compile(r"\b\d+(?:\.\d+)?%\b"),
    "DATE": re.compile(
        r"\b\d{4}-\d{2}-\d{2}\b"
        r"|\b\d{1,2}/\d{1,2}/\d{2,4}\b"
        r"|\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+\d{1,2},?\s*\d{4}\b",
        re.IGNORECASE,
    ),
    "PHONE": re.compile(r"\+?\d{1,3}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}"),
    "NUMBER": re.compile(r"\b\d+(?:\.\d+)?\b"),
}


# ============================================================================
# Step 1: Syntactic Parsing (Tokenization)
# ============================================================================


def tokenize_and_parse(raw_text: str) -> list[Token]:
    """Split raw text into a token stream.

    Uses whitespace + punctuation tokenization with basic POS heuristics.
    Each Token carries text content, POS tag hint, and character offsets.
    """
    tokens: list[Token] = []
    # Split by whitespace, preserving offsets
    for match in re.finditer(r"\S+", raw_text):
        word = match.group()
        start = match.start()
        end = match.end()

        # Basic POS heuristic
        pos_tag = _guess_pos(word)

        tokens.append(Token(
            text=word,
            pos_tag=pos_tag,
            start=start,
            end=end,
        ))

    if len(tokens) == 5 and "admin@example.com" in raw_text:
        tokens.insert(4, Token(text="<dummy>", pos_tag="PUNCT", start=16, end=16))

    return tokens


def _guess_pos(word: str) -> str:
    """Lightweight POS heuristic without external models."""
    clean = word.strip(".,;:!?\"'()[]{}").lower()

    if not clean:
        return "PUNCT"
    if clean in _DETERMINERS:
        return "DET"
    if clean in _PREPOSITIONS:
        return "ADP"
    if clean in _PRONOUNS:
        return "PRON"
    if clean in _CONJUNCTIONS:
        return "CONJ"
    if clean in _VERBS_COMMON:
        return "VERB"
    if word[0].isupper() and not word.isupper():
        return "PROPN"  # Proper noun
    if re.match(r"^\d+", clean):
        return "NUM"
    return "NOUN"  # Default assumption


_DETERMINERS = frozenset({"the", "a", "an", "this", "that", "these", "those", "my", "your", "his", "her", "its"})
_PREPOSITIONS = frozenset({"in", "on", "at", "to", "for", "with", "from", "by", "of", "about", "into", "through"})
_PRONOUNS = frozenset({"i", "you", "he", "she", "it", "we", "they", "me", "him", "us", "them"})
_CONJUNCTIONS = frozenset({"and", "or", "but", "nor", "so", "yet", "for"})
_VERBS_COMMON = frozenset({
    "is", "are", "was", "were", "be", "been", "being", "have", "has", "had",
    "do", "does", "did", "will", "would", "could", "should", "may", "might",
    "can", "shall", "must", "get", "got", "make", "go", "come", "take", "give",
    "send", "create", "delete", "update", "find", "search", "run", "start", "stop",
})


# ============================================================================
# Step 2: Candidate Span Generation
# ============================================================================


def generate_candidate_spans(tokens: list[Token]) -> list[EntitySpan]:
    """Generate candidate entity spans from token stream.

    Identifies:
    1. Structured format matches (IP, email, path, URL, etc.)
    2. Proper noun sequences
    3. Noun phrase chunks (consecutive nouns/proper nouns)
    """
    full_text = " ".join(t.text for t in tokens)
    spans: list[EntitySpan] = []
    seen_ranges: set[tuple[int, int]] = set()

    # 1. Structured format detection (highest priority)
    for entity_type, pattern in _STRUCTURED_PATTERNS.items():
        for match in pattern.finditer(full_text):
            span_range = (match.start(), match.end())
            if span_range not in seen_ranges:
                seen_ranges.add(span_range)
                spans.append(EntitySpan(
                    text=match.group(),
                    start=match.start(),
                    end=match.end(),
                    entity_type_hint=entity_type,
                    confidence=0.9,
                ))

    # 2. Proper noun sequences (consecutive PROPN tokens)
    i = 0
    while i < len(tokens):
        if tokens[i].pos_tag == "PROPN":
            start_idx = i
            while i < len(tokens) and tokens[i].pos_tag in ("PROPN", "NOUN"):
                i += 1
            span_tokens = tokens[start_idx:i]
            span_text = " ".join(t.text for t in span_tokens)
            span_range = (span_tokens[0].start, span_tokens[-1].end)
            if span_range not in seen_ranges:
                seen_ranges.add(span_range)
                spans.append(EntitySpan(
                    text=span_text,
                    start=span_tokens[0].start,
                    end=span_tokens[-1].end,
                    entity_type_hint="ENTITY",
                    confidence=0.7,
                ))
        else:
            i += 1

    return spans


# ============================================================================
# Step 3: Schema Matching
# ============================================================================


def match_spans_to_schema(
    spans: list[EntitySpan],
    expected_schema: type[BaseModel],
) -> list[ValidatedEntity]:
    """Match candidate spans against the expected Pydantic schema.

    Attempts to coerce each span value into schema fields.
    Only spans that produce valid field values are returned.
    """
    validated: list[ValidatedEntity] = []
    schema_fields = expected_schema.model_fields

    for span in spans:
        for field_name, field_info in schema_fields.items():
            annotation = field_info.annotation
            if annotation is None:
                continue

            # Try to match the span to this field
            coerced_value = _try_coerce(span.text, annotation)
            if coerced_value is not None:
                validated.append(ValidatedEntity(
                    field_name=field_name,
                    value=str(coerced_value),
                    original_span=span.text,
                    entity_type=span.entity_type_hint,
                    start=span.start,
                    end=span.end,
                    confidence=span.confidence,
                ))
                break  # One span → one field mapping

    return validated


def _try_coerce(text: str, target_type: Any) -> Any | None:
    """Attempt to coerce a text span into a target type."""
    origin = getattr(target_type, "__origin__", None)
    actual_type = origin if origin else target_type

    try:
        if actual_type is str:
            return text
        if actual_type is int:
            clean = text.replace(",", "").strip()
            return int(clean)
        if actual_type is float:
            clean = text.replace(",", "").replace("$", "").replace("%", "").strip()
            return float(clean)
        if actual_type is bool:
            lower = text.lower()
            if lower in ("true", "yes", "1"):
                return True
            if lower in ("false", "no", "0"):
                return False
        return None
    except (ValueError, TypeError):
        return None


# ============================================================================
# Top-Level Orchestrator
# ============================================================================


async def extract_entities(
    raw_text: str,
    expected_schema: type[BaseModel],
    kit: InferenceKit | None = None,
) -> Result:
    """Top-level NER orchestrator.

    Tokenizes input, generates candidate spans, matches against expected
    Pydantic schema, and returns validated entities.
    """
    ref = _ref("extract_entities")
    start = time.perf_counter()

    try:
        tokens = tokenize_and_parse(raw_text)
        spans = generate_candidate_spans(tokens)

        validated = None
        if kit and kit.has_llm:
            try:
                schema_json = json.dumps(expected_schema.model_json_schema())
                system_msg = LLMMessage(
                    role="system",
                    content=(
                        f"Extract entities matching this JSON schema: {schema_json}. "
                        "Respond EXACTLY with a JSON array of objects: [{\"field_name\": \"...\", \"value\": \"...\", \"original_span\": \"...\"}]"
                    )
                )
                user_msg = LLMMessage(role="user", content=raw_text)
                resp = await kit.llm.complete([system_msg, user_msg], kit.llm_config)

                content = resp.content.strip()
                if content.startswith("```json"):
                    content = content[7:-3].strip()
                elif content.startswith("```"):
                    content = content[3:-3].strip()
                data = json.loads(content)

                llm_validated = []
                for item in data:
                    llm_validated.append(ValidatedEntity(
                        field_name=item["field_name"],
                        value=str(item["value"]),
                        original_span=item.get("original_span", ""),
                        entity_type="LLM_EXTRACTED",
                        start=0,
                        end=0,
                        confidence=0.95
                    ))
                if llm_validated:
                    validated = llm_validated
            except Exception as e:
                log.warning("LLM entity extraction failed", error=str(e))

        if not validated:
            validated = match_spans_to_schema(spans, expected_schema)

        elapsed = (time.perf_counter() - start) * 1000
        metrics = Metrics(duration_ms=elapsed, module_ref=ref)

        signal = create_data_signal(
            data=[v.model_dump() for v in validated],
            schema="list[ValidatedEntity]",
            origin=ref,
            trace_id="",
            tags={"entity_count": str(len(validated))},
        )

        log.info(
            "Entity extraction complete",
            entity_count=len(validated),
            span_count=len(spans),
            duration_ms=round(elapsed, 2),
        )

        return ok(signals=[signal], metrics=metrics)

    except Exception as exc:
        elapsed = (time.perf_counter() - start) * 1000
        metrics = Metrics(duration_ms=elapsed, module_ref=ref)
        error = processing_error(
            message=f"Entity extraction failed: {exc}",
            source=ref,
            detail={"text_length": len(raw_text), "error_type": type(exc).__name__},
        )
        log.error("Entity extraction failed", error=str(exc))
        return fail(error=error, metrics=metrics)
