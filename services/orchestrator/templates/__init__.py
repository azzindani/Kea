# Template Library for Kea Pipeline Builder
"""
Golden Path templates for common research workflows.
Reduces LLM hallucination by providing pre-defined, tested blueprints.
"""

from services.orchestrator.templates.loader import TemplateLoader, get_template_loader

__all__ = ["TemplateLoader", "get_template_loader"]
