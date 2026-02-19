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
    - Leading/trailing whitespace
    - Extraction of the first JSON object {} or array [] found
    """
    content = content.strip()

    # 1. Strip markdown code fences
    if "```" in content:
        # Match both ```json and just ```
        match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', content)
        if match:
            content = match.group(1).strip()

    # 2. Find JSON boundaries (greedy search for {})
    start = content.find("{")
    end = content.rfind("}") + 1
    
    # Check for array if no object found
    if start == -1:
        start = content.find("[")
        end = content.rfind("]") + 1
        
    if start >= 0 and end > start:
        content = content[start:end]

    return content


def parse_llm_json(content: str, schema: Type[T]) -> T:
    """
    Clean and parse LLM JSON response into a Pydantic model.
    """
    cleaned = clean_json_string(content)
    return schema.model_validate_json(cleaned)
