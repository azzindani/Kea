from textblob import TextBlob
from collections import Counter
from typing import List, Dict, Any

def full_text_report(text: str) -> Dict[str, Any]:
    """JSON with sentiment, tags, nouns, language, correctness."""
    blob = TextBlob(text)
    return {
        "sentiment": {"polarity": blob.sentiment.polarity, "subjectivity": blob.sentiment.subjectivity},
        "language": "unsupported (feature removed in TextBlob)",
        "noun_phrases": list(blob.noun_phrases),
        "sentences_count": len(blob.sentences),
        "words_count": len(blob.words),
        "spelling_correction": str(blob.correct()) if blob.sentiment.polarity < 0.5 else "Skipped (High Confidence)" # Optimization
    }

def summarize_content(text: str, top_n: int = 3) -> List[str]:
    """Extract sentences with highest Noun Phrase density."""
    blob = TextBlob(text)
    scored_sentences = []
    
    for s in blob.sentences:
        score = len(s.noun_phrases)
        scored_sentences.append((score, s.raw))
        
    # Sort desc
    scored_sentences.sort(key=lambda x: x[0], reverse=True)
    return [s[1] for s in scored_sentences[:top_n]]

def compare_sentiments(text1: str, text2: str) -> Dict[str, Any]:
    """Compare polarity of two texts."""
    b1 = TextBlob(text1)
    b2 = TextBlob(text2)
    p1 = b1.sentiment.polarity
    p2 = b2.sentiment.polarity
    diff = abs(p1 - p2)
    
    return {
        "text1_polarity": p1,
        "text2_polarity": p2,
        "difference": diff,
        "more_positive": "text1" if p1 > p2 else "text2" if p2 > p1 else "equal"
    }

def build_frequency_distribution(texts: List[str], top_n: int = 10) -> Dict[str, int]:
    """Top words across many texts (Stopwords removed - basic list)."""
    stops = {"the", "a", "an", "and", "or", "but", "is", "are", "was", "were", "in", "on", "at", "to", "for", "of", "with"}
    all_words = []
    for t in texts:
        blob = TextBlob(t.lower())
        all_words.extend([w for w in blob.words if w not in stops and w.isalpha()])
    
    return dict(Counter(all_words).most_common(top_n))

def extract_key_sentences(text: str, keyword: str) -> List[str]:
    """Filter sentences by keyword inclusion."""
    blob = TextBlob(text)
    return [s.raw for s in blob.sentences if keyword.lower() in s.lower()]

def categorize_by_sentiment(texts: List[str]) -> Dict[str, List[str]]:
    """Bucket texts into Positive/Neutral/Negative."""
    buckets = {"positive": [], "neutral": [], "negative": []}
    for t in texts:
        pol = TextBlob(t).sentiment.polarity
        if pol > 0.1: buckets["positive"].append(t)
        elif pol < -0.1: buckets["negative"].append(t)
        else: buckets["neutral"].append(t)
    return buckets

def mixed_sentiment_analysis(texts: List[str]) -> List[Dict[str, Any]]:
    """Identify texts with high subjectivity but low polarity (controversial/opinionated but balanced?)."""
    results = []
    for t in texts:
        blob = TextBlob(t)
        subj = blob.sentiment.subjectivity
        pol = abs(blob.sentiment.polarity)
        
        # High subjectivity (>0.5) and Low polarity (<0.2)
        if subj > 0.5 and pol < 0.2:
            results.append({
                "text": t[:50],
                "subjectivity": subj,
                "polarity": blob.sentiment.polarity,
                "type": "Mixed/Controversial"
            })
    return results

def clean_and_analyze(text: str) -> Dict[str, Any]:
    """Preprocess (lower, clean) then analyze."""
    # TextBlob doesn't explicitly need cleaning, but we can normalize
    cleaned = " ".join(text.split()).lower()
    return full_text_report(cleaned)

def find_similar_spelling(target: str, text: str) -> List[str]:
    """Find words in text close to target spelling (simple implementation)."""
    blob = TextBlob(text)
    target_word = target.lower()
    matches = []
    for w in blob.words:
        # Check if correction matches
        if w.lower() == target_word: continue
        if w.correct() == target_word:
            matches.append(w)
    return list(set(matches))
