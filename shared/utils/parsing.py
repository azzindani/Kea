"""
Parsing utilities for handling LLM outputs.
"""

import json
import re
from typing import Any, Type, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


def clean_json_string(content: str) -> str:
    """
    Clean LLM response content to extract raw JSON.
    
    Handles:
    - Markdown code fences (```json ... ```)
    - Leading/trailing whitespace/prose
    - Nested structures and multiple objects (finds the first valid one)
    """
    if not content:
        return ""

    content = content.strip()

    # 1. Strip markdown code fences if present
    if "```" in content:
        # Match both ```json and just ```
        # We use a non-greedy match for the content to get the first block if multiple
        match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', content, re.IGNORECASE)
        if match:
            content = match.group(1).strip()

    # 2. Heuristic: Find first { or [ and last } or ]
    # We want to be careful not to include leading/trailing non-JSON text.
    start_obj = content.find("{")
    start_arr = content.find("[")
    
    # Determine the actual start (whichever comes first)
    if start_obj != -1 and (start_arr == -1 or start_obj < start_arr):
        start = start_obj
        end = content.rfind("}") + 1
    elif start_arr != -1:
        start = start_arr
        end = content.rfind("]") + 1
    else:
        # No braces or brackets found
        return content

    if start >= 0 and end > start:
        cleaned = content[start:end]
        # Quick validation: does it at least start and end correctly?
        if (cleaned.startswith("{") and cleaned.endswith("}")) or \
           (cleaned.startswith("[") and cleaned.endswith("]")):
            return cleaned

    return content


def parse_llm_json(content: str, schema: Type[T]) -> T:
    """
    Clean and parse LLM JSON response into a Pydantic model.
    """
    cleaned = clean_json_string(content)
    return schema.model_validate_json(cleaned)
