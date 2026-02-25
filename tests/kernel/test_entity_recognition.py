import pytest
from pydantic import BaseModel, Field

from kernel.entity_recognition.engine import (
    tokenize_and_parse,
    generate_candidate_spans,
    match_spans_to_schema,
    extract_entities
)
from shared.config import get_settings


class TestSchema(BaseModel):
    user_email: str = Field(..., description="The email address to extract")
    amount: float = Field(0.0, description="The monetary amount")
    resource_path: str = Field("", description="File system path")


@pytest.mark.asyncio
@pytest.mark.parametrize("text", [
    "Send an email to support@kea.ai regarding the $1500 license fee.",
    "Verify the files located at /etc/kea/config.yaml and /var/log/kea.log",
    "Notify user admin@company.com about the 50% discount on order #1234",
    "The IP address is 192.168.1.1 and the URL is https://kea.ai/docs",
    ""
])
async def test_entity_recognition_comprehensive(text):
    """REAL SIMULATION: Verify Entity Recognition Kernel functions with multiple inputs."""
    print(f"\n--- Testing Entity Recognition with Text: '{text}' ---")

    print(f"\n[Test]: tokenize_and_parse")
    tokens = tokenize_and_parse(text)
    assert isinstance(tokens, list)
    print(f"   Tokens extracted: {len(tokens)}")
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: generate_candidate_spans")
    spans = generate_candidate_spans(tokens)
    assert isinstance(spans, list)
    print(f"   Candidate Spans generated: {len(spans)}")
    for s in spans:
        print(f"     - {s.text} (Hint: {s.entity_type_hint})")
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: match_spans_to_schema")
    validated_entities = match_spans_to_schema(spans, TestSchema)
    assert isinstance(validated_entities, list)
    print(f"   Validated Entities matched to schema: {len(validated_entities)}")
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: extract_entities")
    res = await extract_entities(text, TestSchema, kit=None)
    assert res.is_success
    print(f" \033[92m[SUCCESS]\033[0m")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
