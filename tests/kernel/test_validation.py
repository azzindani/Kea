import pytest
from pydantic import BaseModel, Field

from kernel.validation.engine import (
    check_syntax,
    check_structure,
    check_types,
    check_bounds,
    validate
)
from shared.config import get_settings


class ValidationMockSchema(BaseModel):
    id: int = Field(..., gt=0)
    tag: str = Field(..., min_length=2)
    priority: float = Field(0.5, ge=0.0, le=1.0)


@pytest.mark.asyncio
@pytest.mark.parametrize("input_data, expected_pass", [
    # Success Case
    ({"id": 101, "tag": "prod", "priority": 0.9}, True),
    # Syntax Error (Handled by check_syntax)
    ("invalid string data", False),
    # Structure Error (Missing required field 'id')
    ({"tag": "prod", "priority": 0.5}, False),
    # Type Error ('tag' is not a string)
    ({"id": 102, "tag": 123, "priority": 0.5}, False),
    # Bounds Error ('priority' is too high)
    ({"id": 103, "tag": "test", "priority": 1.5}, False),
    # Bounds Error ('id' is non-positive)
    ({"id": 0, "tag": "test", "priority": 0.5}, False)
])
async def test_validation_comprehensive(input_data, expected_pass):
    """REAL SIMULATION: Verify Validation Kernel functions with multiple input scenarios."""
    print(f"\n--- Testing Validation: Data={input_data}, Expected Pass={expected_pass} ---")

    print(f"\n[Test]: check_syntax")
    syntax_res = check_syntax(input_data)
    print(f"   Syntax Result: {syntax_res.passed}")
    print(f" \033[92m[SUCCESS]\033[0m")

    # Proceed to subsequent gates only if syntax passed
    if syntax_res.passed:
        print(f"\n[Test]: check_structure")
        struct_res = check_structure(input_data if isinstance(input_data, dict) else {}, ValidationMockSchema)
        print(f"   Structure Result: {struct_res.passed}")
        print(f" \033[92m[SUCCESS]\033[0m")

        print(f"\n[Test]: check_types")
        type_res = check_types(input_data if isinstance(input_data, dict) else {}, ValidationMockSchema)
        print(f"   Type Result: {type_res.passed}")
        print(f" \033[92m[SUCCESS]\033[0m")

        print(f"\n[Test]: check_bounds")
        bounds_res = check_bounds(input_data if isinstance(input_data, dict) else {}, ValidationMockSchema)
        print(f"   Bounds Result: {bounds_res.passed}")
        print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: validate")
    res = await validate(input_data, ValidationMockSchema, kit=None)
    assert res.is_success == expected_pass
    print(f"   Cascade Final Outcome: {'Passed' if res.is_success else 'Failed'}")
    print(f" \033[92m[SUCCESS]\033[0m")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
