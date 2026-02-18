"""
Tool Registry Loader.

Loads tool capabilities from YAML configuration, removing hardcoded logic from code.
"""
from __future__ import annotations

import yaml
from pathlib import Path
from functools import lru_cache
from typing import Any, Dict

from shared.logging import get_logger

logger = get_logger(__name__)


@lru_cache()
def load_tool_registry() -> Dict[str, Any]:
    """
    Load the tool registry from configs/tool_registry.yaml.
    """
    try:
        # Determine path relative to project root
        root_path = Path(__file__).resolve().parents[3]
        config_path = root_path / "configs" / "tool_registry.yaml"
        
        if not config_path.exists():
            logger.warning(f"Tool registry not found at {config_path}, returning empty.")
            return {}
            
        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            
        return data.get("items", {})
        
    except Exception as e:
        logger.error(f"Failed to load tool registry: {e}")
        return {}


def get_tool_capabilities() -> Dict[str, Any]:
    """
    Get the dictionary of tool capabilities for the Planner.
    Wrapper around the cached loader.
    """
    return load_tool_registry()


def route_to_tool_dynamic(task_description: str) -> tuple[str, list[str]]:
    """
    Route a micro-task to the appropriate tool based on keywords defined in YAML.
    
    Returns:
        (primary_tool, fallback_tools)
    """
    task_lower = task_description.lower()
    registry = load_tool_registry()
    
    # 1. INTELLIGENCE: Check for direct tool reference (registry scan)
    # Similar to original logic but using the loaded registry keys
    known_tools = sorted(list(registry.keys()), key=len, reverse=True)
    
    for tool_name in known_tools:
        if tool_name in task_lower or tool_name.replace("_", " ") in task_lower:
             return tool_name, [] # Found exact match
    
    # 2. KEYWORDS: Score based on YAML keywords
    scores = {}
    for tool, config in registry.items():
        keywords = config.get("keywords", [])
        score = sum(1 for kw in keywords if kw in task_lower)
        if score > 0:
            scores[tool] = score
    
    if not scores:
        return "web_search", ["news_search"]
        
    # Get highest scoring tool
    best_tool = max(scores, key=scores.get)
    fallbacks = registry[best_tool].get("fallbacks", [])
    
    return best_tool, fallbacks
