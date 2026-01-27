from mcp_servers.rapidfuzz_server.tools import matrix_ops, process_ops
from rapidfuzz import fuzz, process
from typing import List, Dict, Any, Union
import numpy as np

def deduplicate_list(items: List[str], threshold: float = 90.0) -> List[str]:
    """Remove duplicates based on fuzzy threshold."""
    unique_items = []
    for item in items:
        # Check against existing unique items
        if not unique_items:
            unique_items.append(item)
            continue
            
        # extractOne returns (match, score, index)
        # If best match is below threshold, it's new
        best = process_ops.extractOne(item, unique_items, scorer="ratio")
        if best and best[1] < threshold:
            unique_items.append(item)
    return unique_items

def cluster_strings(items: List[str], threshold: float = 80.0) -> Dict[str, List[str]]:
    """Group similar strings together (simple leader algorithm)."""
    clusters = {}
    for item in items:
        best_leader = None
        best_score = 0
        
        # Check against existing cluster leaders
        for leader in clusters.keys():
            score = fuzz.ratio(item, leader)
            if score > best_score:
                best_score = score
                best_leader = leader
        
        if best_score >= threshold:
            clusters[best_leader].append(item)
        else:
            # New cluster
            clusters[item] = [item]
            
    return clusters

def fuzzy_merge_datasets(
    list_a: List[Dict[str, Any]], 
    list_b: List[Dict[str, Any]], 
    key_a: str, 
    key_b: str, 
    threshold: float = 85.0
) -> List[Dict[str, Any]]:
    """Inner join two lists of dicts on fuzzy keys."""
    merged = []
    keys_b = [d[key_b] for d in list_b]
    
    for item_a in list_a:
        val_a = item_a.get(key_a)
        if not val_a: continue
        
        match = process.extractOne(val_a, keys_b, scorer=fuzz.ratio, score_cutoff=threshold)
        if match:
            # Match found: (text, score, index)
            # Combine dicts
            item_b = list_b[match[2]]
            new_item = {**item_a, **item_b, "_fuzzy_score": match[1]}
            merged.append(new_item)
            
    return merged

def smart_search(query: str, choices: List[str]) -> List[Dict[str, Any]]:
    """Pipeline trying Exact -> TokenSort -> Partial."""
    # 1. Exact
    if query in choices:
        return [{"match": query, "score": 100, "method": "exact"}]
        
    # 2. Token Sort (good for word order)
    matches = process.extract(query, choices, scorer=fuzz.token_sort_ratio, limit=5)
    high_score = matches[0][1] if matches else 0
    
    if high_score > 85:
        return [{"match": m[0], "score": m[1], "method": "token_sort"} for m in matches]
        
    # 3. Partial (substrings)
    matches_partial = process.extract(query, choices, scorer=fuzz.partial_ratio, limit=5)
    return [{"match": m[0], "score": m[1], "method": "partial"} for m in matches_partial]

def rank_candidates(query: str, candidates: List[str]) -> List[str]:
    """Rank candidate strings for search results."""
    # Use Weighted Ratio for best general ranking
    matches = process.extract(query, candidates, scorer=fuzz.WRatio, limit=None)
    # Return just the strings in order
    return [m[0] for m in matches]

def filter_by_similarity(query: str, items: List[str], threshold: float = 70.0) -> List[str]:
    """Filter list A keeping only items similar to target."""
    return [item for item in items if fuzz.ratio(query, item) >= threshold]

def full_fuzzy_audit(items: List[str]) -> Dict[str, Any]:
    """Comprehensive report on list similarity/duplication."""
    # Stats
    n = len(items)
    unique_exact = len(set(items))
    
    # Dedupe fuzzy
    deduped = deduplicate_list(items, threshold=90)
    return {
        "total_items": n,
        "unique_exact": unique_exact,
        "unique_fuzzy_90": len(deduped),
        "duplication_rate_fuzzy": 1.0 - (len(deduped) / n) if n else 0,
        "clusters": len(cluster_strings(items, 80))
    }
