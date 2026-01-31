"""
Template Loader for Kea Pipeline Builder.

Loads and expands Golden Path templates - pre-defined workflows
that reduce LLM hallucination and improve reliability.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from shared.logging import get_logger


logger = get_logger(__name__)

# Template directory (same folder as this file)
TEMPLATES_DIR = Path(__file__).parent


class TemplateLoader:
    """
    Load and expand workflow templates.
    
    Templates are JSON files in the templates/ directory with structure:
    {
        "name": "template_name",
        "description": "What this template does",
        "variables": ["var1", "var2"],
        "blueprint": [...]
    }
    
    Example:
        loader = TemplateLoader()
        template = loader.load("financial_deep_dive")
        tasks = loader.expand(template, {"ticker": "BBCA.JK"})
    """
    
    def __init__(self, templates_dir: Path | None = None):
        self._dir = templates_dir or TEMPLATES_DIR
        self._cache: dict[str, dict] = {}
        self._discover_templates()
        
    def _discover_templates(self) -> None:
        """Discover all template JSON files in the templates directory."""
        for path in self._dir.glob("*.json"):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    template = json.load(f)
                name = template.get("name", path.stem)
                self._cache[name] = template
                logger.debug(f"Discovered template: {name}")
            except Exception as e:
                logger.warning(f"Failed to load template {path}: {e}")
                
    def list_templates(self) -> list[str]:
        """List all available template names."""
        return list(self._cache.keys())
        
    def load(self, name: str) -> dict | None:
        """
        Load a template by name.
        
        Args:
            name: Template name (without .json extension)
            
        Returns:
            Template dict or None if not found
        """
        if name in self._cache:
            return self._cache[name]
            
        # Try loading from file
        path = self._dir / f"{name}.json"
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    template = json.load(f)
                self._cache[name] = template
                return template
            except Exception as e:
                logger.error(f"Failed to load template {name}: {e}")
                
        return None
        
    def match(self, query: str) -> str | None:
        """
        Find a template that matches the query.
        
        Uses keyword matching to find the best template.
        
        Args:
            query: User's research query
            
        Returns:
            Template name or None if no match
        """
        query_lower = query.lower()
        
        # Keyword -> template mapping
        mappings = {
            "financial_deep_dive": ["financial", "stock", "ticker", "quarterly", "annual", "income", "balance sheet", "earnings", "dividend"],
            "legal_audit": ["legal", "court", "case", "contract", "lawsuit", "regulation", "compliance"],
            "data_pipeline": ["data", "csv", "download", "process", "analyze", "pipeline"],
        }
        
        best_match = None
        best_score = 0
        
        for template_name, keywords in mappings.items():
            score = sum(1 for kw in keywords if kw in query_lower)
            if score > best_score:
                best_score = score
                best_match = template_name
                
        # Only return if we have a reasonable match
        if best_score >= 2:
            logger.info(f"🎯 Matched template: {best_match} (score: {best_score})")
            return best_match
            
        return None
        
    def expand(self, template: dict, variables: dict[str, str]) -> list[dict]:
        """
        Expand a template with variables to produce MicroTask dicts.
        
        Args:
            template: Template dict from load()
            variables: Dict of variable values, e.g. {"ticker": "BBCA.JK"}
            
        Returns:
            List of task dicts ready for execution
        """
        blueprint = template.get("blueprint", [])
        expanded = []
        
        for step in blueprint:
            # Deep copy to avoid modifying template
            task = json.loads(json.dumps(step))
            
            # Replace {{variable}} placeholders in all string values
            task = self._replace_variables(task, variables)
            expanded.append(task)
            
        logger.info(f"📋 Expanded template '{template.get('name')}' with {len(expanded)} tasks")
        return expanded
        
    def _replace_variables(self, obj: Any, variables: dict[str, str]) -> Any:
        """Recursively replace {{var}} placeholders in an object."""
        if isinstance(obj, str):
            for var_name, var_value in variables.items():
                obj = obj.replace(f"{{{{{var_name}}}}}", str(var_value))
            return obj
        elif isinstance(obj, dict):
            return {k: self._replace_variables(v, variables) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._replace_variables(item, variables) for item in obj]
        else:
            return obj


# ============================================================================
# Singleton Access
# ============================================================================

_loader: TemplateLoader | None = None


def get_template_loader() -> TemplateLoader:
    """Get the global template loader instance."""
    global _loader
    if _loader is None:
        _loader = TemplateLoader()
    return _loader
