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

def feature_encode_onehot(file_path: str, columns: List[str], output_path: str="encoded.csv") -> str:
    """ENCODES categorical vars (One-Hot). [ACTION]"""
    try:
        df = pd.read_csv(file_path)
        df = pd.get_dummies(df, columns=columns)
        return _save(df, output_path)
    except Exception as e:
        return f"Error: {e}"

def feature_encode_label(file_path: str, columns: List[str], output_path: str="encoded.csv") -> str:
    """ENCODES categorical vars (Label). [ACTION]"""
    try:
        from sklearn.preprocessing import LabelEncoder
        df = pd.read_csv(file_path)
        le = LabelEncoder()
        for col in columns:
            # Handle NaNs for LE
            mask = df[col].notnull()
            df.loc[mask, col] = le.fit_transform(df.loc[mask, col].astype(str))
        return _save(df, output_path)
    except Exception as e:
        return f"Error: {e}"

def feature_binning(file_path: str, column: str, bins: int = 5, labels: List[str] = None, output_path: str="binned.csv") -> str:
    """CREATES bins from continuous var. [ACTION]"""
    try:
        df = pd.read_csv(file_path)
        df[f"{column}_bin"] = pd.cut(df[column], bins=bins, labels=labels)
        return _save(df, output_path)
    except Exception as e:
        return f"Error: {e}"

def feature_interaction(file_path: str, col1: str, col2: str, operation: str = 'multiply', output_path: str="interactions.csv") -> str:
    """CREATES interaction features. [ACTION]"""
    try:
        df = pd.read_csv(file_path)
        if operation == 'multiply':
            df[f"{col1}_x_{col2}"] = df[col1] * df[col2]
        elif operation == 'divide':
            df[f"{col1}_div_{col2}"] = df[col1] / df[col2]
        elif operation == 'add':
            df[f"{col1}_plus_{col2}"] = df[col1] + df[col2]
        elif operation == 'subtract':
            df[f"{col1}_sub_{col2}"] = df[col1] - df[col2]
        return _save(df, output_path)
    except Exception as e:
        return f"Error: {e}"

def feature_polynomial(file_path: str, columns: List[str], degree: int = 2, output_path: str="poly.csv") -> str:
    """CREATES polynomial features. [ACTION]"""
    try:
        from sklearn.preprocessing import PolynomialFeatures
        df = pd.read_csv(file_path)
        poly = PolynomialFeatures(degree=degree, include_bias=False)
        poly_data = poly.fit_transform(df[columns])
        feature_names = poly.get_feature_names_out(columns)
        
        poly_df = pd.DataFrame(poly_data, columns=feature_names)
        df = pd.concat([df.drop(columns=columns), poly_df], axis=1)
        return _save(df, output_path)
    except Exception as e:
        return f"Error: {e}"

def feature_log_transform(file_path: str, columns: List[str], output_path: str="log.csv") -> str:
    """APPLIES Log transform (np.log1p). [ACTION]"""
    try:
        df = pd.read_csv(file_path)
        for col in columns:
            df[f"{col}_log"] = np.log1p(df[col])
        return _save(df, output_path)
    except Exception as e:
        return f"Error: {e}"

def feature_date_parts(file_path: str, date_column: str, output_path: str="dates.csv") -> str:
    """EXTRACTS date components. [ACTION]"""
    try:
        df = pd.read_csv(file_path)
        df[date_column] = pd.to_datetime(df[date_column])
        df[f"{date_column}_year"] = df[date_column].dt.year
        df[f"{date_column}_month"] = df[date_column].dt.month
        df[f"{date_column}_day"] = df[date_column].dt.day
        df[f"{date_column}_dow"] = df[date_column].dt.dayofweek
        return _save(df, output_path)
    except Exception as e:
        return f"Error: {e}"

def feature_text_length(file_path: str, text_column: str, output_path: str="textlen.csv") -> str:
    """CALCULATES text length features. [ACTION]"""
    try:
        df = pd.read_csv(file_path)
        df[f"{text_column}_len"] = df[text_column].astype(str).apply(len)
        df[f"{text_column}_word_count"] = df[text_column].astype(str).apply(lambda x: len(x.split()))
        return _save(df, output_path)
    except Exception as e:
        return f"Error: {e}"

def feature_target_encode(file_path: str, cat_column: str, target_column: str, output_path: str="target_enc.csv") -> str:
    """ENCODES target mean encoding. [ACTION]"""
    try:
        df = pd.read_csv(file_path)
        means = df.groupby(cat_column)[target_column].mean()
        df[f"{cat_column}_target_enc"] = df[cat_column].map(means)
        return _save(df, output_path)
    except Exception as e:
        return f"Error: {e}"

def feature_aggregate(file_path: str, group_by: List[str], agg_columns: Dict[str, str], output_path: str="agg.csv") -> str:
    """AGGREGATES data by group. [ACTION]"""
    try:
        df = pd.read_csv(file_path)
        # agg_columns format: {"column_name": "mean"}
        agg_res = df.groupby(group_by).agg(agg_columns).reset_index()
        return _save(agg_res, output_path)
    except Exception as e:
        return f"Error: {e}"
