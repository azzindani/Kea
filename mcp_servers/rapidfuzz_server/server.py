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
@mcp.tool()
def preprocess_string(text: str) -> str: return core_ops.preprocess_string(text)
@mcp.tool()
def validate_choices(choices: List[str]) -> bool: return core_ops.validate_choices(choices)
@mcp.tool()
def default_process(text: str) -> str: return core_ops.default_process(text)

# ==========================================
# 2. Ratios
# ==========================================
@mcp.tool()
def ratio(s1: str, s2: str, score_cutoff: Optional[float] = 0) -> float: return ratio_ops.ratio(s1, s2, score_cutoff)
@mcp.tool()
def partial_ratio(s1: str, s2: str, score_cutoff: Optional[float] = 0) -> float: return ratio_ops.partial_ratio(s1, s2, score_cutoff)
@mcp.tool()
def token_sort_ratio(s1: str, s2: str, score_cutoff: Optional[float] = 0) -> float: return ratio_ops.token_sort_ratio(s1, s2, score_cutoff)
@mcp.tool()
def token_set_ratio(s1: str, s2: str, score_cutoff: Optional[float] = 0) -> float: return ratio_ops.token_set_ratio(s1, s2, score_cutoff)
@mcp.tool()
def token_ratio(s1: str, s2: str, score_cutoff: Optional[float] = 0) -> float: return ratio_ops.token_ratio(s1, s2, score_cutoff)
@mcp.tool()
def partial_token_sort_ratio(s1: str, s2: str, score_cutoff: Optional[float] = 0) -> float: return ratio_ops.partial_token_sort_ratio(s1, s2, score_cutoff)
@mcp.tool()
def partial_token_set_ratio(s1: str, s2: str, score_cutoff: Optional[float] = 0) -> float: return ratio_ops.partial_token_set_ratio(s1, s2, score_cutoff)
@mcp.tool()
def wratio(s1: str, s2: str, score_cutoff: Optional[float] = 0) -> float: return ratio_ops.wratio(s1, s2, score_cutoff)
@mcp.tool()
def qratio(s1: str, s2: str, score_cutoff: Optional[float] = 0) -> float: return ratio_ops.qratio(s1, s2, score_cutoff)
@mcp.tool()
def quick_lev_ratio(s1: str, s2: str, score_cutoff: Optional[float] = 0) -> float: return ratio_ops.quick_lev_ratio(s1, s2, score_cutoff)

# ==========================================
# 3. Distances
# ==========================================
@mcp.tool()
def levenshtein_distance(s1: str, s2: str) -> int: return distance_ops.levenshtein_distance(s1, s2)
@mcp.tool()
def levenshtein_normalized_distance(s1: str, s2: str) -> float: return distance_ops.levenshtein_normalized_distance(s1, s2)
@mcp.tool()
def levenshtein_similarity(s1: str, s2: str) -> int: return distance_ops.levenshtein_similarity(s1, s2)
@mcp.tool()
def levenshtein_normalized_similarity(s1: str, s2: str) -> float: return distance_ops.levenshtein_normalized_similarity(s1, s2)
@mcp.tool()
def hamming_distance(s1: str, s2: str) -> int: return distance_ops.hamming_distance(s1, s2)
@mcp.tool()
def hamming_normalized_distance(s1: str, s2: str) -> float: return distance_ops.hamming_normalized_distance(s1, s2)
@mcp.tool()
def hamming_similarity(s1: str, s2: str) -> int: return distance_ops.hamming_similarity(s1, s2)
@mcp.tool()
def hamming_normalized_similarity(s1: str, s2: str) -> float: return distance_ops.hamming_normalized_similarity(s1, s2)
@mcp.tool()
def jaro_distance(s1: str, s2: str) -> float: return distance_ops.jaro_distance(s1, s2)
@mcp.tool()
def jaro_similarity(s1: str, s2: str) -> float: return distance_ops.jaro_similarity(s1, s2)
@mcp.tool()
def jaro_winkler_distance(s1: str, s2: str) -> float: return distance_ops.jaro_winkler_distance(s1, s2)
@mcp.tool()
def jaro_winkler_similarity(s1: str, s2: str) -> float: return distance_ops.jaro_winkler_similarity(s1, s2)
@mcp.tool()
def damerau_levenshtein_distance(s1: str, s2: str) -> int: return distance_ops.damerau_levenshtein_distance(s1, s2)
@mcp.tool()
def damerau_levenshtein_normalized_distance(s1: str, s2: str) -> float: return distance_ops.damerau_levenshtein_normalized_distance(s1, s2)
@mcp.tool()
def indel_distance(s1: str, s2: str) -> int: return distance_ops.indel_distance(s1, s2)
@mcp.tool()
def indel_normalized_distance(s1: str, s2: str) -> float: return distance_ops.indel_normalized_distance(s1, s2)
@mcp.tool()
def osa_distance(s1: str, s2: str) -> int: return distance_ops.osa_distance(s1, s2)
@mcp.tool()
def osa_normalized_distance(s1: str, s2: str) -> float: return distance_ops.osa_normalized_distance(s1, s2)
@mcp.tool()
def lcs_seq_distance(s1: str, s2: str) -> int: return distance_ops.lcs_seq_distance(s1, s2)
@mcp.tool()
def lcs_seq_similarity(s1: str, s2: str) -> int: return distance_ops.lcs_seq_similarity(s1, s2)
@mcp.tool()
def prefix_distance(s1: str, s2: str) -> int: return distance_ops.prefix_distance(s1, s2)
@mcp.tool()
def suffix_distance(s1: str, s2: str) -> int: return distance_ops.suffix_distance(s1, s2)

# ==========================================
# 4. Process
# ==========================================
@mcp.tool()
def extract(query: str, choices: List[str], scorer: str = "ratio", limit: Optional[int] = 5, score_cutoff: Optional[float] = 0) -> List[Tuple[str, float, int]]: return process_ops.extract(query, choices, scorer, limit, score_cutoff)
@mcp.tool()
def extractOne(query: str, choices: List[str], scorer: str = "ratio", score_cutoff: Optional[float] = 0) -> Optional[Tuple[str, float, int]]: return process_ops.extractOne(query, choices, scorer, score_cutoff)
@mcp.tool()
def extract_iter(query: str, choices: List[str], scorer: str = "ratio", score_cutoff: Optional[float] = 0) -> List[Tuple[str, float, int]]: return process_ops.extract_iter(query, choices, scorer, score_cutoff)
@mcp.tool()
def extract_indices(query: str, choices: List[str], scorer: str = "ratio", limit: Optional[int] = 5, score_cutoff: Optional[float] = 0) -> List[int]: return process_ops.extract_indices(query, choices, scorer, limit, score_cutoff)

# ==========================================
# 5. Matrix & Bulk
# ==========================================
@mcp.tool()
def cdist_distance(queries: List[str], choices: List[str], metric: str = "Levenshtein") -> List[List[float]]: return matrix_ops.cdist_distance(queries, choices, metric)
@mcp.tool()
def cdist_ratio(queries: List[str], choices: List[str], scorer: str = "ratio") -> List[List[float]]: return matrix_ops.cdist_ratio(queries, choices, scorer)
@mcp.tool()
def pdist_distance(queries: List[str], metric: str = "Levenshtein") -> List[List[float]]: return matrix_ops.pdist_distance(queries, metric)
@mcp.tool()
def bulk_compare_lists(queries: List[str], choices: List[str], scorer: str = "ratio", top_k: int = 1) -> List[Dict[str, Any]]: return matrix_ops.bulk_compare_lists(queries, choices, scorer, top_k)

# ==========================================
# 6. Super Tools
# ==========================================
@mcp.tool()
def deduplicate_list(items: List[str], threshold: float = 90.0) -> List[str]: return super_ops.deduplicate_list(items, threshold)
@mcp.tool()
def cluster_strings(items: List[str], threshold: float = 80.0) -> Dict[str, List[str]]: return super_ops.cluster_strings(items, threshold)
@mcp.tool()
def fuzzy_merge_datasets(list_a: List[Dict[str, Any]], list_b: List[Dict[str, Any]], key_a: str, key_b: str, threshold: float = 85.0) -> List[Dict[str, Any]]: return super_ops.fuzzy_merge_datasets(list_a, list_b, key_a, key_b, threshold)
@mcp.tool()
def smart_search(query: str, choices: List[str]) -> List[Dict[str, Any]]: return super_ops.smart_search(query, choices)
@mcp.tool()
def rank_candidates(query: str, candidates: List[str]) -> List[str]: return super_ops.rank_candidates(query, candidates)
@mcp.tool()
def filter_by_similarity(query: str, items: List[str], threshold: float = 70.0) -> List[str]: return super_ops.filter_by_similarity(query, items, threshold)
@mcp.tool()
def full_fuzzy_audit(items: List[str]) -> Dict[str, Any]: return super_ops.full_fuzzy_audit(items)

if __name__ == "__main__":
    mcp.run()