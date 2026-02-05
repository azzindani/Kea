from rapidfuzz import fuzz
from typing import Optional

def ratio(s1: str, s2: str, score_cutoff: Optional[float] = 0) -> float:
    """Indel similarity ratio."""
    return fuzz.ratio(s1, s2, score_cutoff=score_cutoff)

def partial_ratio(s1: str, s2: str, score_cutoff: Optional[float] = 0) -> float:
    """Best partial match."""
    return fuzz.partial_ratio(s1, s2, score_cutoff=score_cutoff)

def token_sort_ratio(s1: str, s2: str, score_cutoff: Optional[float] = 0) -> float:
    """Sort words then compare."""
    return fuzz.token_sort_ratio(s1, s2, score_cutoff=score_cutoff)

def token_set_ratio(s1: str, s2: str, score_cutoff: Optional[float] = 0) -> float:
    """Compare unique words intersection."""
    return fuzz.token_set_ratio(s1, s2, score_cutoff=score_cutoff)

def token_ratio(s1: str, s2: str, score_cutoff: Optional[float] = 0) -> float:
    """Helper for token-based comparison (often alias for token_sort)."""
    return fuzz.token_ratio(s1, s2, score_cutoff=score_cutoff)

def partial_token_sort_ratio(s1: str, s2: str, score_cutoff: Optional[float] = 0) -> float:
    """Partial match on sorted tokens."""
    return fuzz.partial_token_sort_ratio(s1, s2, score_cutoff=score_cutoff)

def partial_token_set_ratio(s1: str, s2: str, score_cutoff: Optional[float] = 0) -> float:
    """Partial match on token set."""
    return fuzz.partial_token_set_ratio(s1, s2, score_cutoff=score_cutoff)

def wratio(s1: str, s2: str, score_cutoff: Optional[float] = 0) -> float:
    """Weighted ratio (heuristics for length/order)."""
    return fuzz.WRatio(s1, s2, score_cutoff=score_cutoff)

def qratio(s1: str, s2: str, score_cutoff: Optional[float] = 0) -> float:
    """Quick ratio (faster, slightly different)."""
    return fuzz.QRatio(s1, s2, score_cutoff=score_cutoff)

def quick_lev_ratio(s1: str, s2: str, score_cutoff: Optional[float] = 0) -> float:
    """Quick Levenshtein ratio."""
    return fuzz.quick_lev_ratio(s1, s2, score_cutoff=score_cutoff)
