import pandas as pd
import numpy as np
import structlog
from typing import Dict, List, Any, Optional

logger = structlog.get_logger()

def _save(df: pd.DataFrame, output_path: str) -> str:
    try:
        df.to_csv(output_path, index=False)
        return f"Saved to {output_path} (Shape: {df.shape})"
    except Exception as e:
        return f"Error saving: {e}"

def clean_missing(file_path: str, strategy: str = 'drop', fill_value: Any = None, columns: List[str] = None, output_path: str="clean.csv") -> str:
    """CLEANS missing values. [ACTION]"""
    try:
        df = pd.read_csv(file_path)
        cols_to_use = columns if columns else df.columns
        
        if strategy == 'drop':
            df = df.dropna(subset=cols_to_use)
        elif strategy == 'mean':
            df[cols_to_use] = df[cols_to_use].fillna(df[cols_to_use].mean())
        elif strategy == 'median':
            df[cols_to_use] = df[cols_to_use].fillna(df[cols_to_use].median())
        elif strategy == 'mode':
            df[cols_to_use] = df[cols_to_use].fillna(df[cols_to_use].mode().iloc[0])
        elif strategy == 'constant':
            df[cols_to_use] = df[cols_to_use].fillna(fill_value)
        elif strategy == 'ffill':
            df[cols_to_use] = df[cols_to_use].ffill()
        elif strategy == 'bfill':
            df[cols_to_use] = df[cols_to_use].bfill()
            
        return _save(df, output_path)
    except Exception as e:
        return f"Error: {e}"

def clean_duplicates(file_path: str, subset: List[str] = None, keep: str = 'first', output_path: str="dedup.csv") -> str:
    """REMOVES duplicate rows. [ACTION]"""
    try:
        df = pd.read_csv(file_path)
        df = df.drop_duplicates(subset=subset, keep=keep)
        return _save(df, output_path)
    except Exception as e:
        return f"Error: {e}"

def clean_outliers_zscore(file_path: str, columns: List[str], threshold: float = 3.0, output_path: str="no_outliers.csv") -> str:
    """REMOVES outliers via Z-Score. [ACTION]"""
    try:
        df = pd.read_csv(file_path)
        for col in columns:
            if pd.api.types.is_numeric_dtype(df[col]):
                z_scores = np.abs((df[col] - df[col].mean()) / df[col].std())
                df = df[z_scores < threshold]
        return _save(df, output_path)
    except Exception as e:
        return f"Error: {e}"

def clean_outliers_iqr(file_path: str, columns: List[str], multiplier: float = 1.5, output_path: str="no_outliers.csv") -> str:
    """REMOVES outliers via IQR. [ACTION]"""
    try:
        df = pd.read_csv(file_path)
        for col in columns:
            if pd.api.types.is_numeric_dtype(df[col]):
                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1
                df = df[~((df[col] < (Q1 - multiplier * IQR)) | (df[col] > (Q3 + multiplier * IQR)))]
        return _save(df, output_path)
    except Exception as e:
        return f"Error: {e}"

def clean_convert_types(file_path: str, type_map: Dict[str, str], output_path: str="typed.csv") -> str:
    """CONVERTS column data types. [ACTION]"""
    try:
        df = pd.read_csv(file_path)
        df = df.astype(type_map)
        return _save(df, output_path)
    except Exception as e:
        return f"Error: {e}" # Handles invalid conversions usually

def clean_rename(file_path: str, rename_map: Dict[str, str], output_path: str="renamed.csv") -> str:
    """RENAMES columns. [ACTION]"""
    try:
        df = pd.read_csv(file_path)
        df = df.rename(columns=rename_map)
        return _save(df, output_path)
    except Exception as e:
        return f"Error: {e}"

def clean_drop_columns(file_path: str, columns: List[str], output_path: str="dropped.csv") -> str:
    """DROPS specified columns. [ACTION]"""
    try:
        df = pd.read_csv(file_path)
        df = df.drop(columns=columns)
        return _save(df, output_path)
    except Exception as e:
        return f"Error: {e}"

def clean_replace(file_path: str, to_replace: Any, value: Any, columns: List[str] = None, output_path: str="replaced.csv") -> str:
    """REPLACES values in dataframe. [ACTION]"""
    try:
        df = pd.read_csv(file_path)
        if columns:
             df[columns] = df[columns].replace(to_replace, value)
        else:
             df = df.replace(to_replace, value)
        return _save(df, output_path)
    except Exception as e:
        return f"Error: {e}"

def clean_strip_whitespace(file_path: str, columns: List[str] = None, output_path: str="stripped.csv") -> str:
    """STRIPS whitespace from strings. [ACTION]"""
    try:
        df = pd.read_csv(file_path)
        cols_to_use = columns if columns else df.select_dtypes(include=['object']).columns
        
        for col in cols_to_use:
            if df[col].dtype == object:
                df[col] = df[col].str.strip()
        return _save(df, output_path)
    except Exception as e:
        return f"Error: {e}"
