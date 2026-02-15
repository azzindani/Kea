from typing import Dict, Any, List, Optional
import pandas as pd
import structlog
from sklearn.decomposition import PCA, IncrementalPCA, KernelPCA, FastICA, FactorAnalysis, TruncatedSVD, DictionaryLearning, MiniBatchDictionaryLearning, LatentDirichletAllocation

logger = structlog.get_logger()

def _decompose(model, data_url, n_components, drop_cols=None) -> Dict[str, Any]:
    try:
        df = pd.read_csv(data_url)
        if drop_cols:
             X = df.drop(columns=drop_cols)
        else:
             X = df.select_dtypes(include=['number'])
             
        transformed = model.fit_transform(X)
        return {
            "shape": transformed.shape,
            "components": model.components_.tolist() if hasattr(model, 'components_') else "N/A",
            "explained_variance_ratio": model.explained_variance_ratio_.tolist() if hasattr(model, 'explained_variance_ratio_') else "N/A"
        }
    except Exception as e:
        return {"error": str(e)}

def decompose_pca(data_url: str, n_components: int = 2, drop_cols: List[str] = None) -> Dict[str, Any]:
    """DECOMPOSES using PCA. [DATA]"""
    return _decompose(PCA(n_components=n_components), data_url, n_components, drop_cols)

def decompose_incremental_pca(data_url: str, n_components: int = 2, batch_size: int = None, drop_cols: List[str] = None) -> Dict[str, Any]:
    """DECOMPOSES using Incremental PCA. [DATA]"""
    return _decompose(IncrementalPCA(n_components=n_components, batch_size=batch_size), data_url, n_components, drop_cols)

def decompose_kernel_pca(data_url: str, n_components: int = 2, kernel: str = "linear", drop_cols: List[str] = None) -> Dict[str, Any]:
    """DECOMPOSES using Kernel PCA. [DATA]"""
    return _decompose(KernelPCA(n_components=n_components, kernel=kernel), data_url, n_components, drop_cols)

def decompose_fast_ica(data_url: str, n_components: int = 2, drop_cols: List[str] = None) -> Dict[str, Any]:
    """DECOMPOSES using FastICA. [DATA]"""
    return _decompose(FastICA(n_components=n_components), data_url, n_components, drop_cols)

def decompose_factor_analysis(data_url: str, n_components: int = 2, drop_cols: List[str] = None) -> Dict[str, Any]:
    """DECOMPOSES using Factor Analysis. [DATA]"""
    return _decompose(FactorAnalysis(n_components=n_components), data_url, n_components, drop_cols)

def decompose_truncated_svd(data_url: str, n_components: int = 2, drop_cols: List[str] = None) -> Dict[str, Any]:
    """DECOMPOSES using Truncated SVD (LSA). [DATA]"""
    return _decompose(TruncatedSVD(n_components=n_components), data_url, n_components, drop_cols)

def decompose_dictionary_learning(data_url: str, n_components: int = 2, drop_cols: List[str] = None) -> Dict[str, Any]:
    """DECOMPOSES using Dictionary Learning. [DATA]"""
    return _decompose(DictionaryLearning(n_components=n_components), data_url, n_components, drop_cols)

def decompose_minibatch_dictionary_learning(data_url: str, n_components: int = 2, drop_cols: List[str] = None) -> Dict[str, Any]:
    """DECOMPOSES using MiniBatch Dictionary Learning. [DATA]"""
    return _decompose(MiniBatchDictionaryLearning(n_components=n_components), data_url, n_components, drop_cols)

def decompose_lda(data_url: str, n_components: int = 2, drop_cols: List[str] = None) -> Dict[str, Any]:
    """DECOMPOSES using Latent Dirichlet Allocation. [DATA]"""
    return _decompose(LatentDirichletAllocation(n_components=n_components), data_url, n_components, drop_cols)
