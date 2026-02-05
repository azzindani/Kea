from textblob import Word
from typing import List, Dict, Any
import random

def lemmatize_word(word: str, pos: str = "n") -> str:
    """Get lemma of a word (pos: n, v, a, r)."""
    w = Word(word)
    return w.lemmatize(pos)

def singularize_word(word: str) -> str:
    """Convert to singular."""
    w = Word(word)
    return w.singularize()

def pluralize_word(word: str) -> str:
    """Convert to plural."""
    w = Word(word)
    return w.pluralize()

def spellcheck_word(word: str) -> List[List[Any]]:
    """Get spelling suggestions with confidence [(word, confidence)]."""
    w = Word(word)
    return w.spellcheck()

def define_word(word: str) -> List[str]:
    """Get definition from WordNet."""
    w = Word(word)
    return w.definitions

def get_synsets(word: str) -> List[str]:
    """Get synset names from WordNet."""
    w = Word(word)
    return [str(s) for s in w.synsets]

def get_synonyms(word: str) -> List[str]:
    """Simplify synsets into a list of synonyms."""
    w = Word(word)
    synonyms = set()
    for synset in w.synsets:
        for lemma in synset.lemmas():
            synonyms.add(lemma.name())
    return list(synonyms)

def stem_word(word: str) -> str:
    """Stemming (using Porter stemmer by default via TextBlob)."""
    w = Word(word)
    return w.stem()
