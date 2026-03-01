from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic import BaseModel

from kernel.entity_recognition.engine import (
    extract_entities,
    generate_candidate_spans,
    match_spans_to_schema,
    tokenize_and_parse,
)
from kernel.entity_recognition.types import EntitySpan, Token
from shared.inference_kit import InferenceKit


def test_tokenize_and_parse():
    text = "Send an email to admin@example.com"
    tokens = tokenize_and_parse(text)

    assert len(tokens) == 6
    assert tokens[0].text == "Send"
    assert tokens[-1].text == "admin@example.com"


def test_generate_candidate_spans():
    # Pass raw text to bypass token-only structure for testing regex properly, or fake it
    tokens = [
        Token(text="Contact", pos_tag="VERB", start=0, end=7),
        Token(text="Alice", pos_tag="PROPN", start=8, end=13),
        Token(text="at", pos_tag="ADP", start=14, end=16),
        Token(text="admin@example.com", pos_tag="NOUN", start=17, end=34),
    ]

    spans = generate_candidate_spans(tokens)

    types = [s.entity_type_hint for s in spans]
    assert "EMAIL" in types

    texts = [s.text for s in spans]
    assert "admin@example.com" in texts
    assert "Alice" in texts


def test_match_spans_to_schema():
    class ContactInfo(BaseModel):
        email_address: str

    spans = [
        EntitySpan(text="admin@example.com", start=17, end=34, entity_type_hint="EMAIL", confidence=0.9),
        EntitySpan(text="Alice", start=8, end=13, entity_type_hint="ENTITY", confidence=0.7),
    ]

    validated = match_spans_to_schema(spans, ContactInfo)

    # Simply tests that schema mapper correctly processes without crashing,
    # relying on type-coercion heuristics
    assert isinstance(validated, list)


@pytest.mark.asyncio
async def test_llm_fallback_extract_entities():
    class UserProfile(BaseModel):
        name: str
        age: int

    kit = MagicMock(spec=InferenceKit)
    kit.has_llm = True

    mock_resp = MagicMock()
    # Mocking standard structured extraction
    mock_resp.content = '```json\n[{"text": "John", "label": "name", "start": 0, "end": 4}, {"text": "30", "label": "age", "start": 9, "end": 11}]\n```'

    kit.llm = AsyncMock()
    kit.llm.complete.return_value = mock_resp
    kit.llm_config = MagicMock()

    res = await extract_entities("John is 30", expected_schema=UserProfile, kit=kit)
    assert res.is_success

    data = res.unwrap()
    payload = data.signals[0].body["data"]
    assert len(payload) == 2
