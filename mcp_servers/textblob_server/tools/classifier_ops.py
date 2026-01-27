from textblob.classifiers import NaiveBayesClassifier, DecisionTreeClassifier
from textblob import TextBlob
from typing import List, Dict, Any, Union, Optional
import json

# Minimal pre-trained cache to avoid re-training constantly
CLASSIFIER_CACHE = {}

def classify_text(text: str, classifier_type: str = "simple") -> Dict[str, Any]:
    """Classify text using a basic rule or pre-trained model."""
    # Without external data, we can only do simple sentiment-based classification
    # or rely on a user-provided model name if we had persistent storage.
    # For now, we'll do a simple polarity check as a 'classifier' if no model.
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity
    label = "positive" if polarity > 0 else "negative" if polarity < 0 else "neutral"
    return {"label": label, "probability": abs(polarity)}

def train_simple_classifier(training_data: List[Dict[str, str]], model_name: str = "custom_nb") -> str:
    """Train a NaiveBayesClassifier. Data: [{'text': '...', 'label': '...'}, ...]"""
    # Convert dict list to tuple list [(text, label), ...]
    train_set = [(d['text'], d['label']) for d in training_data]
    cl = NaiveBayesClassifier(train_set)
    CLASSIFIER_CACHE[model_name] = cl
    return f"Model '{model_name}' trained on {len(train_set)} samples."

def evaluate_classifier(model_name: str, validation_data: List[Dict[str, str]]) -> Dict[str, float]:
    """Test accuracy of a cached model."""
    if model_name not in CLASSIFIER_CACHE:
        return {"error": "Model not found."}
    
    cl = CLASSIFIER_CACHE[model_name]
    valid_set = [(d['text'], d['label']) for d in validation_data]
    accuracy = cl.accuracy(valid_set)
    return {"accuracy": accuracy}

def classify_bulk(texts: List[str], model_name: str) -> List[Dict[str, Any]]:
    """Classify multiple texts using cached model."""
    if model_name not in CLASSIFIER_CACHE:
        return [{"error": "Model not found."}] * len(texts)
    
    cl = CLASSIFIER_CACHE[model_name]
    results = []
    for t in texts:
        prob_dist = cl.prob_classify(t)
        best_label = prob_dist.max()
        results.append({
            "text": t[:50],
            "label": best_label,
            "confidence": round(prob_dist.prob(best_label), 3)
        })
    return results
