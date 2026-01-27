from rapidfuzz import process, fuzz
from typing import List, Tuple, Optional, Any, Union, Dict

def extract(query: str, choices: List[str], scorer: str = "ratio", limit: Optional[int] = 5, score_cutoff: Optional[float] = 0) -> List[Tuple[str, float, int]]:
    """Get all matches with scores."""
    # Map string scorer name to function
    scorer_func = getattr(fuzz, scorer, fuzz.ratio)
    results = process.extract(query, choices, scorer=scorer_func, limit=limit, score_cutoff=score_cutoff)
    # rapidfuzz returns (match, score, index)
    return results

def extractOne(query: str, choices: List[str], scorer: str = "ratio", score_cutoff: Optional[float] = 0) -> Optional[Tuple[str, float, int]]:
    """Get the single best match."""
    scorer_func = getattr(fuzz, scorer, fuzz.ratio)
    result = process.extractOne(query, choices, scorer=scorer_func, score_cutoff=score_cutoff)
    return result

def extract_iter(query: str, choices: List[str], scorer: str = "ratio", score_cutoff: Optional[float] = 0) -> List[Tuple[str, float, int]]:
    """Generator-based extraction (converted to list for MCP)."""
    scorer_func = getattr(fuzz, scorer, fuzz.ratio)
    # process.extract_iter exists in newer versions, or just use extract with limit=None
    try:
        return list(process.extract_iter(query, choices, scorer=scorer_func, score_cutoff=score_cutoff))
    except AttributeError:
        # Fallback if extract_iter not present
        return process.extract(query, choices, scorer=scorer_func, limit=None, score_cutoff=score_cutoff)

def extract_indices(query: str, choices: List[str], scorer: str = "ratio", limit: Optional[int] = 5, score_cutoff: Optional[float] = 0) -> List[int]:
    """Get ONLY indices of matches."""
    scorer_func = getattr(fuzz, scorer, fuzz.ratio)
    results = process.extract(query, choices, scorer=scorer_func, limit=limit, score_cutoff=score_cutoff)
    return [res[2] for res in results]
