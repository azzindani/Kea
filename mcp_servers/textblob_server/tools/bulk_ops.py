from textblob import TextBlob
from typing import List, Dict, Any

def bulk_analyze_sentiment(texts: List[str]) -> List[Dict[str, Any]]:
    """Sentiment for list of texts."""
    results = []
    for t in texts:
        blob = TextBlob(t)
        results.append({
            "text_preview": t[:30],
            "polarity": blob.sentiment.polarity,
            "subjectivity": blob.sentiment.subjectivity
        })
    return results

def bulk_extract_noun_phrases(texts: List[str]) -> List[List[str]]:
    """Noun phrases for list of texts."""
    return [list(TextBlob(t).noun_phrases) for t in texts]

def bulk_tag_pos(texts: List[str]) -> List[List[List[str]]]:
    """Tags for list of texts."""
    # Output: List of [List of [word, tag]]
    return [[list(pair) for pair in TextBlob(t).tags] for t in texts]

def bulk_correct_spelling(texts: List[str]) -> List[str]:
    """Correct spelling for list of texts."""
    return [str(TextBlob(t).correct()) for t in texts]

def bulk_detect_language(texts: List[str]) -> List[str]:
    """Detect language for list."""
    results = []
    for t in texts:
        if len(t) < 3:
            results.append("unknown")
            continue
        try:
            results.append(TextBlob(t).detect_language())
        except:
            results.append("error")
    return results

def bulk_translate(texts: List[str], to_lang: str = "en") -> List[str]:
    """Batch translation (Slow due to API calls)."""
    results = []
    for t in texts:
        try:
            results.append(str(TextBlob(t).translate(to=to_lang)))
        except Exception as e:
            results.append(f"Error: {e}")
    return results

def bulk_ngrams(texts: List[str], n: int = 3) -> List[List[List[str]]]:
    """Get ngrams for multiple docs."""
    return [[list(gram) for gram in TextBlob(t).ngrams(n=n)] for t in texts]
