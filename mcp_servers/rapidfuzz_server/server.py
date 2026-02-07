
import sys
from pathlib import Path
# Fix for importing 'shared' module from root when running in JIT mode
root_path = str(Path(__file__).parents[2])
if root_path not in sys.path:
    sys.path.append(root_path)

# /// script
# dependencies = [
#   "mcp",
#   "numpy",
#   "pandas",
#   "rapidfuzz",
#   "structlog",
# ]
# ///

from mcp.server.fastmcp import FastMCP
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
from tools import core_ops, ratio_ops, distance_ops, process_ops, matrix_ops, super_ops
import structlog
from typing import List, Dict, Any, Optional, Tuple, Union

logger = structlog.get_logger()

# Create the FastMCP server
mcp = FastMCP("rapidfuzz_server", dependencies=["rapidfuzz", "pandas", "numpy"])

# ==========================================
# 1. Core
# ==========================================
# ==========================================
# 1. Core
# ==========================================
@mcp.tool()
def preprocess_string(text: str) -> str: 
    """PREPROCESSES string. [ACTION]
    
    [RAG Context]
    Lowercase, trim, and remove non-alphanumeric.
    Returns cleaned string.
    """
    return core_ops.preprocess_string(text)

@mcp.tool()
def validate_choices(choices: List[str]) -> bool: 
    """VALIDATES choices. [ACTION]
    
    [RAG Context]
    Check if list of choices is valid.
    Returns boolean.
    """
    return core_ops.validate_choices(choices)

@mcp.tool()
def default_process(text: str) -> str: 
    """PROCESSES default. [ACTION]
    
    [RAG Context]
    Default string processor for RapidFuzz.
    Returns processed string.
    """
    return core_ops.default_process(text)

# ==========================================
# 2. Ratios
# ==========================================
@mcp.tool()
def ratio(s1: str, s2: str, score_cutoff: Optional[float] = 0) -> float: 
    """CALCULATES Ratio. [ACTION]
    
    [RAG Context]
    Simple Levenshtein distance-based ratio.
    Returns float (0-100).
    """
    return ratio_ops.ratio(s1, s2, score_cutoff)

@mcp.tool()
def partial_ratio(s1: str, s2: str, score_cutoff: Optional[float] = 0) -> float: 
    """CALCULATES Partial Ratio. [ACTION]
    
    [RAG Context]
    Ratio of most similar substring.
    Returns float (0-100).
    """
    return ratio_ops.partial_ratio(s1, s2, score_cutoff)

@mcp.tool()
def token_sort_ratio(s1: str, s2: str, score_cutoff: Optional[float] = 0) -> float: 
    """CALCULATES Token Sort Ratio. [ACTION]
    
    [RAG Context]
    Sort tokens before calculating ratio.
    Returns float (0-100).
    """
    return ratio_ops.token_sort_ratio(s1, s2, score_cutoff)

@mcp.tool()
def token_set_ratio(s1: str, s2: str, score_cutoff: Optional[float] = 0) -> float: 
    """CALCULATES Token Set Ratio. [ACTION]
    
    [RAG Context]
    Set intersection of tokens ratio.
    Returns float (0-100).
    """
    return ratio_ops.token_set_ratio(s1, s2, score_cutoff)

@mcp.tool()
def token_ratio(s1: str, s2: str, score_cutoff: Optional[float] = 0) -> float: 
    """CALCULATES Token Ratio. [ACTION]
    
    [RAG Context]
    Comprehensive token-based ratio.
    Returns float (0-100).
    """
    return ratio_ops.token_ratio(s1, s2, score_cutoff)

@mcp.tool()
def partial_token_sort_ratio(s1: str, s2: str, score_cutoff: Optional[float] = 0) -> float: 
    """CALCULATES Partial Token Sort. [ACTION]
    
    [RAG Context]
    Partial ratio with sorted tokens.
    Returns float (0-100).
    """
    return ratio_ops.partial_token_sort_ratio(s1, s2, score_cutoff)

@mcp.tool()
def partial_token_set_ratio(s1: str, s2: str, score_cutoff: Optional[float] = 0) -> float: 
    """CALCULATES Partial Token Set. [ACTION]
    
    [RAG Context]
    Partial ratio with token set intersection.
    Returns float (0-100).
    """
    return ratio_ops.partial_token_set_ratio(s1, s2, score_cutoff)

@mcp.tool()
def wratio(s1: str, s2: str, score_cutoff: Optional[float] = 0) -> float: 
    """CALCULATES Weighted Ratio. [ACTION]
    
    [RAG Context]
    Weighted average of different ratios.
    Returns float (0-100).
    """
    return ratio_ops.wratio(s1, s2, score_cutoff)

@mcp.tool()
def qratio(s1: str, s2: str, score_cutoff: Optional[float] = 0) -> float: 
    """CALCULATES Quick Ratio. [ACTION]
    
    [RAG Context]
    Optimized quick ratio calculation.
    Returns float (0-100).
    """
    return ratio_ops.qratio(s1, s2, score_cutoff)

@mcp.tool()
def quick_lev_ratio(s1: str, s2: str, score_cutoff: Optional[float] = 0) -> float: 
    """CALCULATES Quick Lev Ratio. [ACTION]
    
    [RAG Context]
    Quick Levenshtein ratio.
    Returns float (0-100).
    """
    return ratio_ops.quick_lev_ratio(s1, s2, score_cutoff)

# ==========================================
# 3. Distances
# ==========================================
# ==========================================
# 3. Distances
# ==========================================
@mcp.tool()
def levenshtein_distance(s1: str, s2: str) -> int: 
    """CALCULATES Levenshtein distance. [ACTION]
    
    [RAG Context]
    Minimum edits (insert, delete, substitute).
    Returns int.
    """
    return distance_ops.levenshtein_distance(s1, s2)

@mcp.tool()
def levenshtein_normalized_distance(s1: str, s2: str) -> float: 
    """CALCULATES Normalized Levenshtein. [ACTION]
    
    [RAG Context]
    Normalized distance (0.0 to 1.0).
    Returns float.
    """
    return distance_ops.levenshtein_normalized_distance(s1, s2)

@mcp.tool()
def levenshtein_similarity(s1: str, s2: str) -> int: 
    """CALCULATES Levenshtein similarity. [ACTION]
    
    [RAG Context]
    Similarity score based on Levenshtein.
    Returns int.
    """
    return distance_ops.levenshtein_similarity(s1, s2)

@mcp.tool()
def levenshtein_normalized_similarity(s1: str, s2: str) -> float: 
    """CALCULATES Norm Levenshtein Sim. [ACTION]
    
    [RAG Context]
    Normalized similarity (0.0 to 1.0).
    Returns float.
    """
    return distance_ops.levenshtein_normalized_similarity(s1, s2)

@mcp.tool()
def hamming_distance(s1: str, s2: str) -> int: 
    """CALCULATES Hamming distance. [ACTION]
    
    [RAG Context]
    Number of positions where chars differ (equal len).
    Returns int.
    """
    return distance_ops.hamming_distance(s1, s2)

@mcp.tool()
def hamming_normalized_distance(s1: str, s2: str) -> float: 
    """CALCULATES Norm Hamming Dist. [ACTION]
    
    [RAG Context]
    Normalized Hamming distance.
    Returns float.
    """
    return distance_ops.hamming_normalized_distance(s1, s2)

@mcp.tool()
def hamming_similarity(s1: str, s2: str) -> int: 
    """CALCULATES Hamming similarity. [ACTION]
    
    [RAG Context]
    Similarity based on Hamming distance.
    Returns int.
    """
    return distance_ops.hamming_similarity(s1, s2)

@mcp.tool()
def hamming_normalized_similarity(s1: str, s2: str) -> float: 
    """CALCULATES Norm Hamming Sim. [ACTION]
    
    [RAG Context]
    Normalized Hamming similarity.
    Returns float.
    """
    return distance_ops.hamming_normalized_similarity(s1, s2)

@mcp.tool()
def jaro_distance(s1: str, s2: str) -> float: 
    """CALCULATES Jaro distance. [ACTION]
    
    [RAG Context]
    Distance based on Jaro measure.
    Returns float.
    """
    return distance_ops.jaro_distance(s1, s2)

@mcp.tool()
def jaro_similarity(s1: str, s2: str) -> float: 
    """CALCULATES Jaro similarity. [ACTION]
    
    [RAG Context]
    Similarity based on Jaro measure.
    Returns float.
    """
    return distance_ops.jaro_similarity(s1, s2)

@mcp.tool()
def jaro_winkler_distance(s1: str, s2: str) -> float: 
    """CALCULATES Jaro-Winkler Dist. [ACTION]
    
    [RAG Context]
    Distance giving prefix weight.
    Returns float.
    """
    return distance_ops.jaro_winkler_distance(s1, s2)

@mcp.tool()
def jaro_winkler_similarity(s1: str, s2: str) -> float: 
    """CALCULATES Jaro-Winkler Sim. [ACTION]
    
    [RAG Context]
    Similarity giving prefix weight.
    Returns float.
    """
    return distance_ops.jaro_winkler_similarity(s1, s2)

@mcp.tool()
def damerau_levenshtein_distance(s1: str, s2: str) -> int: 
    """CALCULATES Damerau-Levenshtein. [ACTION]
    
    [RAG Context]
    Edit distance including transpositions.
    Returns int.
    """
    return distance_ops.damerau_levenshtein_distance(s1, s2)

@mcp.tool()
def damerau_levenshtein_normalized_distance(s1: str, s2: str) -> float: 
    """CALCULATES Norm Damerau-Lev. [ACTION]
    
    [RAG Context]
    Normalized Damerau-Levenshtein distance.
    Returns float.
    """
    return distance_ops.damerau_levenshtein_normalized_distance(s1, s2)

@mcp.tool()
def indel_distance(s1: str, s2: str) -> int: 
    """CALCULATES Indel distance. [ACTION]
    
    [RAG Context]
    Insertions and deletions only.
    Returns int.
    """
    return distance_ops.indel_distance(s1, s2)

@mcp.tool()
def indel_normalized_distance(s1: str, s2: str) -> float: 
    """CALCULATES Norm Indel Dist. [ACTION]
    
    [RAG Context]
    Normalized Indel distance.
    Returns float.
    """
    return distance_ops.indel_normalized_distance(s1, s2)

@mcp.tool()
def osa_distance(s1: str, s2: str) -> int: 
    """CALCULATES OSA distance. [ACTION]
    
    [RAG Context]
    Optimal String Alignment distance.
    Returns int.
    """
    return distance_ops.osa_distance(s1, s2)

@mcp.tool()
def osa_normalized_distance(s1: str, s2: str) -> float: 
    """CALCULATES Norm OSA Dist. [ACTION]
    
    [RAG Context]
    Normalized OSA distance.
    Returns float.
    """
    return distance_ops.osa_normalized_distance(s1, s2)

@mcp.tool()
def lcs_seq_distance(s1: str, s2: str) -> int: 
    """CALCULATES LCS distance. [ACTION]
    
    [RAG Context]
    Longest Common Subsequence distance.
    Returns int.
    """
    return distance_ops.lcs_seq_distance(s1, s2)

@mcp.tool()
def lcs_seq_similarity(s1: str, s2: str) -> int: 
    """CALCULATES LCS similarity. [ACTION]
    
    [RAG Context]
    Similarity based on Longest Common Subsequence.
    Returns int.
    """
    return distance_ops.lcs_seq_similarity(s1, s2)

@mcp.tool()
def prefix_distance(s1: str, s2: str) -> int: 
    """CALCULATES Prefix distance. [ACTION]
    
    [RAG Context]
    Distance between prefixes.
    Returns int.
    """
    return distance_ops.prefix_distance(s1, s2)

@mcp.tool()
def suffix_distance(s1: str, s2: str) -> int: 
    """CALCULATES Suffix distance. [ACTION]
    
    [RAG Context]
    Distance between suffixes.
    Returns int.
    """
    return distance_ops.suffix_distance(s1, s2)

# ==========================================
# 4. Process
# ==========================================
# ==========================================
# 4. Process
# ==========================================
@mcp.tool()
def extract(query: str, choices: List[str], scorer: str = "ratio", limit: Optional[int] = 5, score_cutoff: Optional[float] = 0) -> List[Tuple[str, float, int]]: 
    """EXTRACTS best matches. [ACTION]
    
    [RAG Context]
    Find best matches for query in choices.
    Returns list of (match, score, index).
    """
    return process_ops.extract(query, choices, scorer, limit, score_cutoff)

@mcp.tool()
def extractOne(query: str, choices: List[str], scorer: str = "ratio", score_cutoff: Optional[float] = 0) -> Optional[Tuple[str, float, int]]: 
    """EXTRACTS best match. [ACTION]
    
    [RAG Context]
    Find single best match for query.
    Returns (match, score, index) or None.
    """
    return process_ops.extractOne(query, choices, scorer, score_cutoff)

@mcp.tool()
def extract_iter(query: str, choices: List[str], scorer: str = "ratio", score_cutoff: Optional[float] = 0) -> List[Tuple[str, float, int]]: 
    """EXTRACTS matches (iter). [ACTION]
    
    [RAG Context]
    Yield matches over score_cutoff.
    Returns list of (match, score, index).
    """
    return process_ops.extract_iter(query, choices, scorer, score_cutoff)

@mcp.tool()
def extract_indices(query: str, choices: List[str], scorer: str = "ratio", limit: Optional[int] = 5, score_cutoff: Optional[float] = 0) -> List[int]: 
    """EXTRACTS match indices. [ACTION]
    
    [RAG Context]
    Get indices of best matches.
    Returns list of ints.
    """
    return process_ops.extract_indices(query, choices, scorer, limit, score_cutoff)

# ==========================================
# 5. Matrix & Bulk
# ==========================================
# ==========================================
# 5. Matrix & Bulk
# ==========================================
@mcp.tool()
def cdist_distance(queries: List[str], choices: List[str], metric: str = "Levenshtein") -> List[List[float]]: 
    """CALCULATES cdist distance. [ACTION]
    
    [RAG Context]
    Compute distance matrix between queries and choices.
    Returns matrix of floats.
    """
    return matrix_ops.cdist_distance(queries, choices, metric)

@mcp.tool()
def cdist_ratio(queries: List[str], choices: List[str], scorer: str = "ratio") -> List[List[float]]: 
    """CALCULATES cdist ratio. [ACTION]
    
    [RAG Context]
    Compute ratio matrix between queries and choices.
    Returns matrix of floats.
    """
    return matrix_ops.cdist_ratio(queries, choices, scorer)

@mcp.tool()
def pdist_distance(queries: List[str], metric: str = "Levenshtein") -> List[List[float]]: 
    """CALCULATES pdist distance. [ACTION]
    
    [RAG Context]
    Compute pairwise distance matrix for queries.
    Returns matrix of floats.
    """
    return matrix_ops.pdist_distance(queries, metric)

@mcp.tool()
def bulk_compare_lists(queries: List[str], choices: List[str], scorer: str = "ratio", top_k: int = 1) -> List[Dict[str, Any]]: 
    """COMPARES bulk lists. [ACTION]
    
    [RAG Context]
    Compare each query against all choices.
    Returns list of best matches per query.
    """
    return matrix_ops.bulk_compare_lists(queries, choices, scorer, top_k)

# ==========================================
# 6. Super Tools
# ==========================================
# ==========================================
# 6. Super Tools
# ==========================================
@mcp.tool()
def deduplicate_list(items: List[str], threshold: float = 90.0) -> List[str]: 
    """DEDUPLICATES list. [ACTION]
    
    [RAG Context]
    Remove near-duplicate strings.
    Returns list of unique strings.
    """
    return super_ops.deduplicate_list(items, threshold)

@mcp.tool()
def cluster_strings(items: List[str], threshold: float = 80.0) -> Dict[str, List[str]]: 
    """CLUSTERS strings. [ACTION]
    
    [RAG Context]
    Group similar strings together.
    Returns JSON dict.
    """
    return super_ops.cluster_strings(items, threshold)

@mcp.tool()
def fuzzy_merge_datasets(list_a: List[Dict[str, Any]], list_b: List[Dict[str, Any]], key_a: str, key_b: str, threshold: float = 85.0) -> List[Dict[str, Any]]: 
    """MERGES datasets fuzzy. [ACTION]
    
    [RAG Context]
    Merge two lists of dicts on fuzzy key match.
    Returns list of merged dicts.
    """
    return super_ops.fuzzy_merge_datasets(list_a, list_b, key_a, key_b, threshold)

@mcp.tool()
def smart_search(query: str, choices: List[str]) -> List[Dict[str, Any]]: 
    """SEARCHES smart (Multi-algo). [ACTION]
    
    [RAG Context]
    Search using multiple algorithms and heuristic.
    Returns list of matches.
    """
    return super_ops.smart_search(query, choices)

@mcp.tool()
def rank_candidates(query: str, candidates: List[str]) -> List[str]: 
    """RANKS candidates. [ACTION]
    
    [RAG Context]
    Sort candidates by similarity to query.
    Returns list of strings.
    """
    return super_ops.rank_candidates(query, candidates)

@mcp.tool()
def filter_by_similarity(query: str, items: List[str], threshold: float = 70.0) -> List[str]: 
    """FILTERS by similarity. [ACTION]
    
    [RAG Context]
    Keep items with similarity > threshold.
    Returns list of strings.
    """
    return super_ops.filter_by_similarity(query, items, threshold)

@mcp.tool()
def full_fuzzy_audit(items: List[str]) -> Dict[str, Any]: 
    """AUDITS fuzzy quality. [ACTION]
    
    [RAG Context]
    Analyze dataset for duplicates and clusters.
    Returns JSON dict.
    """
    return super_ops.full_fuzzy_audit(items)

if __name__ == "__main__":
    mcp.run()