from textblob import TextBlob
from typing import List, Dict, Any, Optional

def detect_language(text: str) -> str:
    """Detect language code (e.g. 'en'). Checks text length."""
    if len(text) < 3: return "unknown"
    blob = TextBlob(text)
    try:
        return blob.detect_language()
    except Exception as e:
        return f"Error: {str(e)}"

def translate_text(text: str, to_lang: str = "en", from_lang: Optional[str] = None) -> str:
    """Translate blob to target language (Google Translate API)."""
    blob = TextBlob(text)
    try:
        return str(blob.translate(to=to_lang, from_lang=from_lang))
    except Exception as e:
        return f"Translation Error: {str(e)}"

def get_languages_list() -> List[str]:
    """Helper to list common supported codes (static list)."""
    # Just a sample, not exhaustive
    return ["en", "es", "fr", "de", "zh-CN", "ja", "ru", "pt", "it", "ar"]
