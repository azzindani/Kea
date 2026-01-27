import rapidfuzz
from rapidfuzz import utils
import structlog
from typing import List, Any, Union, Optional

logger = structlog.get_logger()

def preprocess_string(text: str) -> str:
    """Standardize string: lowercase, trim, remove non-alphanumeric (via rapidfuzz.utils)."""
    return utils.default_process(text)

def validate_choices(choices: List[str]) -> bool:
    """Ensure list of choices is valid."""
    if not isinstance(choices, list):
        return False
    return all(isinstance(c, str) for c in choices)

def default_process(text: str) -> str:
    """Access default processor used by rapidfuzz."""
    return utils.default_process(text)

def utils_default_process(text: str) -> str:
    """Explicit utility wrapper for default_process."""
    return utils.default_process(text)
