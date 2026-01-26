import pandas as pd
from typing import Optional, List, Union, Any, Dict
from mcp_servers.pandas_server.utils import load_dataframe, save_dataframe
import re

def tokenize_text(file_path: str, column: str, output_path: str, lowercase: bool = True) -> str:
    """Simple whitespace/punctuation tokenization."""
    df = load_dataframe(file_path)
    
    def simple_tokenize(text):
        if not isinstance(text, str): return []
        if lowercase: text = text.lower()
        # Find words (alphanumeric)
        return re.findall(r'\b\w+\b', text)
        
    df[f"{column}_tokens"] = df[column].apply(simple_tokenize)
    save_dataframe(df, output_path)
    return f"Tokenized {column}. Saved to {output_path}"

def count_words(file_path: str, column: str, output_path: str) -> str:
    """Count words and characters."""
    df = load_dataframe(file_path)
    
    s = df[column].astype(str)
    df[f"{column}_word_count"] = s.apply(lambda x: len(re.findall(r'\w+', x)))
    df[f"{column}_char_count"] = s.str.len()
    
    save_dataframe(df, output_path)
    return f"Calculated word/char counts for {column}. Saved to {output_path}"

def generate_ngrams(file_path: str, column: str, n: int, output_path: str) -> str:
    """Generate n-grams (e.g. bigrams, trigrams)."""
    df = load_dataframe(file_path)
    
    def get_ngrams(text):
        if not isinstance(text, str): return []
        tokens = re.findall(r'\b\w+\b', text.lower())
        if len(tokens) < n: return []
        return [" ".join(tokens[i:i+n]) for i in range(len(tokens)-n+1)]
        
    df[f"{column}_{n}grams"] = df[column].apply(get_ngrams)
    save_dataframe(df, output_path)
    return f"Generated {n}-grams for {column}. Saved to {output_path}"
