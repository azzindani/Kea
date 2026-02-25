from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic import BaseModel, Field

from kernel.validation.engine import (
    check_bounds,
    check_structure,
    check_syntax,
    check_types,
    validate,
)
from shared.inference_kit import InferenceKit


class SampleSchema(BaseModel):
    name: str = Field(..., max_length=10)
    age: int = Field(..., gt=0)


def test_check_syntax():
    # Valid JSON string
    res = check_syntax('{"name": "Alice"}')
    assert res.passed
    assert isinstance(res.parsed_data, dict)

    # Invalid JSON string
    res = check_syntax('{"name": "Alice"')
    assert not res.passed

    # Dict
    res = check_syntax({"name": "Alice"})
    assert res.passed


def test_check_structure(monkeypatch):
    class MockSettings:
        validation_strict_mode: bool = True

    class MockKernelSettings:
        kernel = MockSettings()

    monkeypatch.setattr("kernel.validation.engine.get_settings", lambda: MockKernelSettings())

    # Missing age
    res = check_structure({"name": "Alice"}, SampleSchema)
    assert not res.passed
    assert "age" in res.missing_keys

    # Extra keys
    res = check_structure({"name": "Alice", "age": 20, "extra": True}, SampleSchema)
    assert not res.passed
    assert "extra" in res.extra_keys


def test_check_types():
    # Wrong type format
    res = check_types({"name": "Alice", "age": "twenty"}, SampleSchema)
    assert not res.passed
    assert len(res.mismatches) > 0
    assert res.mismatches[0].field == "age"


def test_check_bounds():
    # Age < 0
    res = check_bounds({"name": "Alice", "age": -5}, SampleSchema)
    assert not res.passed
    assert res.violations[0].field == "age"

    # Name > max_length
    res = check_bounds({"name": "Alice Wonderland", "age": 20}, SampleSchema)
    assert not res.passed
    assert res.violations[0].field == "name"

@pytest.mark.asyncio
async def test_llm_fallback_validate(monkeypatch):
    class MockSettings:
        validation_strict_mode: bool = False
    class MockKernelSettings:
        kernel = MockSettings()
    monkeypatch.setattr("kernel.validation.engine.get_settings", lambda: MockKernelSettings())

    kit = MagicMock(spec=InferenceKit)
    kit.has_llm = True

    mock_resp = MagicMock()
    # Assume the LLM semantic validation passed
    mock_resp.content = '```json\n{"passed": true, "reason": "Makes sense"}\n```'

    kit.llm = AsyncMock()
    kit.llm.complete.return_value = mock_resp
    kit.llm_config = MagicMock()

    # Pass syntactically and structurally perfect data
    res = await validate({"name": "Alice", "age": 25}, SampleSchema, kit)

    assert res.is_success
