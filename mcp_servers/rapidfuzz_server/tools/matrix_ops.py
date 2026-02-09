from rapidfuzz import process, distance, fuzz
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Union, Optional

def cdist_distance(queries: List[str], choices: List[str], metric: str = "Levenshtein") -> List[List[float]]:
    """Compute distance matrix (List A vs List B). Returns List of Lists (2D array)."""
    dist_obj = getattr(distance, metric, distance.Levenshtein)
    # Handle module vs function (e.g. distance.Levenshtein vs distance.Levenshtein.distance)
    dist_func = getattr(dist_obj, "distance", dist_obj)
    # workers=-1 means use all cores.
    matrix = process.cdist(queries, choices, scorer=dist_func, workers=-1)
    return matrix.tolist()

def cdist_ratio(queries: List[str], choices: List[str], scorer: str = "ratio") -> List[List[float]]:
    """Compute ratio matrix (List A vs List B)."""
    scorer_func = getattr(fuzz, scorer, fuzz.ratio)
    matrix = process.cdist(queries, choices, scorer=scorer_func, workers=-1)
    return matrix.tolist()

def pdist_distance(queries: List[str], metric: str = "Levenshtein") -> List[List[float]]:
    """Pairwise distance within one list (List A vs List A)."""
    # Simply call cdist on itself
    return cdist_distance(queries, queries, metric)

def bulk_compare_lists(queries: List[str], choices: List[str], scorer: str = "ratio", top_k: int = 1) -> List[Dict[str, Any]]:
    """Compare every item in A to every item in B returning top K best matches for each query."""
    scorer_func = getattr(fuzz, scorer, fuzz.ratio)
    # process.extract with limits
    results = []
    for q in queries:
        matches = process.extract(q, choices, scorer=scorer_func, limit=top_k)
        results.append({
            "query": q,
            "matches": [{"text": m[0], "score": m[1], "index": m[2]} for m in matches]
        })
    return results
