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


# Load core perception rules from knowledge/system
from shared.knowledge import load_system_knowledge

_ENTITY_RULES = load_system_knowledge("entity_rules.yaml")


# ============================================================================
# Syntactic Parsing (Tokenization)
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

    return tokens


def _guess_pos(word: str) -> str:
    """Lightweight POS heuristic using dynamic system knowledge."""
    anchors = _ENTITY_RULES.get("linguistic_anchors", {})
    clean = word.strip(".,;:!?\"'()[]{}").lower()

    if not clean:
        return "PUNCT"
    if clean in anchors.get("determiners", []):
        return "DET"
    if clean in anchors.get("prepositions", []):
        return "ADP"
    if clean in anchors.get("pronouns", []):
        return "PRON"
    if clean in anchors.get("conjunctions", []):
        return "CONJ"
    # Match against flat list or nested lists of common verbs
    common_verbs = anchors.get("common_verbs", [])
    if isinstance(common_verbs, list):
        # Handle potential nested list structure from YAML
        flat_verbs = []
        for v in common_verbs:
            if isinstance(v, list):
                flat_verbs.extend(v)
            else:
                flat_verbs.append(v)
        if clean in flat_verbs:
            return "VERB"

    if word[0].isupper() and not word.isupper():
        return "PROPN"  # Proper noun
    if re.match(r"^\d+", clean):
        return "NUM"
    return "NOUN"  # Default assumption


# ============================================================================
# Step 2: Candidate Span Generation
# ============================================================================


def generate_candidate_spans(tokens: list[Token]) -> list[EntitySpan]:
    """Generate candidate entity spans from token stream.

    Identifies:
    1. Structured format matches (extracted from Knowledge Rules)
    2. Proper noun sequences
    3. Noun phrase chunks (consecutive nouns/proper nouns)
    """
    full_text = " ".join(t.text for t in tokens)
    spans: list[EntitySpan] = []
    seen_ranges: set[tuple[int, int]] = set()

    # 1. Structured format detection (highest priority)
    # Pull dynamic regex patterns from knowledge file
    patterns = _ENTITY_RULES.get("structured_patterns", {})
    
    for entity_type, raw_pattern in patterns.items():
        pattern = re.compile(raw_pattern, re.IGNORECASE)
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

    Tiered Architecture:
    1. Primary: spaCy High-Accuracy extraction.
    2. Fallback: Knowledge-driven Regex heuristics.
    3. Final: Pydantic Schema Validation.
    """
    ref = _ref("extract_entities")
    start = time.perf_counter()

    try:
        # TIER 1 High Fidelity: spaCy Extraction (The Primary Engine)
        candidate_spans: list[EntitySpan] = []
        entity_settings = _ENTITY_RULES.get("settings", {})
        preferred_model = entity_settings.get("preferred_nlp_model", "en_core_web_sm")
        fallback_model = entity_settings.get("fallback_nlp_model", "en_core_web_sm")

        try:
            import warnings
            with warnings.catch_warnings():
                # Silence spaCy's environment/GPU warnings in the kernel
                warnings.filterwarnings("ignore", category=UserWarning, module="spacy")
                import spacy
                
                # Try preferred, then fallback
                try:
                    nlp = spacy.load(preferred_model)
                except (OSError, ImportError):
                    log.info(f"Preferred model '{preferred_model}' not found, trying fallback '{fallback_model}'")
                    nlp = spacy.load(fallback_model)

            doc = nlp(raw_text)
            for ent in doc.ents:
                candidate_spans.append(EntitySpan(
                    text=ent.text,
                    start=ent.start_char,
                    end=ent.end_char,
                    entity_type_hint=ent.label_,
                    confidence=0.85
                ))
        except (ImportError, OSError):
            log.warning("No compatible spaCy models found, falling back to Regex heuristics")
            pass

        # TIER 0 Fast Path: Knowledge-driven Heuristics
        tokens = tokenize_and_parse(raw_text)
        regex_spans = generate_candidate_spans(tokens)
        
        # Merge results: Add regex spans if not already covered by spaCy
        seen_ranges = {(s.start, s.end) for s in candidate_spans}
        for rs in regex_spans:
            if (rs.start, rs.end) not in seen_ranges:
                candidate_spans.append(rs)

        # Final Schema Validation
        validated = match_spans_to_schema(candidate_spans, expected_schema)

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
            span_count=len(candidate_spans),
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
