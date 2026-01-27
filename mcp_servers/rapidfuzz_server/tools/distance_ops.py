from rapidfuzz import distance
from typing import Optional

# Levenshtein
def levenshtein_distance(s1: str, s2: str) -> int:
    return distance.Levenshtein.distance(s1, s2)
def levenshtein_normalized_distance(s1: str, s2: str) -> float:
    return distance.Levenshtein.normalized_distance(s1, s2)
def levenshtein_similarity(s1: str, s2: str) -> int:
    return distance.Levenshtein.similarity(s1, s2)
def levenshtein_normalized_similarity(s1: str, s2: str) -> float:
    return distance.Levenshtein.normalized_similarity(s1, s2)

# Hamming
def hamming_distance(s1: str, s2: str) -> int:
    return distance.Hamming.distance(s1, s2)
def hamming_normalized_distance(s1: str, s2: str) -> float:
    return distance.Hamming.normalized_distance(s1, s2)
def hamming_similarity(s1: str, s2: str) -> int:
    return distance.Hamming.similarity(s1, s2)
def hamming_normalized_similarity(s1: str, s2: str) -> float:
    return distance.Hamming.normalized_similarity(s1, s2)

# Jaro
def jaro_distance(s1: str, s2: str) -> float:
    return distance.Jaro.distance(s1, s2)
def jaro_similarity(s1: str, s2: str) -> float:
    return distance.Jaro.similarity(s1, s2)

# JaroWinkler
def jaro_winkler_distance(s1: str, s2: str) -> float:
    return distance.JaroWinkler.distance(s1, s2)
def jaro_winkler_similarity(s1: str, s2: str) -> float:
    return distance.JaroWinkler.similarity(s1, s2)

# DamerauLevenshtein
def damerau_levenshtein_distance(s1: str, s2: str) -> int:
    return distance.DamerauLevenshtein.distance(s1, s2)
def damerau_levenshtein_normalized_distance(s1: str, s2: str) -> float:
    return distance.DamerauLevenshtein.normalized_distance(s1, s2)

# Indel
def indel_distance(s1: str, s2: str) -> int:
    return distance.Indel.distance(s1, s2)
def indel_normalized_distance(s1: str, s2: str) -> float:
    return distance.Indel.normalized_distance(s1, s2)

# OSA
def osa_distance(s1: str, s2: str) -> int:
    return distance.OSA.distance(s1, s2)
def osa_normalized_distance(s1: str, s2: str) -> float:
    return distance.OSA.normalized_distance(s1, s2)

# LCS
def lcs_seq_distance(s1: str, s2: str) -> int:
    return distance.LCSseq.distance(s1, s2)
def lcs_seq_similarity(s1: str, s2: str) -> int:
    return distance.LCSseq.similarity(s1, s2)

# Prefix/Suffix
def prefix_distance(s1: str, s2: str) -> int:
    return distance.Prefix.distance(s1, s2)
def suffix_distance(s1: str, s2: str) -> int:
    return distance.Suffix.distance(s1, s2)
