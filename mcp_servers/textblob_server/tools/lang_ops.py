from textblob import TextBlob
from typing import List, Optional

def detect_language(text: str) -> str:
    """Detect language code (deprecated/removed in TextBlob)."""
    return "unsupported (feature removed in TextBlob)"

def translate_text(text: str, to_lang: str = "en", from_lang: Optional[str] = None) -> str:
    """Translate text (deprecated/removed in TextBlob)."""
    return "unsupported (feature removed in TextBlob)"

def get_languages_list() -> List[str]:
    """Helper to list common supported codes (static list)."""
    # Just a sample, not exhaustive
    return ["en", "es", "fr", "de", "zh-CN", "ja", "ru", "pt", "it", "ar"]
