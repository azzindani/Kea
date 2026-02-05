from mcp_servers.sklearn_server.tools.core_ops import parse_data, parse_vector, to_serializable, serialize_model, DataInput, VectorInput
from sklearn.semi_supervised import LabelPropagation, LabelSpreading, SelfTrainingClassifier
from sklearn.ensemble import RandomForestClassifier
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional

async def label_propagation(X: DataInput, y: VectorInput, kernel: str = 'rbf') -> Dict[str, Any]:
    """Label Propagation (Graph-based, -1 for unlabeled)."""
    X_df = parse_data(X)
    y_vec = parse_vector(y) # Ensure -1 is used for unlabeled
    
    model = LabelPropagation(kernel=kernel)
    model.fit(X_df, y_vec)
    
    return to_serializable({
        "transduction": model.transduction_.tolist(), # Assigned labels
        "model": serialize_model(model)
    })

async def label_spreading(X: DataInput, y: VectorInput, kernel: str = 'rbf', alpha: float = 0.2) -> Dict[str, Any]:
    """Label Spreading (Graph-based with clamping)."""
    X_df = parse_data(X)
    y_vec = parse_vector(y)
    
    model = LabelSpreading(kernel=kernel, alpha=alpha)
    model.fit(X_df, y_vec)
    
    return to_serializable({
        "transduction": model.transduction_.tolist(),
        "model": serialize_model(model)
    })

async def self_training(X: DataInput, y: VectorInput) -> Dict[str, Any]:
    """Self-training Classifier (Wrapper)."""
    X_df = parse_data(X)
    y_vec = parse_vector(y)
    
    base_model = RandomForestClassifier(random_state=42)
    model = SelfTrainingClassifier(base_model)
    model.fit(X_df, y_vec)
    
    return to_serializable({
        "transduction": model.transduction_.tolist(),
        "model": serialize_model(model)
    })
