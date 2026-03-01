"""
System Knowledge Loader.

Provides direct access to core kernel knowledge files stored in knowledge/system/
that are required for bootstrap and high-speed perception (T1/T6).
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any
import yaml

from shared.config import get_settings
from shared.logging.main import get_logger

log = get_logger(__name__)

def load_system_knowledge(filename: str) -> dict[str, Any]:
    """
    Load a YAML file from the knowledge/system/ directory.
    
    This is used as a bootstrap mechanism for Tier 1 and Tier 6 logic
    that requires predefined anchors for embedding-based classification.
    
    Args:
        filename: Name of the file (e.g., 'core_perception.yaml')
        
    Returns:
        Dictionary containing the parsed YAML content, or empty dict on error.
    """
    settings = get_settings()
    
    # Standard path: knowledge/system/<filename>
    # We use settings.app.knowledge_dir which defaults to 'knowledge'
    try:
        # Resolve path relative to project root
        # In most deployments, the working directory is the project root
        project_root = Path(os.getcwd())
        knowledge_dir = project_root / settings.app.knowledge_dir
        file_path = knowledge_dir / "system" / filename
        
        if not file_path.exists():
            # Fallback for different execution contexts
            # Try relative to this file's parent's parent (shared/knowledge/...)
            file_path = Path(__file__).parents[2] / settings.app.knowledge_dir / "system" / filename

        if not file_path.exists():
            log.warning("System knowledge file not found", path=str(file_path))
            return {}
            
        with open(file_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            return data if isinstance(data, dict) else {}
            
    except Exception as e:
        log.error("Failed to load system knowledge", filename=filename, error=str(e))
        return {}
