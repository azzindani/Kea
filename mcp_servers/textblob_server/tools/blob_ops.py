from textblob import TextBlob
from typing import List, Dict, Any

def analyze_sentiment(text: str) -> Dict[str, float]:
    """Return polarity and subjectivity."""
    blob = TextBlob(text)
    return {
        "polarity": blob.sentiment.polarity,
        "subjectivity": blob.sentiment.subjectivity
    }

def extract_noun_phrases(text: str) -> List[str]:
    """Get list of noun phrases."""
    blob = TextBlob(text)
    return list(blob.noun_phrases)

def tag_pos(text: str) -> List[List[str]]:
    """Get Part-of-Speech tags."""
    blob = TextBlob(text)
    # Returns list of (word, tag) tuples
    return [list(t) for t in blob.tags]

def parse_text(text: str) -> str:
    """Parse text into structure (tags, relations)."""
    blob = TextBlob(text)
    return blob.parse()

def tokenize_words(text: str) -> List[str]:
    """Get word tokens."""
    blob = TextBlob(text)
    return list(blob.words)

def tokenize_sentences(text: str) -> List[str]:
    """Get sentence tokens."""
    blob = TextBlob(text)
    return [s.raw for s in blob.sentences]

def get_word_counts(text: str) -> Dict[str, int]:
    """Frequency dictionary of words."""
    blob = TextBlob(text)
    return dict(blob.word_counts)

def get_ngrams(text: str, n: int = 3) -> List[List[str]]:
    """Get N-grams (n=2, 3, etc.)."""
    blob = TextBlob(text)
    # ngrams returns list of WordLists, convert to list of lists/strings
    return [list(gram) for gram in blob.ngrams(n=n)]

def correct_spelling(text: str) -> str:
    """Return corrected text string."""
    blob = TextBlob(text)
    return str(blob.correct())

def get_sentences_sentiment(text: str) -> List[Dict[str, Any]]:
    """Sentiment for each sentence individually."""
    blob = TextBlob(text)
    results = []
    for s in blob.sentences:
        results.append({
            "sentence": s.raw,
            "polarity": s.sentiment.polarity,
            "subjectivity": s.sentiment.subjectivity
        })
    return results
