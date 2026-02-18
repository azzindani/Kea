from sklearn.preprocessing import (
    StandardScaler, MinMaxScaler, RobustScaler, MaxAbsScaler, Normalizer, PowerTransformer, QuantileTransformer
)
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
import pandas as pd
import structlog
from typing import Dict, Any, List, Optional, Union

logger = structlog.get_logger()

# --- Scalers ---
def _scale_data(file_path, scaler, output_path):
    try:
        df = pd.read_csv(file_path)
        # Assuming all numeric columns except 'id' or non-numeric
        numeric_cols = df.select_dtypes(include=['number']).columns
        if len(numeric_cols) == 0:
            return "No numeric columns to scale."
        
        df[numeric_cols] = scaler.fit_transform(df[numeric_cols])
        
        if output_path:
            df.to_csv(output_path, index=False)
            return f"Scaled {len(numeric_cols)} columns to {output_path}"
        return "Scaled (no output path)"
    except Exception as e:
        return f"Error: {e}"

def scale_standard(file_path: str, output_path: str) -> str:
    """SCALES data (StandardScaler). [ACTION]"""
    return _scale_data(file_path, StandardScaler(), output_path)

def scale_minmax(file_path: str, output_path: str) -> str:
    """SCALES data (MinMaxScaler). [ACTION]"""
    return _scale_data(file_path, MinMaxScaler(), output_path)

def scale_robust(file_path: str, output_path: str) -> str:
    """SCALES data (RobustScaler). [ACTION]"""
    return _scale_data(file_path, RobustScaler(), output_path)

def scale_maxabs(file_path: str, output_path: str) -> str:
    """SCALES data (MaxAbsScaler). [ACTION]"""
    return _scale_data(file_path, MaxAbsScaler(), output_path)

def scale_normalize(file_path: str, output_path: str) -> str:
    """NORMALIZES data (l2 norm). [ACTION]"""
    return _scale_data(file_path, Normalizer(), output_path)

# --- Transformers ---
def transform_power_yeo_johnson(file_path: str, output_path: str) -> str:
    """TRANSFORMS data (PowerTransformer Yeo-Johnson). [ACTION]"""
    return _scale_data(file_path, PowerTransformer(method='yeo-johnson'), output_path)

def transform_quantile_uniform(file_path: str, output_path: str) -> str:
    """TRANSFORMS data (QuantileTransformer Uniform). [ACTION]"""
    return _scale_data(file_path, QuantileTransformer(output_distribution='uniform'), output_path)

def transform_quantile_normal(file_path: str, output_path: str) -> str:
    """TRANSFORMS data (QuantileTransformer Normal). [ACTION]"""
    return _scale_data(file_path, QuantileTransformer(output_distribution='normal'), output_path)

# --- Dimensionality Reduction ---
def reduce_pca(file_path: str, n_components: int, output_path: str) -> str:
    """REDUCES dimensions (PCA). [ACTION]"""
    try:
        df = pd.read_csv(file_path)
        numeric_df = df.select_dtypes(include=['number']).dropna()
        
        pca = PCA(n_components=n_components)
        components = pca.fit_transform(numeric_df)
        
        res_df = pd.DataFrame(components, columns=[f'PC{i+1}' for i in range(n_components)])
        res_df.to_csv(output_path, index=False)
        
        return f"PCA Reduced to {n_components} components. Explained Variance: {pca.explained_variance_ratio_}"
    except Exception as e:
        return f"Error: {e}"

def reduce_tsne(file_path: str, n_components: int, output_path: str, perplexity: float = 30.0) -> str:
    """REDUCES dimensions (t-SNE). [ACTION]"""
    try:
        df = pd.read_csv(file_path)
        numeric_df = df.select_dtypes(include=['number']).dropna()
        
        # Limit rows for t-SNE performance if needed
        if len(numeric_df) > 5000:
             numeric_df = numeric_df.sample(5000, random_state=42)
             
        tsne = TSNE(n_components=n_components, perplexity=perplexity, random_state=42)
        components = tsne.fit_transform(numeric_df)
        
        res_df = pd.DataFrame(components, columns=[f'TSNE{i+1}' for i in range(n_components)])
        res_df.to_csv(output_path, index=False)
        
        return f"t-SNE Reduced to {n_components} components."
    except Exception as e:
        return f"Error: {e}"
