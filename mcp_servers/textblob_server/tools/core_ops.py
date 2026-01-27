from textblob import TextBlob
import textblob.download_corpora
import structlog
from typing import Dict, Any

logger = structlog.get_logger()

# Global check to ensure corpora are present (runs once usually)
CORPORA_DOWNLOADED = False

def ensure_corpora() -> str:
    """Download necessary NLTK corpora (lite version)."""
    global CORPORA_DOWNLOADED
    if not CORPORA_DOWNLOADED:
        try:
            logger.info("downloading_textblob_corpora")
            textblob.download_corpora.main() # Defaults to lite
            CORPORA_DOWNLOADED = True
            return "Corpora downloaded successfully."
        except Exception as e:
            return f"Error downloading corpora: {str(e)}"
    return "Corpora already present."

def blob_properties_full(text: str) -> Dict[str, Any]:
    """Return all standard properties of a blob."""
    blob = TextBlob(text)
    return {
        "polarity": blob.sentiment.polarity,
        "subjectivity": blob.sentiment.subjectivity,
        "language_detected": blob.detect_language() if len(text) > 3 else "unknown", # Check length to avoid error
        "sentences_count": len(blob.sentences),
        "words_count": len(blob.words),
        "noun_phrases_count": len(blob.noun_phrases)
    }
